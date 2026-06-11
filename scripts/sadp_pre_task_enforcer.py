#!/usr/bin/env python3
"""SADP Pre-Task Enforcer — validates SADP compliance before agent edits begin.

Enforcement points:
  1. pre_task  — Before a task starts: TaskSpec exists, Gate 0 valid, no conflicts
  2. pre_edit  — Before any file is written: file is in active TaskSpec write_set
  3. post_task — After task completion: ExecutionReport exists, gates evaluated

Usage:
  python scripts/sadp_pre_task_enforcer.py pre_task --task-id SHARED-CDP-V2-FIX-A1
  python scripts/sadp_pre_task_enforcer.py pre_edit --file scripts/foo.py
  python scripts/sadp_pre_task_enforcer.py post_task --task-id SHARED-CDP-V2-FIX-A1

Exit codes:
  0 = PASS (enforcement satisfied)
  1 = BLOCKED (SADP violation — agent must not proceed)
  2 = WARNING (non-blocking advisory)
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parent.parent
TASKS_DIR = REPO / "tasks"
RULES_DIR = REPO / "rules"
DOCS_DIR = REPO / "docs" / "agent-runtime"
AGENT_DIR = REPO / ".agent"
SADP_DIR = REPO / ".sadp"

# Protected governance files that require exclusive lock (SADP §0.2 rule 2)
# Loaded from .sadp/SADP_POLICY.json if available, otherwise use defaults
PROTECTED_FILES = {
    "AGENTS.md",
    "CLAUDE.md",
    "docs/agent-runtime/capability-inventory.md",
    "docs/agent-runtime/sub-agent-dispatch-protocol.md",
    "rules/core.md",
    "docs/agent-runtime/lessons-learned.md",
    ".sadp/SADP_POLICY.json",
    ".sadp/TRIGGER_RULES.json",
    "scripts/sadp-audit.ps1",
}

# Enforcer scripts that protect themselves (require human + reviewer to modify)
SELF_PROTECTING_FILES = {
    "scripts/sadp_pre_task_enforcer.py",
    "scripts/sadp-audit.ps1",
    "scripts/qoderwork_task_runner.py",
}

# Governance-adjacent files that trigger advisory (not blocking)
GOVERNANCE_ADJACENT = {
    ".agent/PROJECT_REGISTRY.json",
    ".agent/MULTI_PROJECT_RESOURCE_POLICY.json",
    ".agent/CONVERSATION_BINDING.json",
}


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def load_sadp_policy() -> dict:
    """Load unified SADP policy from .sadp/SADP_POLICY.json.

    Returns policy dict or empty dict if not available.
    """
    policy_path = SADP_DIR / "SADP_POLICY.json"
    if policy_path.exists():
        try:
            return json.loads(policy_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


def parse_taskspec_priority(path: Path) -> str:
    """Extract priority level from a TaskSpec (P0, P1, P2, P3)."""
    content = path.read_text(encoding="utf-8")
    match = re.search(r"\*\*Priority\*\*:\s*(P\d)", content)
    if match:
        return match.group(1)
    return "P3"  # Default to lowest priority


# ── TaskSpec Parsing ──────────────────────────────────────────────────


def find_taskspec(task_id: str) -> Path | None:
    """Find a TaskSpec file by task ID in the tasks/ directory."""
    if not TASKS_DIR.exists():
        return None
    for f in TASKS_DIR.glob("*.md"):
        content = f.read_text(encoding="utf-8")
        # Match **ID**: <task_id> pattern
        if re.search(rf"\*\*ID\*\*:\s*{re.escape(task_id)}", content):
            return f
        # Also match task_id: in YAML blocks
        if re.search(rf"task_id:\s*{re.escape(task_id)}", content):
            return f
    return None


def parse_taskspec_gate0(path: Path) -> dict:
    """Extract gate_0 block from a TaskSpec markdown file."""
    content = path.read_text(encoding="utf-8")

    # Find the gate_0 YAML block
    gate0_match = re.search(
        r"gate_0:\s*\n((?:\s{2,}.+\n)*)", content
    )
    if not gate0_match:
        return {}

    gate0_text = gate0_match.group(1)

    result: dict[str, Any] = {}

    # Check for inventory_evidence
    result["has_inventory_evidence"] = "inventory_evidence:" in gate0_text
    result["has_queried_sources"] = "queried_sources:" in gate0_text
    result["has_matched_capabilities"] = "matched_capabilities:" in gate0_text
    result["has_sufficiency_decision"] = "sufficiency_decision:" in gate0_text
    result["has_decision"] = "decision:" in gate0_text

    # Check for rules_checked
    result["has_rules_checked"] = "rules_checked:" in gate0_text
    result["has_lessons_checked"] = "lessons_checked:" in gate0_text

    # Check for delta_justification (required if new_delta_required)
    result["has_delta_justification"] = "delta_justification:" in gate0_text
    result["sufficiency_decision_value"] = ""
    decision_match = re.search(r"sufficiency_decision:\s*(\S+)", gate0_text)
    if decision_match:
        result["sufficiency_decision_value"] = decision_match.group(1)

    return result


def parse_taskspec_conflict_registry(path: Path) -> dict:
    """Extract conflict_registry from a TaskSpec markdown file."""
    content = path.read_text(encoding="utf-8")

    cr_match = re.search(
        r"conflict_registry:\s*\n((?:\s{2,}.+\n)*)", content
    )
    if not cr_match:
        return {}

    cr_text = cr_match.group(1)

    result: dict[str, Any] = {}
    result["has_read_set"] = "read_set:" in cr_text
    result["has_write_set"] = "write_set:" in cr_text
    result["has_conflict_level"] = "conflict_level:" in cr_text
    result["has_protected_files_touched"] = "protected_files_touched:" in cr_text

    # Extract write_set entries
    write_set: list[str] = []
    ws_match = re.search(r"write_set:\s*\n((?:\s+-\s+.+\n)*)", cr_text)
    if ws_match:
        for line in ws_match.group(1).splitlines():
            m = re.match(r"\s+-\s+(.+)", line)
            if m:
                write_set.append(m.group(1).strip())
    result["write_set"] = write_set

    return result


def parse_taskspec_acceptance_gates(path: Path) -> list[str]:
    """Extract acceptance gates from a TaskSpec."""
    content = path.read_text(encoding="utf-8")
    gates: list[str] = []

    gates_match = re.search(
        r"\*\*Acceptance Gates\*\*:\s*\n((?:\s+\d+\..+\n)*)", content
    )
    if gates_match:
        for line in gates_match.group(1).splitlines():
            m = re.match(r"\s+\d+\.\s+(.+)", line)
            if m:
                gates.append(m.group(1).strip())

    return gates


# ── ExecutionReport Detection ─────────────────────────────────────────


def find_execution_report(task_id: str) -> Path | None:
    """Find an ExecutionReport for the given task ID."""
    # Check _evidence/ directory
    evidence_dir = REPO / "_evidence" / task_id
    if evidence_dir.exists():
        er_path = evidence_dir / "EXECUTION_REPORT.md"
        if er_path.exists():
            return er_path

    # Check tasks/ directory
    if TASKS_DIR.exists():
        for f in TASKS_DIR.glob(f"*{task_id}*"):
            if "execution" in f.name.lower() or "report" in f.name.lower():
                return f

    # Check reports/ directory
    reports_dir = REPO / "reports"
    if reports_dir.exists():
        for f in reports_dir.glob(f"*{task_id}*"):
            return f

    return None


# ── Enforcement Checks ────────────────────────────────────────────────


def check_pre_task(task_id: str) -> tuple[int, list[str]]:
    """Pre-task enforcement: validate SADP compliance before task starts.

    Returns (exit_code, messages).
    exit_code: 0=PASS, 1=BLOCKED, 2=WARNING
    """
    messages: list[str] = []
    blocked = False

    # 1. TaskSpec must exist
    taskspec_path = find_taskspec(task_id)
    if not taskspec_path:
        messages.append(f"BLOCKED: No TaskSpec found for task_id={task_id}")
        messages.append(f"  Searched: {TASKS_DIR}")
        messages.append("  Required: TaskSpec with Gate 0 Ledger + Conflict Registry")
        return 1, messages
    messages.append(f"PASS: TaskSpec found at {taskspec_path.name}")

    # 2. Gate 0 Ledger must have inventory_evidence (SADP §0.1)
    gate0 = parse_taskspec_gate0(taskspec_path)
    if not gate0:
        messages.append("BLOCKED: No gate_0 block found in TaskSpec")
        blocked = True
    else:
        if not gate0.get("has_inventory_evidence"):
            messages.append("BLOCKED: gate_0 missing inventory_evidence (SADP §0.1)")
            blocked = True
        elif not gate0.get("has_queried_sources"):
            messages.append("BLOCKED: inventory_evidence missing queried_sources")
            blocked = True
        elif not gate0.get("has_matched_capabilities"):
            messages.append("BLOCKED: inventory_evidence missing matched_capabilities")
            blocked = True
        else:
            messages.append("PASS: Gate 0 Ledger has valid inventory_evidence")

        if not gate0.get("has_sufficiency_decision"):
            messages.append("BLOCKED: gate_0 missing sufficiency_decision")
            blocked = True

        # Check delta_justification requirement
        if gate0.get("sufficiency_decision_value") == "new_delta_required":
            if not gate0.get("has_delta_justification"):
                messages.append("BLOCKED: new_delta_required but no delta_justification")
                blocked = True

    # 3. Conflict Registry must exist (SADP §0.2)
    cr = parse_taskspec_conflict_registry(taskspec_path)
    if not cr:
        messages.append("BLOCKED: No conflict_registry found in TaskSpec (SADP §0.2)")
        blocked = True
    else:
        if not cr.get("has_read_set"):
            messages.append("BLOCKED: conflict_registry missing read_set")
            blocked = True
        if not cr.get("has_write_set"):
            messages.append("BLOCKED: conflict_registry missing write_set")
            blocked = True
        if not cr.get("has_conflict_level"):
            messages.append("BLOCKED: conflict_registry missing conflict_level")
            blocked = True
        if cr.get("has_read_set") and cr.get("has_write_set") and cr.get("has_conflict_level"):
            messages.append("PASS: Conflict Registry valid (read_set + write_set + conflict_level)")

    # 4. Acceptance gates must be defined
    gates = parse_taskspec_acceptance_gates(taskspec_path)
    if not gates:
        messages.append("WARNING: No acceptance gates defined in TaskSpec")
    else:
        messages.append(f"PASS: {len(gates)} acceptance gates defined")

    # 5. Check protected file access
    write_set = cr.get("write_set", [])
    protected_touched = [f for f in write_set if f in PROTECTED_FILES]
    if protected_touched:
        messages.append(f"BLOCKED: Protected governance files in write_set: {protected_touched}")
        messages.append("  These require exclusive lock per SADP §0.2 rule 2")
        blocked = True

    # 6. Advisory for governance-adjacent files
    adjacent_touched = [f for f in write_set if f in GOVERNANCE_ADJACENT]
    if adjacent_touched:
        messages.append(f"ADVISORY: Governance-adjacent files in write_set: {adjacent_touched}")
        messages.append("  Note in Conflict Registry as governance_adjacent_files_modified")

    if blocked:
        return 1, messages
    return 0, messages


def check_pre_edit(file_path: str, task_id: str | None = None) -> tuple[int, list[str]]:
    """Pre-edit enforcement: verify file is in an active TaskSpec write_set.

    Scope creep blocking is priority-dependent:
      P0/P1: BLOCKED (exit 1) — scope creep is a hard stop
      P2/P3: WARNING (exit 2) — advisory, may continue

    Self-protecting files (enforcer scripts) require HUMAN_REQUIRED.

    Returns (exit_code, messages).
    """
    messages: list[str] = []

    # Normalize path
    rel_path = file_path
    if Path(file_path).is_absolute():
        try:
            rel_path = str(Path(file_path).relative_to(REPO))
        except ValueError:
            rel_path = file_path

    # Check if file is protected governance file
    if rel_path in PROTECTED_FILES:
        messages.append(f"BLOCKED: {rel_path} is a protected governance file")
        messages.append("  Requires exclusive lock per SADP §0.2 rule 2")
        return 1, messages

    # Check if file is self-protecting (enforcer scripts)
    if rel_path in SELF_PROTECTING_FILES:
        messages.append(f"HUMAN_REQUIRED: {rel_path} is a self-protecting enforcer file")
        messages.append("  Cannot be modified by automated tasks — requires human approval + independent reviewer")
        return 1, messages

    # If no task_id specified, just check protected status
    if not task_id:
        messages.append(f"PASS: {rel_path} is not a protected governance file")
        messages.append("ADVISORY: No task_id specified — cannot verify write_set membership")
        return 2, messages

    # Check if file is in TaskSpec write_set
    taskspec_path = find_taskspec(task_id)
    if not taskspec_path:
        messages.append(f"WARNING: No TaskSpec found for task_id={task_id}")
        messages.append(f"  Cannot verify if {rel_path} is in write_set")
        return 2, messages

    cr = parse_taskspec_conflict_registry(taskspec_path)
    write_set = cr.get("write_set", [])

    # Check if file matches any write_set entry
    in_write_set = False
    for ws_entry in write_set:
        if rel_path == ws_entry or rel_path.replace("\\", "/") == ws_entry.replace("\\", "/"):
            in_write_set = True
            break
        # Glob-style matching
        if "*" in ws_entry:
            import fnmatch
            if fnmatch.fnmatch(rel_path, ws_entry):
                in_write_set = True
                break

    if in_write_set:
        messages.append(f"PASS: {rel_path} is in TaskSpec write_set")
        return 0, messages
    else:
        # Priority-based scope creep blocking
        priority = parse_taskspec_priority(taskspec_path)
        policy = load_sadp_policy()
        scope_policy = policy.get("pre_edit_policy", {}).get("scope_creep_by_priority", {})
        action = scope_policy.get(priority, "WARNING")

        if action == "BLOCKED":
            messages.append(f"BLOCKED: {rel_path} not in write_set — scope creep BLOCKED for {priority} task")
            messages.append(f"  TaskSpec: {taskspec_path.name} (priority: {priority})")
            messages.append("  To add this file: update TaskSpec write_set + Conflict Registry first")
            return 1, messages
        else:
            messages.append(f"WARNING: {rel_path} not found in TaskSpec write_set for {task_id}")
            if write_set:
                messages.append(f"  write_set: {write_set}")
            messages.append(f"  Priority: {priority} — scope creep is advisory (WARNING)")
            messages.append("  This may indicate scope creep — verify with TaskSpec owner")
            return 2, messages


def check_post_task(task_id: str) -> tuple[int, list[str]]:
    """Post-task enforcement: verify ExecutionReport and gate evaluation.

    Returns (exit_code, messages).
    """
    messages: list[str] = []
    blocked = False

    # 1. TaskSpec must still exist
    taskspec_path = find_taskspec(task_id)
    if not taskspec_path:
        messages.append(f"BLOCKED: TaskSpec missing for task_id={task_id}")
        return 1, messages
    messages.append(f"PASS: TaskSpec exists ({taskspec_path.name})")

    # 2. ExecutionReport must exist
    er_path = find_execution_report(task_id)
    if not er_path:
        messages.append(f"BLOCKED: No ExecutionReport found for task_id={task_id}")
        messages.append(f"  Searched: _evidence/{task_id}/, tasks/, reports/")
        blocked = True
    else:
        messages.append(f"PASS: ExecutionReport found at {er_path}")

        # Check for gate results in ExecutionReport
        er_content = er_path.read_text(encoding="utf-8")
        if "Gate 0" in er_content or "Gate 1" in er_content:
            messages.append("PASS: ExecutionReport contains gate results")
        else:
            messages.append("WARNING: ExecutionReport may be missing gate results")

    # 3. Check for Reviewer Index
    reviewer_index = REPO / "_evidence" / task_id / "REVIEWER_INDEX.md"
    if reviewer_index.exists():
        messages.append("PASS: Reviewer Index exists")
    else:
        messages.append("ADVISORY: No Reviewer Index — recommended for SADP compliance")

    # 4. Check for Conflict Registry
    conflict_registry = REPO / "_evidence" / task_id / "CONFLICT_REGISTRY.json"
    if conflict_registry.exists():
        messages.append("PASS: Conflict Registry exists")
    else:
        # Check if it's in the TaskSpec
        cr = parse_taskspec_conflict_registry(taskspec_path)
        if cr:
            messages.append("PASS: Conflict Registry embedded in TaskSpec")
        else:
            messages.append("WARNING: No Conflict Registry found")

    if blocked:
        return 1, messages
    return 0, messages


# ── CLI ────────────────────────────────────────────────────────────────


def main() -> None:
    parser = argparse.ArgumentParser(
        description="SADP Pre-Task Enforcer — validates SADP compliance at task boundaries"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # pre_task
    pt_parser = subparsers.add_parser("pre_task", help="Validate before task starts")
    pt_parser.add_argument("--task-id", required=True, help="TaskSpec ID to validate")

    # pre_edit
    pe_parser = subparsers.add_parser("pre_edit", help="Validate before file edit")
    pe_parser.add_argument("--file", required=True, help="File path to validate")
    pe_parser.add_argument("--task-id", help="Optional TaskSpec ID for write_set check")

    # post_task
    po_parser = subparsers.add_parser("post_task", help="Validate after task completes")
    po_parser.add_argument("--task-id", required=True, help="TaskSpec ID to validate")

    args = parser.parse_args()

    if args.command == "pre_task":
        exit_code, messages = check_pre_task(args.task_id)
    elif args.command == "pre_edit":
        exit_code, messages = check_pre_edit(args.file, getattr(args, "task_id", None))
    elif args.command == "post_task":
        exit_code, messages = check_post_task(args.task_id)
    else:
        parser.print_help()
        sys.exit(2)

    for msg in messages:
        print(msg)

    print(f"\n--- SADP Enforcer: {['PASS', 'BLOCKED', 'WARNING'][exit_code]} ---")
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
