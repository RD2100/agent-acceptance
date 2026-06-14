#!/usr/bin/env python3
"""Build a human-gated multi-agent dispatch plan.

This script does not dispatch agents and does not execute external runtimes.
It turns the current Gate 0 state into a machine-checkable first-wave worker
assignment packet with explicit write boundaries.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

REPO = Path(__file__).resolve().parent.parent
TASK_SPEC_SCHEMA = REPO / "schemas" / "agent-runtime" / "task-spec.schema.json"

PROTECTED_PATHS = {
    "AGENTS.md",
    "CLAUDE.md",
    "docs/agent-runtime/capability-inventory.md",
    "docs/agent-runtime/sub-agent-dispatch-protocol.md",
    "docs/agent-runtime/rules/core.md",
    "docs/agent-runtime/lessons-learned.md",
    "rules/core.md",
}


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _norm(path: str) -> str:
    return path.replace("\\", "/").strip().rstrip("/")


def _paths_conflict(left: str, right: str) -> bool:
    left_norm = _norm(left)
    right_norm = _norm(right)
    return (
        left_norm == right_norm
        or left_norm.startswith(right_norm + "/")
        or right_norm.startswith(left_norm + "/")
    )


def _load_json(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except FileNotFoundError:
        return None, f"file not found: {path}"
    except json.JSONDecodeError as exc:
        return None, f"invalid JSON: {exc}"
    except OSError as exc:
        return None, f"cannot read file: {path}: {exc}"
    if not isinstance(data, dict):
        return None, f"JSON root must be an object: {path}"
    return data, None


def _load_task_spec_validator() -> Draft202012Validator:
    schema, error = _load_json(TASK_SPEC_SCHEMA)
    if error or schema is None:
        raise ValueError(error or "TaskSpec schema load failed")
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


def _gate0() -> dict[str, Any]:
    return {
        "triggered": True,
        "trigger_reason": "Multi-agent dispatch plan introduces executable worker boundaries.",
        "inventory_evidence": {
            "queried_sources": [
                "docs/agent-runtime/sub-agent-dispatch-protocol.md",
                "docs/agent-runtime/capability-inventory.md",
                "docs/MULTI_AGENT_MULTI_GPT_PILOT_PLAN.md",
                "schemas/agent-runtime/task-spec.schema.json",
            ],
            "matched_capabilities": [
                "CAP-029 dev-frame-opencode Dispatch",
                "SADP TaskSpec conflict_registry",
                "multi-agent-gate0-preflight",
            ],
            "compared_against_request": [
                "parallel worker dispatch",
                "exclusive write boundaries",
                "human-gated external runtime execution",
            ],
        },
        "rules_checked": ["core-001", "core-005", "core-007", "review-001"],
        "lessons_checked": ["LL-structured-task-spec", "LL-independent-review-evidence"],
        "sufficiency_decision": "existing_partial",
        "decision": "build_delta",
        "delta_justification": "Existing TaskSpec covers per-task boundaries, but the pilot needs a batch-level assignment packet and conflict check before human-gated dispatch.",
    }


def _task_spec(
    task_id: str,
    title: str,
    description: str,
    write_set: list[str],
    read_set: list[str],
    *,
    priority: str = "P2",
    status: str = "ready",
    depends_on: list[str] | None = None,
    risk_notes: str = "No external runtime execution is authorized by this TaskSpec.",
) -> dict[str, Any]:
    touched = {
        _norm(path)
        for path in read_set + write_set
        if _norm(path) in PROTECTED_PATHS
    }
    return {
        "task_id": task_id,
        "title": title,
        "priority": priority,
        "status": status,
        "description": description,
        "depends_on": depends_on or [],
        "assumptions": [
            "Current Gate 0 preflight may remain HUMAN_REQUIRED.",
            "Worker must not execute opencode, live CDP, cross-repo smoke, or paper workflow without separate human authorization.",
        ],
        "risk_notes": risk_notes,
        "estimated_tools": ["rg", "python", "pytest"],
        "gate_0": _gate0(),
        "conflict_registry": {
            "read_set": read_set,
            "write_set": write_set,
            "protected_files_touched": bool(touched),
            "conflict_level": "high" if touched else "none",
        },
        "security_report": {
            "scan_status": "not_run",
            "new_external_api": False,
            "env_example_placeholders_only": None,
            "real_key_patterns_found": None,
            "staged_diff_secret_scan_run": False,
            "key_rotation_needed": None,
        },
    }


def _assignment(
    *,
    worker_role: str,
    task_spec: dict[str, Any],
    project_module: str,
    target: str,
    why_big_module: str,
    allowed_modify_range: list[str],
    forbidden_modify_range: list[str],
    main_flow_to_connect: str,
    tests_or_probes_required: list[str],
    governance_record_requirements: list[str],
    parallel_group_id: str,
    parallel_safe: bool,
    blocking_conditions: list[str],
) -> dict[str, Any]:
    return {
        "worker_role": worker_role,
        "parallel_group_id": parallel_group_id,
        "parallel_safe": parallel_safe,
        "project_module": project_module,
        "target": target,
        "why_big_module": why_big_module,
        "allowed_modify_range": allowed_modify_range,
        "forbidden_modify_range": forbidden_modify_range,
        "depends_on_interface_contracts": [
            "schemas/agent-runtime/task-spec.schema.json",
            "schemas/agent-runtime/multi-agent-gate0-preflight.schema.json",
        ],
        "provides_interface_contracts": [
            "Worker final report format from active objective",
            "TaskSpec conflict_registry write_set/read_set",
        ],
        "main_flow_to_connect": main_flow_to_connect,
        "real_functionality_required": "Produce real local evidence, not mock completion or verbal readiness.",
        "tests_or_probes_required": tests_or_probes_required,
        "required_verification_commands": tests_or_probes_required,
        "quality_standard": "P0/P1 zero; P2 documented with evidence; no external runtime execution.",
        "completion_standard": "Report includes verdict, changed files, tests run, artifacts, known gaps, and suggested review focus.",
        "blocking_conditions": blocking_conditions,
        "governance_record_requirements": governance_record_requirements,
        "task_spec": task_spec,
    }


def _default_assignments(*, activation_complete: bool = False) -> list[dict[str, Any]]:
    architecture_task = _task_spec(
        "ma-architecture-review-a1",
        "Review multi-agent architecture boundaries",
        "Check module boundaries, interface contracts, and forbidden cross-runtime execution paths before dispatch.",
        ["_reports/multi-agent-architecture-review-a1/ARCHITECTURE_REVIEW.md"],
        [
            "docs/MULTI_AGENT_MULTI_GPT_PILOT_PLAN.md",
            "docs/governance/HANDOFF.md",
            "docs/governance/RISK_REGISTER.md",
        ],
    )
    verifier_task = _task_spec(
        "ma-verifier-a1",
        "Run local multi-agent governance verification",
        "Independently run local-only tests and CLI probes for Gate 0, registry, and execution guards.",
        ["_reports/multi-agent-verifier-a1/VERIFY_REPORT.md"],
        [
            "scripts/multi_agent_gate0_preflight.py",
            "tests/test_multi_agent_gate0_preflight.py",
            "tests/test_conversation_registry.py",
            "tests/test_cross_repo_execution_guards.py",
            "tests/test_smoke_suite.py",
        ],
    )
    quality_task = _task_spec(
        "ma-quality-review-a1",
        "Review multi-agent readiness changes",
        "Audit safety, regression, error handling, tests, and evidence quality for the local readiness layer.",
        ["_reports/multi-agent-quality-review-a1/QUALITY_REVIEW.md"],
        [
            "scripts/multi_agent_gate0_preflight.py",
            "scripts/cross_repo_authorization.py",
            "scripts/cross_repo_verify.py",
            "scripts/multi_repo_smoke.py",
            "tests/test_multi_agent_gate0_preflight.py",
            "tests/test_cross_repo_execution_guards.py",
        ],
    )
    integrator_task = _task_spec(
        "ma-integrator-a1",
        "Integrate first-wave reports into governance docs",
        "Serially reconcile reviewer/verifier outputs and update governance state after first-wave local reports exist.",
        [
            "docs/governance/PROGRESS_LOG.md",
            "docs/governance/VERIFY_MATRIX.md",
            "docs/governance/HANDOFF.md",
        ],
        [
            "_reports/multi-agent-architecture-review-a1/ARCHITECTURE_REVIEW.md",
            "_reports/multi-agent-verifier-a1/VERIFY_REPORT.md",
            "_reports/multi-agent-quality-review-a1/QUALITY_REVIEW.md",
            "docs/governance/PROGRESS_LOG.md",
            "docs/governance/VERIFY_MATRIX.md",
            "docs/governance/HANDOFF.md",
        ],
        status="deferred",
        depends_on=["ma-architecture-review-a1", "ma-verifier-a1", "ma-quality-review-a1"],
        risk_notes="Integrator writes shared governance docs and must run serially after report tasks finish.",
    )
    binding_task = _task_spec(
        "ma-manual-binding-a1",
        "Record independent conversation binding evidence",
        "Human-gated activation task for replacing pending manual bindings with verified independent conversation evidence.",
        [".agent/CONVERSATION_BINDING.json"],
        [".agent/CONVERSATION_BINDING.json"],
        priority="P1",
        status="completed" if activation_complete else "deferred",
        risk_notes="Requires human-provided independent binding evidence; do not fabricate chat_url or conversation_id; avoid last-message-only capture.",
    )
    cap_task = _task_spec(
        "ma-cap029-approval-a1",
        "Review CAP-029 execution approval",
        "Human/reviewer-gated task for deciding whether dev-frame-opencode dispatch may become execution-usable.",
        ["docs/agent-runtime/capability-inventory.md"],
        [
            "docs/agent-runtime/capability-inventory.md",
            "docs/agent-runtime/tool-policy.md",
            "docs/agent-runtime/sub-agent-dispatch-protocol.md",
        ],
        priority="P1",
        status="completed" if activation_complete else "deferred",
        risk_notes="Requires human/reviewer approval before usable_for_execution can change. Must not execute opencode run or cross-repo smoke without separate human authorization; tool-policy weakening requires review.",
    )

    return [
        _assignment(
            worker_role="Architecture-Reviewer",
            task_spec=architecture_task,
            project_module="multi-agent pilot architecture",
            target="Confirm dispatch boundaries and runtime scope before any execution.",
            why_big_module="Architecture gating prevents parallel work from crossing runtime, paper, or governance boundaries.",
            allowed_modify_range=["_reports/multi-agent-architecture-review-a1/"],
            forbidden_modify_range=["scripts/", ".agent/", "docs/agent-runtime/", "scripts/paper_*.py"],
            main_flow_to_connect="Gate 0 preflight -> dispatch plan -> reviewer-safe task pool.",
            tests_or_probes_required=["read-only report plus cited file/line evidence"],
            governance_record_requirements=["Report path must be referenced by Integrator before governance docs change."],
            parallel_group_id="local-readiness",
            parallel_safe=True,
            blocking_conditions=["Finds P0/P1 architecture issue", "Needs external runtime execution"],
        ),
        _assignment(
            worker_role="Verifier",
            task_spec=verifier_task,
            project_module="multi-agent local verification",
            target="Run the narrow local checks that prove current readiness state.",
            why_big_module="Verification is the evidence source for deciding whether HUMAN_REQUIRED is the only remaining gate.",
            allowed_modify_range=["_reports/multi-agent-verifier-a1/"],
            forbidden_modify_range=["scripts/", "tests/", ".agent/", "docs/"],
            main_flow_to_connect="Registry validation -> Gate 0 preflight -> execution guard tests.",
            tests_or_probes_required=[
                "python -m pytest tests\\test_multi_agent_gate0_preflight.py tests\\test_conversation_registry.py tests\\test_cross_repo_execution_guards.py tests\\test_smoke_suite.py -q",
                "python scripts\\multi_agent_gate0_preflight.py --output _reports\\multi-agent-gate0-preflight-a1\\GATE0_PREFLIGHT.json",
            ],
            governance_record_requirements=["Verifier report must include command, exit code, and output summary."],
            parallel_group_id="local-readiness",
            parallel_safe=True,
            blocking_conditions=["Local tests fail", "CLI executes an external runtime", "Output omits HUMAN_REQUIRED details"],
        ),
        _assignment(
            worker_role="Quality-Reviewer",
            task_spec=quality_task,
            project_module="multi-agent quality review",
            target="Review safety, error handling, and fake-green resistance in readiness scripts.",
            why_big_module="Quality review protects the project from claiming readiness based on weak or misleading probes.",
            allowed_modify_range=["_reports/multi-agent-quality-review-a1/"],
            forbidden_modify_range=["scripts/", "tests/", ".agent/", "docs/"],
            main_flow_to_connect="Execution guard behavior -> review findings -> serial Integrator handoff.",
            tests_or_probes_required=["read-only code review with P0/P1/P2 findings"],
            governance_record_requirements=["Quality report must list review focus and residual risk."],
            parallel_group_id="local-readiness",
            parallel_safe=True,
            blocking_conditions=["Open P0/P1 finding", "Reviewer needs to modify implementation"],
        ),
        _assignment(
            worker_role="Integrator",
            task_spec=integrator_task,
            project_module="multi-agent governance integration",
            target="Serially fold accepted first-wave reports into governance docs.",
            why_big_module="Integrator is the controlled write point for shared governance docs.",
            allowed_modify_range=["docs/governance/"],
            forbidden_modify_range=["scripts/", "tests/", ".agent/", "docs/agent-runtime/"],
            main_flow_to_connect="Reviewer/verifier reports -> governance logs -> next dispatch wave.",
            tests_or_probes_required=["git diff --check -- docs\\governance\\PROGRESS_LOG.md docs\\governance\\VERIFY_MATRIX.md docs\\governance\\HANDOFF.md"],
            governance_record_requirements=["Update progress, verify matrix, risk/debt if and only if backed by report evidence."],
            parallel_group_id="serial-integration",
            parallel_safe=False,
            blocking_conditions=["Any required first-wave report missing", "Shared governance docs changed by another active worker"],
        ),
        _assignment(
            worker_role="Human Gate",
            task_spec=binding_task,
            project_module="conversation binding activation",
            target="Provide real independent agent/conversation binding evidence.",
            why_big_module="The pilot cannot be real multi-agent without independent conversation bindings.",
            allowed_modify_range=[".agent/CONVERSATION_BINDING.json"],
            forbidden_modify_range=["scripts/", "tests/", "docs/"],
            main_flow_to_connect="Manual binding evidence -> Gate 0 PASS candidate.",
            tests_or_probes_required=["python scripts\\validate_conversation_registry.py .agent\\CONVERSATION_BINDING.json --project-root D:\\agent-acceptance"],
            governance_record_requirements=["Decision log must record source of binding evidence without secrets."],
            parallel_group_id="human-gated-activation",
            parallel_safe=False,
            blocking_conditions=[
                "Missing or invalid conversation binding",
                "Agent count below minimum",
                "Binding not in active status",
            ],
        ),
        _assignment(
            worker_role="Human Reviewer",
            task_spec=cap_task,
            project_module="CAP-029 execution approval",
            target="Decide whether dev-frame-opencode dispatch can become executable.",
            why_big_module="Execution approval changes the runtime authority boundary for real dispatch.",
            allowed_modify_range=["docs/agent-runtime/capability-inventory.md"],
            forbidden_modify_range=["scripts/", "tests/", ".agent/"],
            main_flow_to_connect="Capability approval -> Gate 0 PASS candidate -> real dispatch.",
            tests_or_probes_required=["python scripts\\multi_agent_gate0_preflight.py --output _reports\\multi-agent-gate0-preflight-a1\\GATE0_PREFLIGHT.json"],
            governance_record_requirements=["Decision log and risk register must record approval basis and limits."],
            parallel_group_id="human-gated-activation",
            parallel_safe=False,
            blocking_conditions=[
                "CAP-029 not registered",
                "CAP-029 not approved for gate0",
                "Tool policy missing runtime gates",
            ],
        ),
    ]


def _load_preflight(preflight_path: Path | None) -> dict[str, Any]:
    if preflight_path is None:
        return {
            "path": None,
            "sha256": None,
            "generated_at": None,
            "overall": "HUMAN_REQUIRED",
            "human_gate_required": True,
            "executed_external_runtime": False,
            "detail": "No preflight path supplied; dispatch remains human-gated.",
        }
    data, error = _load_json(preflight_path)
    if error or data is None:
        return {
            "path": str(preflight_path),
            "sha256": None,
            "generated_at": None,
            "overall": "BLOCKED",
            "human_gate_required": False,
            "executed_external_runtime": False,
            "detail": error or "preflight load failed",
        }
    preflight_sha = hashlib.sha256(preflight_path.read_bytes()).hexdigest()
    return {
        "path": str(preflight_path),
        "sha256": preflight_sha,
        "generated_at": data.get("generated_at"),
        "overall": data.get("overall"),
        "human_gate_required": data.get("human_gate_required"),
        "executed_external_runtime": data.get("executed_external_runtime"),
        "detail": "Loaded Gate 0 preflight artifact.",
    }


def _summarize_conflicts(assignments: list[dict[str, Any]]) -> dict[str, Any]:
    errors: list[str] = []
    task_ids: list[str] = []
    compared_write_pairs: list[list[str]] = []

    for assignment in assignments:
        task_spec = assignment["task_spec"]
        task_id = task_spec["task_id"]
        if task_id in task_ids:
            errors.append(f"duplicate task_id: {task_id}")
        task_ids.append(task_id)

        conflict_registry = task_spec.get("conflict_registry", {})
        if assignment.get("parallel_safe") and conflict_registry.get("protected_files_touched"):
            errors.append(f"{task_id} is parallel_safe but touches protected files")

    by_group: dict[str, list[dict[str, Any]]] = {}
    for assignment in assignments:
        if assignment.get("parallel_safe") and assignment["task_spec"].get("status") == "ready":
            by_group.setdefault(assignment["parallel_group_id"], []).append(assignment)

    for group_id, group_assignments in by_group.items():
        for left_idx, left in enumerate(group_assignments):
            left_writes = left["task_spec"]["conflict_registry"]["write_set"]
            for right in group_assignments[left_idx + 1:]:
                right_writes = right["task_spec"]["conflict_registry"]["write_set"]
                for left_path in left_writes:
                    for right_path in right_writes:
                        if _paths_conflict(left_path, right_path):
                            errors.append(
                                f"write conflict in {group_id}: {left['task_spec']['task_id']}:{left_path} overlaps {right['task_spec']['task_id']}:{right_path}"
                            )
                        compared_write_pairs.append([left_path, right_path])

    return {
        "has_write_conflicts": any("write conflict" in error for error in errors),
        "has_errors": bool(errors),
        "errors": errors,
        "parallel_group_count": len(by_group),
        "compared_write_pairs": compared_write_pairs,
    }


def validate_plan(plan: dict[str, Any]) -> tuple[bool, list[str]]:
    errors: list[str] = []
    validator = _load_task_spec_validator()

    if plan.get("executed_external_runtime") is not False:
        errors.append("dispatch plan must not claim external runtime execution")

    if plan.get("source_preflight", {}).get("executed_external_runtime") is True:
        errors.append("source preflight unexpectedly executed external runtime")

    if plan.get("status") == "READY":
        source = plan.get("source_preflight", {})
        if source.get("overall") != "PASS" or source.get("human_gate_required") is not False:
            errors.append("READY plan requires a PASS preflight with human_gate_required=false")
        for assignment in plan.get("assignments", []):
            if assignment.get("parallel_group_id") != "human-gated-activation":
                continue
            task_spec = assignment.get("task_spec", {})
            if task_spec.get("status") not in {
                "completed",
                "closed",
                "accepted_with_limitation",
            }:
                errors.append(
                    "READY plan has unresolved human activation task: "
                    + str(task_spec.get("task_id", "<unknown>"))
                )

    for assignment in plan.get("assignments", []):
        task_spec = assignment.get("task_spec", {})
        schema_errors = sorted(
            validator.iter_errors(task_spec),
            key=lambda error: list(error.absolute_path),
        )
        for error in schema_errors:
            errors.append(f"{task_spec.get('task_id', '<unknown>')} schema error: {error.message}")

    conflict_summary = _summarize_conflicts(plan.get("assignments", []))
    errors.extend(conflict_summary["errors"])
    return not errors, errors


def build_plan(
    *,
    plan_id: str = "multi-agent-dispatch-plan-a1",
    preflight_path: Path | None = None,
) -> dict[str, Any]:
    source_preflight = _load_preflight(preflight_path)
    activation_complete = (
        source_preflight.get("overall") == "PASS"
        and source_preflight.get("human_gate_required") is False
    )
    assignments = _default_assignments(activation_complete=activation_complete)
    conflict_summary = _summarize_conflicts(assignments)

    status = "READY"
    if conflict_summary["has_errors"]:
        status = "BLOCKED"
    elif source_preflight.get("overall") == "HUMAN_REQUIRED" or source_preflight.get("human_gate_required"):
        status = "HUMAN_REQUIRED"
    elif source_preflight.get("overall") == "BLOCKED":
        status = "BLOCKED"

    return {
        "plan_id": plan_id,
        "generated_at": _utc_now(),
        "status": status,
        "executed_external_runtime": False,
        "source_preflight": source_preflight,
        "conflict_summary": conflict_summary,
        "assignments": assignments,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build a read-only multi-agent dispatch plan packet."
    )
    parser.add_argument(
        "--preflight",
        help="Optional Gate 0 preflight JSON artifact to bind into the dispatch plan.",
    )
    parser.add_argument("--output", help="Optional path to write the dispatch plan JSON.")
    parser.add_argument("--plan-id", default="multi-agent-dispatch-plan-a1")
    args = parser.parse_args()

    plan = build_plan(
        plan_id=args.plan_id,
        preflight_path=Path(args.preflight) if args.preflight else None,
    )
    valid, errors = validate_plan(plan)
    if not valid:
        plan["status"] = "BLOCKED"
        plan["conflict_summary"]["errors"].extend(
            error for error in errors if error not in plan["conflict_summary"]["errors"]
        )
        plan["conflict_summary"]["has_errors"] = True

    plan_json = json.dumps(plan, indent=2, ensure_ascii=False)
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(plan_json + "\n", encoding="utf-8")
    print(plan_json)

    if plan["status"] == "READY":
        sys.exit(0)
    if plan["status"] == "HUMAN_REQUIRED":
        sys.exit(2)
    sys.exit(1)


if __name__ == "__main__":
    main()
