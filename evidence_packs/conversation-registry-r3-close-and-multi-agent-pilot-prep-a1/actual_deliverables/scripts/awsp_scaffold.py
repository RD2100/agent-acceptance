#!/usr/bin/env python3
"""awsp_scaffold.py — Generate AWSP-compliant project directory structure.

Creates the standard directory layout required by Agent Workflow Standard Protocol
(AWSP) v1.1.0 for any project. Designed for cross-project use.

Usage:
    # Create scaffold in current directory:
    python scripts/awsp_scaffold.py --project-root /path/to/project

    # Dry run (preview only):
    python scripts/awsp_scaffold.py --project-root /path/to/project --dry-run

    # Force overwrite existing empty directories:
    python scripts/awsp_scaffold.py --project-root /path/to/project --force
"""

import argparse
import json
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path


AWSP_VERSION = "1.3.0"

# Standard AWSP directory layout
AWSP_DIRECTORIES = [
    "evidence_packs",
    "_reports",
    "docs",
    "scripts",
    "tests",
    ".agent",
]

# Template files to generate
AWSP_TEMPLATES = {
    "docs/AGENT_WORKFLOW_STANDARD.md": """# Agent Workflow Standard Protocol (AWSP) v__AWSP_VERSION__

## Purpose

Defines the canonical workflow for agent hardening tasks in this project.
Ensures consistency across all evidence packs, GPT review submissions, and verification steps.

## Core Principles

1. **Run-ID Consistency**: All run_id values MUST be identical across:
   - Evidence pack filename
   - `run_id.txt` and `R1_RUN_ID.txt` content
   - GPT review prompt `{{RUN_ID}}` substitution
   - GPT reply `run_id:` field

2. **Evidence Pack Standard**: Every pack MUST include:
   - `PACK_MANIFEST.md` with proper markdown table
   - All evidence files listed in manifest
   - PACK_MANIFEST.md itself listed as `core` role

3. **Prompt Template Standard**: Every GPT review prompt MUST:
   - Use `{{RUN_ID}}` template variable (not hardcoded)
   - Include `{{TASK_ID}}` template variable
   - End with `---END_OF_GPT_RESPONSE---` marker
   - Use `overall_judgment:` field name (not `verdict:`)

4. **Verification Standard**: After GPT reply:
   - Verify run_id in reply matches submitted run_id
   - Verify `END_OF_GPT_RESPONSE` marker present
   - Create GPT_REVIEW_RECORD with full metadata
""",
    ".awsp.json": """{
    "awsp_version": "__AWSP_VERSION__",
    "project_root": "__PROJECT_ROOT__",
    "created_at": "__TIMESTAMP__",
    "directories": __DIRS_JSON__,
    "validation": {
        "require_run_id_consistency": true,
        "require_evidence_pack": true,
        "require_prompt_template_vars": true,
        "require_end_marker": true,
        "require_overall_judgment": true
    }
}
""",
    ".agent/REQUIRED_READS.json": """{
    "schema_version": "1.0.0",
    "awsp_version": "__AWSP_VERSION__",
    "project_root": "__PROJECT_ROOT__",
    "required_reads": [
        {
            "path": ".agent/PROJECT_AGENT_CONFIG.json",
            "evidence_level": "P0",
            "must_read_at_startup": true,
            "fail_closed_if_missing": true,
            "description": "Project agent configuration — defines governance rules for this project"
        },
        {
            "path": ".agent/GATE_CONFIG.json",
            "evidence_level": "P0",
            "must_read_at_startup": true,
            "fail_closed_if_missing": true,
            "description": "Gate configuration — defines pre-task and pre-GPT review gates"
        },
        {
            "path": "docs/AGENT_WORKFLOW_STANDARD.md",
            "evidence_level": "P1",
            "must_read_at_startup": true,
            "fail_closed_if_missing": false,
            "description": "AWSP standard document — workflow rules and conventions"
        }
    ]
}
""",
    ".agent/PROJECT_AGENT_CONFIG.json": """{
    "schema_version": "1.0.0",
    "awsp_version": "__AWSP_VERSION__",
    "project_root": "__PROJECT_ROOT__",
    "created_at": "__TIMESTAMP__",
    "governance": {
        "enforce_startup_read_gate": true,
        "enforce_pre_task_gate": true,
        "enforce_pre_gpt_review_gate": true,
        "enforce_state_machine": true,
        "enforce_human_required_decision_record": true
    },
    "state_machine": {
        "enabled": true,
        "states": [
            "draft", "gate_passing", "gpt_reviewing",
            "accepted", "accepted_with_limitation",
            "blocked", "human_required", "closed"
        ],
        "max_review_rounds": 5,
        "fail_closed_on_unknown_state": true
    },
    "evidence_pack": {
        "required_files": [
            "CLOSURE_REPORT.md",
            "GPT_REVIEW_PROMPT.md",
            "PACK_MANIFEST.md",
            "SAFETY_ATTESTATION.md"
        ],
        "required_dirs": ["actual_deliverables", "reports"],
        "summary_only_risk_check": true
    },
    "scripts": {
        "validate_run_id": "scripts/validate_run_id_consistency.py",
        "verify_gpt_reply": "scripts/verify_gpt_reply.py",
        "evidence_pack_linter": "scripts/evidence_pack_linter.py",
        "pre_gpt_review_gate": "scripts/pre_gpt_review_gate.py",
        "startup_read_gate": "scripts/startup_read_gate.py",
        "state_machine_runtime": "scripts/state_machine_runtime.py",
        "human_decision_record": "scripts/human_decision_record.py"
    }
}
""",
    ".agent/GATE_CONFIG.json": """{
    "schema_version": "1.0.0",
    "awsp_version": "__AWSP_VERSION__",
    "gates": {
        "startup_read_gate": {
            "enabled": true,
            "strict_mode": true,
            "required_reads_path": ".agent/REQUIRED_READS.json",
            "proof_template_path": ".agent/startup_proof_template.json",
            "block_on_failure": true
        },
        "pre_task_gate": {
            "enabled": true,
            "checks": [
                "task_id_authorized",
                "previous_verdict_allows_continuation",
                "startup_read_gate_passed"
            ],
            "block_on_failure": true
        },
        "pre_gpt_review_gate": {
            "enabled": true,
            "checks": [
                "evidence_pack_linter_pass",
                "actual_deliverables_not_empty",
                "pack_manifest_has_sha256",
                "startup_read_gate_passed"
            ],
            "block_on_failure": true
        }
    }
}
""",
    ".agent/startup_proof_template.json": """{
    "schema_version": "1.0.0",
    "task_id": "<REPLACE_WITH_TASK_ID>",
    "gate_status": "pass",
    "agent_id": "<REPLACE_WITH_AGENT_ID>",
    "timestamp": "<REPLACE_AT_RUNTIME>",
    "reads_completed": [
        {
            "file": ".agent/PROJECT_AGENT_CONFIG.json",
            "summary_hash": "sha256:<COMPUTE_AT_RUNTIME>",
            "read_confirmed": true
        },
        {
            "file": ".agent/GATE_CONFIG.json",
            "summary_hash": "sha256:<COMPUTE_AT_RUNTIME>",
            "read_confirmed": true
        },
        {
            "file": "docs/AGENT_WORKFLOW_STANDARD.md",
            "summary_hash": "sha256:<COMPUTE_AT_RUNTIME>",
            "read_confirmed": true
        }
    ]
}
""",
    # --- Governance script templates (v1.2.0 deployable stubs) ---
    "scripts/startup_read_gate.py": '''#!/usr/bin/env python3
"""startup_read_gate.py -- Startup Read Gate enforcement (AWSP v__AWSP_VERSION__).

Verifies that an agent has completed all required reads before starting work.
Deployed by awsp_scaffold.py; customize per project.

Exit codes: 0=pass, 1=blocked
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def gate(task_id: str, proof_path: str, required_reads_path: str,
         repo_root: str = None, strict: bool = False) -> dict:
    """Evaluate startup read gate.

    Returns dict with gate_passed, errors, warnings, extra_checks.
    """
    errors = []
    warnings = []
    proof = Path(proof_path)
    reads = Path(required_reads_path)

    if not proof.exists():
        errors.append(f"Proof file not found: {proof}")
    if not reads.exists():
        errors.append(f"Required reads not found: {reads}")

    if errors:
        return {"gate_passed": False, "errors": errors, "warnings": warnings,
                "extra_checks": {}}

    try:
        proof_data = json.loads(proof.read_text(encoding="utf-8"))
        reads_data = json.loads(reads.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        errors.append(f"Failed to load config: {exc}")
        return {"gate_passed": False, "errors": errors, "warnings": warnings,
                "extra_checks": {}}

    if proof_data.get("gate_status") != "pass":
        errors.append(f"Proof gate_status is not pass")

    # TODO: Add project-specific hash verification logic here
    if strict:
        for r in reads_data.get("required_reads", []):
            if r.get("must_read_at_startup") and not r.get("fail_closed_if_missing"):
                warnings.append(f"Entry {r.get('path')} has must_read but not fail_closed")

    return {"gate_passed": len(errors) == 0, "errors": errors,
            "warnings": warnings, "extra_checks": {"strict": strict}}


def main():
    parser = argparse.ArgumentParser(description="Startup Read Gate")
    parser.add_argument("--task-id", required=True)
    parser.add_argument("--proof-path", required=True)
    parser.add_argument("--required-reads", required=True)
    parser.add_argument("--repo-root", default=None)
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()
    result = gate(args.task_id, args.proof_path, args.required_reads,
                  repo_root=args.repo_root, strict=args.strict)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    sys.exit(0 if result["gate_passed"] else 1)


if __name__ == "__main__":
    main()
''',
    "scripts/pre_gpt_review_gate.py": '''#!/usr/bin/env python3
"""pre_gpt_review_gate.py -- Pre-GPT Review Gate (AWSP v__AWSP_VERSION__).

Gates evidence pack before CDP submission. Runs linter + targeted checks.
Deployed by awsp_scaffold.py; customize per project.

Exit codes: 0=pass, 1=blocked
"""
import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent


def gate(pack_dir: str, startup_proof_path: str = None,
         required_reads_path: str = None, strict: bool = False) -> dict:
    """Evaluate pre-GPT review gate.

    Returns dict with gate_passed, errors, warnings.
    """
    errors = []
    warnings = []
    pack = Path(pack_dir)

    if not pack.exists():
        errors.append(f"Pack directory not found: {pack}")
        return {"gate_passed": False, "errors": errors, "warnings": warnings}

    # Check required files
    required = ["CLOSURE_REPORT.md", "GPT_REVIEW_PROMPT.md",
                "PACK_MANIFEST.md", "SAFETY_ATTESTATION.md"]
    for f in required:
        if not (pack / f).exists():
            errors.append(f"Missing required file: {f}")

    # Check required dirs
    for d in ["actual_deliverables", "reports"]:
        if not (pack / d).is_dir():
            errors.append(f"Missing required directory: {d}")

    # TODO: Integrate evidence_pack_linter for SD-01 check
    # TODO: Add startup_read_gate integration via --startup-proof-path

    return {"gate_passed": len(errors) == 0, "errors": errors,
            "warnings": warnings}


def main():
    parser = argparse.ArgumentParser(description="Pre-GPT Review Gate")
    parser.add_argument("pack_dir")
    parser.add_argument("--startup-proof-path", default=None)
    parser.add_argument("--required-reads", default=None)
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()
    result = gate(args.pack_dir, startup_proof_path=args.startup_proof_path,
                  required_reads_path=args.required_reads, strict=args.strict)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    sys.exit(0 if result["gate_passed"] else 1)


if __name__ == "__main__":
    main()
''',
    "scripts/pre_task_gate.py": '''#!/usr/bin/env python3
"""pre_task_gate.py -- Pre-Task Gate (AWSP v__AWSP_VERSION__).

Validates task authorization, previous verdict continuity, and startup gate
pass before allowing task execution. Deployed by awsp_scaffold.py.

Exit codes: 0=pass, 1=blocked
"""
import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent


def gate(task_id: str, config_path: str = None,
         startup_proof_path: str = None, strict: bool = False) -> dict:
    """Evaluate pre-task gate.

    Checks:
    1. task_id is authorized (previous verdict allows continuation)
    2. startup_read_gate passed (if proof path provided)

    Returns dict with gate_passed, errors, warnings.
    """
    errors = []
    warnings = []

    if not task_id:
        errors.append("task_id is required")

    # TODO: Check previous verdict allows continuation
    # TODO: Integrate startup_read_gate.gate() via startup_proof_path
    # TODO: Check task_id is in authorized task list from config

    if startup_proof_path:
        proof = Path(startup_proof_path)
        if not proof.exists():
            errors.append(f"Startup proof not found: {proof}")
        else:
            try:
                data = json.loads(proof.read_text(encoding="utf-8"))
                if data.get("gate_status") != "pass":
                    errors.append("Startup read gate did not pass")
            except (json.JSONDecodeError, OSError) as exc:
                errors.append(f"Failed to read startup proof: {exc}")

    return {"gate_passed": len(errors) == 0, "errors": errors,
            "warnings": warnings}


def main():
    parser = argparse.ArgumentParser(description="Pre-Task Gate")
    parser.add_argument("--task-id", required=True)
    parser.add_argument("--config-path", default=None)
    parser.add_argument("--startup-proof-path", default=None)
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()
    result = gate(args.task_id, config_path=args.config_path,
                  startup_proof_path=args.startup_proof_path, strict=args.strict)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    sys.exit(0 if result["gate_passed"] else 1)


if __name__ == "__main__":
    main()
''',
    "scripts/state_machine_runtime.py": '''#!/usr/bin/env python3
"""state_machine_runtime.py -- Process State Machine (AWSP v__AWSP_VERSION__).

Provides state transition guards integrating startup_read_gate,
pre_gpt_review_gate, and human_decision_record. Deployed by awsp_scaffold.py.

Exit codes: 0=allowed, 1=blocked
"""
import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

STATES = {
    "draft": {"is_initial": True, "is_final": False},
    "gate_passing": {"is_initial": False, "is_final": False},
    "gpt_reviewing": {"is_initial": False, "is_final": False},
    "accepted": {"is_initial": False, "is_final": True},
    "accepted_with_limitation": {"is_initial": False, "is_final": True},
    "blocked": {"is_initial": False, "is_final": True},
    "human_required": {"is_initial": False, "is_final": False},
    "closed": {"is_initial": False, "is_final": True},
}

VALID_TRANSITIONS = {
    ("draft", "gate_passing"),
    ("gate_passing", "gpt_reviewing"),
    ("gpt_reviewing", "accepted"),
    ("gpt_reviewing", "accepted_with_limitation"),
    ("gpt_reviewing", "blocked"),
    ("gpt_reviewing", "human_required"),
    ("accepted_with_limitation", "gate_passing"),
    ("blocked", "gate_passing"),
    ("human_required", "gate_passing"),
    ("accepted", "closed"),
    ("accepted_with_limitation", "closed"),
}


def is_valid_transition(from_state: str, to_state: str) -> bool:
    return (from_state, to_state) in VALID_TRANSITIONS


def check_transition(from_state: str, to_state: str,
                     evidence_pack_dir: str = None,
                     startup_proof_path: str = None,
                     required_reads_path: str = None,
                     decision_record_path: str = None,
                     repo_root: str = None,
                     strict: bool = False) -> dict:
    """Evaluate a state transition.

    Returns dict with transition_allowed, guards, errors.
    """
    errors = []
    guards = {}

    if from_state not in STATES:
        errors.append(f"Unknown from_state: {from_state}")
    if to_state not in STATES:
        errors.append(f"Unknown to_state: {to_state}")
    if not is_valid_transition(from_state, to_state):
        errors.append(f"Invalid transition: {from_state} -> {to_state}")

    # TODO: Integrate startup_read_gate for draft -> gate_passing
    # TODO: Integrate pre_gpt_review_gate for gate_passing -> gpt_reviewing
    # TODO: Integrate human_decision_record for human_required -> gate_passing

    return {"transition_allowed": len(errors) == 0,
            "guards": guards, "errors": errors}


def main():
    parser = argparse.ArgumentParser(description="State Machine Runtime")
    parser.add_argument("--action", choices=["check-transition", "list-states",
                        "list-transitions"], required=True)
    parser.add_argument("--from-state", default=None)
    parser.add_argument("--to-state", default=None)
    parser.add_argument("--evidence-pack-dir", default=None)
    parser.add_argument("--startup-proof-path", default=None)
    parser.add_argument("--required-reads-path", default=None)
    parser.add_argument("--decision-record-path", default=None)
    parser.add_argument("--repo-root", default=None)
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()

    if args.action == "list-states":
        print(json.dumps(list(STATES.keys()), indent=2))
        sys.exit(0)
    elif args.action == "list-transitions":
        print(json.dumps([f"{f} -> {t}" for f, t in sorted(VALID_TRANSITIONS)],
                         indent=2))
        sys.exit(0)

    result = check_transition(
        args.from_state, args.to_state,
        evidence_pack_dir=args.evidence_pack_dir,
        startup_proof_path=args.startup_proof_path,
        required_reads_path=args.required_reads_path,
        decision_record_path=args.decision_record_path,
        repo_root=args.repo_root, strict=args.strict)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    sys.exit(0 if result["transition_allowed"] else 1)


if __name__ == "__main__":
    main()
''',
    "scripts/human_decision_record.py": '''#!/usr/bin/env python3
"""human_decision_record.py -- Human Decision Record Management (AWSP v__AWSP_VERSION__).

Creates and validates decision records for the human_required state.
Deployed by awsp_scaffold.py; customize per project.

Exit codes: 0=ok, 1=invalid
"""
import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
TZ_CST = timezone(timedelta(hours=8))
VALID_DECISION_TYPES = {"override", "approve", "reject", "defer"}
REQUIRED_FIELDS = [
    "task_id", "decision_type", "decision_reason",
    "decision_maker", "decision_timestamp",
]


def create_record(task_id: str, decision_type: str, decision_reason: str,
                  decision_maker: str, evidence_files: list = None,
                  gpt_verdict_context: str = None,
                  repo_root: str = None,
                  compute_hashes: bool = False) -> dict:
    """Create a human decision record.

    Returns dict with record data.
    """
    now = datetime.now(tz=TZ_CST).strftime("%Y-%m-%dT%H:%M:%S+08:00")
    record = {
        "task_id": task_id,
        "decision_type": decision_type,
        "decision_reason": decision_reason,
        "decision_maker": decision_maker,
        "decision_timestamp": now,
        "gpt_verdict_context": gpt_verdict_context or "",
        "evidence_hashes": {},
    }
    # TODO: Compute SHA-256 hashes for evidence files if compute_hashes=True
    return record


def validate_record(record_path: str, repo_root: str = None) -> dict:
    """Validate a human decision record.

    Returns dict with valid, errors.
    """
    errors = []
    path = Path(record_path)
    if not path.exists():
        return {"valid": False, "errors": [f"Record not found: {path}"]}

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        return {"valid": False, "errors": [f"Invalid JSON: {exc}"]}

    for field in REQUIRED_FIELDS:
        if field not in data or not data[field]:
            errors.append(f"Missing required field: {field}")

    if data.get("decision_type") and data["decision_type"] not in VALID_DECISION_TYPES:
        errors.append(f"Invalid decision_type: {data['decision_type']}")

    # TODO: Verify evidence hashes if present

    return {"valid": len(errors) == 0, "errors": errors}


def main():
    parser = argparse.ArgumentParser(description="Human Decision Record")
    sub = parser.add_subparsers(dest="action")

    create_p = sub.add_parser("create")
    create_p.add_argument("--task-id", required=True)
    create_p.add_argument("--decision-type", required=True,
                          choices=sorted(VALID_DECISION_TYPES))
    create_p.add_argument("--decision-reason", required=True)
    create_p.add_argument("--decision-maker", required=True)
    create_p.add_argument("--output", default=None)
    create_p.add_argument("--compute-hashes", action="store_true")

    validate_p = sub.add_parser("validate")
    validate_p.add_argument("record_path")
    validate_p.add_argument("--repo-root", default=None)

    args = parser.parse_args()

    if args.action == "create":
        record = create_record(
            args.task_id, args.decision_type, args.decision_reason,
            args.decision_maker, compute_hashes=args.compute_hashes)
        out = Path(args.output) if args.output else Path(
            f"_reports/{args.task_id}/HUMAN_DECISION_RECORD.json")
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(record, indent=2, ensure_ascii=False),
                       encoding="utf-8")
        print(json.dumps(record, indent=2, ensure_ascii=False))
        sys.exit(0)
    elif args.action == "validate":
        result = validate_record(args.record_path, repo_root=args.repo_root)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        sys.exit(0 if result["valid"] else 1)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
''',
    # --- Conversation Registry templates (v1.3.0) ---
    ".agent/CONVERSATION_BINDING.json": """{
    "schema_version": "1.0.0",
    "awsp_version": "__AWSP_VERSION__",
    "project_id": "__PROJECT_ID__",
    "project_root": "__PROJECT_ROOT__",
    "default_conversation_policy": "one_agent_one_conversation",
    "governance_scope": {
        "default_execution_policy": "human_gated_for_external_runtime_execution",
        "forbid_ad_hoc_gpt_submission": true,
        "forbid_cross_repo_smoke_without_human_gate": true,
        "external_runtimes": [
            {
                "runtime_id": "devframe-control-plane",
                "runtime_kind": "control_plane",
                "path": "D:/dev-frame/ai-workflow-hub",
                "governance_status": "in_scope_read_only",
                "allowed_actions": [
                    "read_policy",
                    "adapter_dry_run",
                    "pipeline_provenance_reference"
                ],
                "forbidden_actions": [
                    "modify_runtime_files",
                    "run_ai_workflow_hub",
                    "run_smoke_test",
                    "produce_gate_result",
                    "write_tasks_yaml_without_authorization"
                ],
                "human_gate_required": true
            },
            {
                "runtime_id": "dev-frame-opencode",
                "runtime_kind": "agent_dispatch",
                "path": null,
                "governance_status": "in_scope_human_gated",
                "allowed_actions": [
                    "dispatch_with_taskspec",
                    "return_execution_report",
                    "provide_diff_and_test_evidence"
                ],
                "forbidden_actions": [
                    "direct_gpt_submission",
                    "manual_flow_outcome",
                    "authoritative_closure_without_reviewer",
                    "bypass_submission_adapter"
                ],
                "human_gate_required": true
            },
            {
                "runtime_id": "paper-workflow",
                "runtime_kind": "business_workflow",
                "path": null,
                "governance_status": "in_scope_pilot_only",
                "allowed_actions": [
                    "synthetic_reference_pipeline",
                    "sanitized_paper_probe",
                    "evidence_pack_generation"
                ],
                "forbidden_actions": [
                    "real_user_paper_without_authorization",
                    "live_cdp_without_authorization",
                    "ad_hoc_playwright_submission",
                    "fabricated_gpt_review"
                ],
                "human_gate_required": true
            }
        ]
    },
    "bindings": [
        {
            "agent_id": "agent-local-001",
            "role": "reviewer",
            "binding_status": "pending_manual_binding",
            "conversation_id": null,
            "chat_url": null,
            "browser_profile_id": null,
            "cdp_endpoint": null,
            "allowed_task_scope": ["*"],
            "capture_policy": {
                "must_match_run_id": true,
                "must_match_task_id": true,
                "must_include_end_marker": true,
                "forbid_last_message_only_capture": true
            }
        }
    ]
}
""",
    ".agent/CONVERSATION_REGISTRY.schema.json": """{
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "schema_version": "1.0.0",
    "awsp_version": "__AWSP_VERSION__",
    "title": "AWSP Conversation Binding Schema",
    "description": "JSON Schema for the full CONVERSATION_BINDING.json file per AWSP v1.3.0",
    "type": "object",
    "required": [
        "schema_version",
        "awsp_version",
        "project_id",
        "project_root",
        "default_conversation_policy",
        "governance_scope",
        "bindings"
    ],
    "properties": {
        "schema_version": {
            "type": "string",
            "const": "1.0.0"
        },
        "awsp_version": {
            "type": "string",
            "const": "__AWSP_VERSION__"
        },
        "project_id": {
            "type": "string",
            "minLength": 1
        },
        "project_root": {
            "type": "string",
            "minLength": 1
        },
        "default_conversation_policy": {
            "type": "string",
            "enum": ["one_agent_one_conversation"]
        },
        "governance_scope": {
            "type": "object",
            "required": [
                "default_execution_policy",
                "forbid_ad_hoc_gpt_submission",
                "forbid_cross_repo_smoke_without_human_gate",
                "external_runtimes"
            ],
            "properties": {
                "default_execution_policy": {
                    "type": "string",
                    "enum": ["human_gated_for_external_runtime_execution"]
                },
                "forbid_ad_hoc_gpt_submission": {
                    "type": "boolean",
                    "const": true
                },
                "forbid_cross_repo_smoke_without_human_gate": {
                    "type": "boolean",
                    "const": true
                },
                "external_runtimes": {
                    "type": "array",
                    "minItems": 3,
                    "items": {
                        "type": "object",
                        "required": [
                            "runtime_id",
                            "runtime_kind",
                            "governance_status",
                            "allowed_actions",
                            "forbidden_actions",
                            "human_gate_required"
                        ],
                        "properties": {
                            "runtime_id": {
                                "type": "string",
                                "enum": [
                                    "devframe-control-plane",
                                    "dev-frame-opencode",
                                    "paper-workflow"
                                ]
                            },
                            "runtime_kind": {
                                "type": "string",
                                "enum": [
                                    "control_plane",
                                    "agent_dispatch",
                                    "business_workflow"
                                ]
                            },
                            "path": {
                                "type": ["string", "null"]
                            },
                            "governance_status": {
                                "type": "string",
                                "enum": [
                                    "in_scope_read_only",
                                    "in_scope_human_gated",
                                    "in_scope_pilot_only"
                                ]
                            },
                            "allowed_actions": {
                                "type": "array",
                                "minItems": 1,
                                "items": { "type": "string" }
                            },
                            "forbidden_actions": {
                                "type": "array",
                                "minItems": 1,
                                "items": { "type": "string" }
                            },
                            "human_gate_required": {
                                "type": "boolean",
                                "const": true
                            }
                        },
                        "additionalProperties": false
                    }
                }
            },
            "additionalProperties": false
        },
        "bindings": {
            "type": "array",
            "minItems": 1,
            "items": {
                "type": "object",
                "required": [
                    "agent_id",
                    "role",
                    "binding_status",
                    "capture_policy"
                ],
                "properties": {
                    "agent_id": {
                        "type": "string",
                        "minLength": 1
                    },
                    "role": {
                        "type": "string",
                        "enum": ["reviewer", "executor", "observer", "orchestrator"]
                    },
                    "binding_status": {
                        "type": "string",
                        "enum": [
                            "pending_manual_binding",
                            "active",
                            "paused",
                            "retired",
                            "invalid"
                        ]
                    },
                    "conversation_id": {
                        "type": ["string", "null"]
                    },
                    "chat_url": {
                        "type": ["string", "null"]
                    },
                    "browser_profile_id": {
                        "type": ["string", "null"]
                    },
                    "cdp_endpoint": {
                        "type": ["string", "null"]
                    },
                    "allowed_task_scope": {
                        "type": "array",
                        "items": { "type": "string" }
                    },
                    "capture_policy": {
                        "type": "object",
                        "required": [
                            "must_match_run_id",
                            "must_match_task_id",
                            "must_include_end_marker",
                            "forbid_last_message_only_capture"
                        ],
                        "properties": {
                            "must_match_run_id": {
                                "type": "boolean",
                                "const": true
                            },
                            "must_match_task_id": {
                                "type": "boolean",
                                "const": true
                            },
                            "must_include_end_marker": {
                                "type": "boolean",
                                "const": true
                            },
                            "forbid_last_message_only_capture": {
                                "type": "boolean",
                                "const": true
                            }
                        },
                        "additionalProperties": false
                    }
                },
                "if": {
                    "properties": { "binding_status": { "const": "active" } }
                },
                "then": {
                    "anyOf": [
                        {
                            "required": ["chat_url"],
                            "properties": {
                                "chat_url": {
                                    "type": "string",
                                    "minLength": 1
                                }
                            }
                        },
                        {
                            "required": ["conversation_id"],
                            "properties": {
                                "conversation_id": {
                                    "type": "string",
                                    "minLength": 1
                                }
                            }
                        }
                    ]
                },
                "additionalProperties": true
            }
        }
    },
    "additionalProperties": true
}
""",
}


def create_scaffold(project_root: str, dry_run: bool = False, force: bool = False) -> dict:
    """Create AWSP-compliant directory structure.

    Args:
        project_root: Root directory of the project.
        dry_run: If True, only preview what would be created.
        force: If True, overwrite existing empty directories.

    Returns:
        dict with created, skipped, errors, config.
    """
    root = Path(project_root)
    result = {"created": [], "skipped": [], "errors": [], "config": None}

    if not root.exists():
        result["errors"].append(f"Project root does not exist: {root}")
        return result

    # Resolve to absolute path for consistent project_root storage
    resolved_root = root.resolve()

    # Create directories
    for d in AWSP_DIRECTORIES:
        dir_path = root / d
        if dir_path.exists() and dir_path.is_dir():
            if force:
                result["skipped"].append(str(d))
            else:
                result["skipped"].append(str(d))
        elif dir_path.exists():
            result["errors"].append(f"{d} exists but is not a directory")
        else:
            if not dry_run:
                dir_path.mkdir(parents=True, exist_ok=True)
            result["created"].append(str(d))

    # Generate template files
    tz = timezone(timedelta(hours=8))
    now = datetime.now(tz=tz)
    timestamp = now.strftime("%Y-%m-%dT%H:%M:%S+08:00")

    for rel_path, template in AWSP_TEMPLATES.items():
        file_path = root / rel_path
        if file_path.exists() and not force:
            result["skipped"].append(rel_path)
            continue

        content = template.replace("__AWSP_VERSION__", AWSP_VERSION)
        content = content.replace("__PROJECT_ID__", resolved_root.name)
        content = content.replace("__PROJECT_ROOT__", str(resolved_root).replace("\\", "/"))
        content = content.replace("__TIMESTAMP__", timestamp)
        content = content.replace("__DIRS_JSON__", json.dumps(AWSP_DIRECTORIES))

        if not dry_run:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content, encoding="utf-8")
        result["created"].append(rel_path)

    # Generate .awsp.json config
    config = {
        "awsp_version": AWSP_VERSION,
        "project_root": str(resolved_root).replace("\\", "/"),
        "created_at": timestamp,
        "directories": AWSP_DIRECTORIES,
        "validation": {
            "require_run_id_consistency": True,
            "require_evidence_pack": True,
            "require_prompt_template_vars": True,
            "require_end_marker": True,
            "require_overall_judgment": True,
        },
    }
    result["config"] = config

    return result


def validate_scaffold(project_root: str) -> dict:
    """Validate that a project has the AWSP-compliant structure.

    Args:
        project_root: Root directory of the project.

    Returns:
        dict with valid, errors, details.
    """
    root = Path(project_root)
    errors = []
    details = {}

    if not root.exists():
        return {"valid": False, "errors": ["Project root does not exist"], "details": {}}

    # Check directories
    missing_dirs = []
    for d in AWSP_DIRECTORIES:
        dir_path = root / d
        if dir_path.exists() and dir_path.is_dir():
            details[f"dir_{d}"] = "exists"
        else:
            missing_dirs.append(d)
            details[f"dir_{d}"] = "missing"

    if missing_dirs:
        errors.append(f"Missing AWSP directories: {', '.join(missing_dirs)}")

    # Check config file
    config_path = root / ".awsp.json"
    if config_path.exists():
        try:
            config = json.loads(config_path.read_text(encoding="utf-8"))
            details["config_exists"] = True
            details["config_valid"] = True

            # Check awsp_version
            cfg_version = config.get("awsp_version")
            details["config_version"] = cfg_version or "unknown"
            if cfg_version != AWSP_VERSION:
                errors.append(
                    f".awsp.json awsp_version mismatch: "
                    f"found '{cfg_version}', expected '{AWSP_VERSION}'"
                )
                details["config_valid"] = False

            # Check required config fields
            required_fields = ["awsp_version", "project_root", "directories", "validation"]
            missing_fields = [f for f in required_fields if f not in config]
            if missing_fields:
                errors.append(
                    f".awsp.json missing required fields: {', '.join(missing_fields)}"
                )
                details["config_valid"] = False

            # Check validation config
            validation_cfg = config.get("validation", {})
            expected_checks = [
                "require_run_id_consistency",
                "require_evidence_pack",
                "require_prompt_template_vars",
                "require_end_marker",
                "require_overall_judgment",
            ]
            missing_validation = [c for c in expected_checks if c not in validation_cfg]
            if missing_validation:
                errors.append(
                    f".awsp.json validation section missing: {', '.join(missing_validation)}"
                )
                details["config_valid"] = False
            else:
                # Check that all validation values are true (fail-closed)
                false_checks = [c for c in expected_checks if not validation_cfg.get(c)]
                if false_checks:
                    errors.append(
                        f".awsp.json validation values not all true: {', '.join(false_checks)} = false"
                    )
                    details["config_valid"] = False

            # Check directories field matches AWSP_DIRECTORIES
            cfg_dirs = config.get("directories", [])
            if sorted(cfg_dirs) != sorted(AWSP_DIRECTORIES):
                errors.append(
                    f".awsp.json directories field mismatch: "
                    f"found {cfg_dirs}, expected {AWSP_DIRECTORIES}"
                )
                details["config_valid"] = False

        except (json.JSONDecodeError, OSError) as e:
            errors.append(f".awsp.json exists but is invalid: {e}")
            details["config_exists"] = True
            details["config_valid"] = False
    else:
        errors.append(".awsp.json config file not found")
        details["config_exists"] = False

    # Check AWSP standard doc
    doc_path = root / "docs" / "AGENT_WORKFLOW_STANDARD.md"
    if doc_path.exists():
        details["awsp_doc_exists"] = True
    else:
        errors.append("docs/AGENT_WORKFLOW_STANDARD.md not found")
        details["awsp_doc_exists"] = False

    # Check project_root matches actual project root
    config_path = root / ".awsp.json"
    if config_path.exists():
        try:
            config = json.loads(config_path.read_text(encoding="utf-8"))
            cfg_project_root = config.get("project_root", "")
            actual_root = str(root.resolve()).replace("\\", "/")
            cfg_root_normalized = cfg_project_root.replace("\\", "/").rstrip("/")
            actual_root_normalized = actual_root.rstrip("/")
            if cfg_root_normalized and cfg_root_normalized != actual_root_normalized:
                errors.append(
                    f".awsp.json project_root mismatch: "
                    f"found '{cfg_root_normalized}', actual '{actual_root_normalized}'"
                )
                details["project_root_valid"] = False
            else:
                details["project_root_valid"] = True
        except (json.JSONDecodeError, OSError):
            pass  # Already handled above

    # Check .agent/ governance config files (v1.2.0)
    agent_config_files = [
        ".agent/REQUIRED_READS.json",
        ".agent/PROJECT_AGENT_CONFIG.json",
        ".agent/GATE_CONFIG.json",
        ".agent/startup_proof_template.json",
    ]
    missing_agent_files = []
    for af in agent_config_files:
        af_path = root / af
        if af_path.exists():
            # Validate JSON structure
            try:
                data = json.loads(af_path.read_text(encoding="utf-8"))
                # Check schema_version exists
                if "schema_version" not in data:
                    errors.append(f"{af} missing required field: schema_version")
                details[f"agent_{af}"] = "exists"

                # Content validation per file type (R2 enhancement)
                if af == ".agent/PROJECT_AGENT_CONFIG.json":
                    cfg_awsp_ver = data.get("awsp_version")
                    if cfg_awsp_ver is None:
                        errors.append(
                            f".agent/PROJECT_AGENT_CONFIG.json missing required field: awsp_version"
                        )
                    elif cfg_awsp_ver != AWSP_VERSION:
                        errors.append(
                            f".agent/PROJECT_AGENT_CONFIG.json awsp_version "
                            f"mismatch: found '{cfg_awsp_ver}', expected '{AWSP_VERSION}'"
                        )
                    gov = data.get("governance", {})
                    required_gov_flags = [
                        "enforce_startup_read_gate",
                        "enforce_pre_task_gate",
                        "enforce_pre_gpt_review_gate",
                        "enforce_state_machine",
                        "enforce_human_required_decision_record",
                    ]
                    missing_flags = [f for f in required_gov_flags if f not in gov]
                    if missing_flags:
                        errors.append(
                            f".agent/PROJECT_AGENT_CONFIG.json missing governance flags: "
                            + ", ".join(missing_flags)
                        )
                    else:
                        # Strict: governance flags must be true (fail-closed)
                        false_flags = [
                            f for f in required_gov_flags if gov.get(f) is not True
                        ]
                        if false_flags:
                            errors.append(
                                f".agent/PROJECT_AGENT_CONFIG.json governance flags "
                                f"not all true (fail-closed): "
                                + ", ".join(false_flags)
                            )
                elif af == ".agent/GATE_CONFIG.json":
                    gates = data.get("gates", {})
                    required_gates = [
                        "startup_read_gate",
                        "pre_task_gate",
                        "pre_gpt_review_gate",
                    ]
                    missing_gates = [g for g in required_gates if g not in gates]
                    if missing_gates:
                        errors.append(
                            f".agent/GATE_CONFIG.json missing required gates: "
                            + ", ".join(missing_gates)
                        )
                    else:
                        # Strict: gate enabled/block_on_failure must be true
                        for gate_name in required_gates:
                            gate_cfg = gates.get(gate_name, {})
                            if gate_cfg.get("enabled") is not True:
                                errors.append(
                                    f".agent/GATE_CONFIG.json gate '{gate_name}' "
                                    f"must have enabled=true (fail-closed)"
                                )
                            if gate_cfg.get("block_on_failure") is not True:
                                errors.append(
                                    f".agent/GATE_CONFIG.json gate '{gate_name}' "
                                    f"must have block_on_failure=true (fail-closed)"
                                )
                        # startup_read_gate must have strict_mode=true
                        srg = gates.get("startup_read_gate", {})
                        if srg.get("strict_mode") is not True:
                            errors.append(
                                ".agent/GATE_CONFIG.json gate 'startup_read_gate' "
                                "must have strict_mode=true"
                            )
                elif af == ".agent/REQUIRED_READS.json":
                    if "required_reads" not in data:
                        errors.append(
                            ".agent/REQUIRED_READS.json missing required field: required_reads"
                        )
                    elif not isinstance(data["required_reads"], list):
                        errors.append(
                            ".agent/REQUIRED_READS.json required_reads must be an array"
                        )
                    else:
                        # Strict: validate each required_read entry structure
                        required_entry_fields = [
                            "path", "evidence_level",
                            "must_read_at_startup", "fail_closed_if_missing",
                        ]
                        valid_evidence_levels = {"P0", "P1"}
                        for idx, entry in enumerate(data["required_reads"]):
                            if not isinstance(entry, dict):
                                errors.append(
                                    f".agent/REQUIRED_READS.json entry[{idx}] "
                                    f"is not an object"
                                )
                                continue
                            missing_fields = [
                                f for f in required_entry_fields if f not in entry
                            ]
                            if missing_fields:
                                errors.append(
                                    f".agent/REQUIRED_READS.json entry[{idx}] "
                                    f"({entry.get('path', '?')}) missing fields: "
                                    + ", ".join(missing_fields)
                                )
                                continue
                            # Type checks for all entry fields
                            entry_path = entry.get("path")
                            if not isinstance(entry_path, str) or not entry_path:
                                errors.append(
                                    f".agent/REQUIRED_READS.json entry[{idx}] "
                                    f"path must be a non-empty string, "
                                    f"got {type(entry_path).__name__}"
                                )
                            if not isinstance(entry.get("must_read_at_startup"), bool):
                                errors.append(
                                    f".agent/REQUIRED_READS.json entry[{idx}] "
                                    f"({entry.get('path', '?')}) must_read_at_startup "
                                    f"must be a boolean"
                                )
                            if not isinstance(entry.get("fail_closed_if_missing"), bool):
                                errors.append(
                                    f".agent/REQUIRED_READS.json entry[{idx}] "
                                    f"({entry.get('path', '?')}) fail_closed_if_missing "
                                    f"must be a boolean"
                                )
                            level = entry.get("evidence_level")
                            if level not in valid_evidence_levels:
                                errors.append(
                                    f".agent/REQUIRED_READS.json entry[{idx}] "
                                    f"({entry.get('path', '?')}) invalid evidence_level: "
                                    f"'{level}' (must be P0 or P1)"
                                )
                            # P0 entries must have strict true flags
                            if level == "P0":
                                if entry.get("must_read_at_startup") is not True:
                                    errors.append(
                                        f".agent/REQUIRED_READS.json P0 entry "
                                        f"({entry.get('path', '?')}) must have "
                                        f"must_read_at_startup=true"
                                    )
                                if entry.get("fail_closed_if_missing") is not True:
                                    errors.append(
                                        f".agent/REQUIRED_READS.json P0 entry "
                                        f"({entry.get('path', '?')}) must have "
                                        f"fail_closed_if_missing=true"
                                    )
            except (json.JSONDecodeError, OSError) as e:
                errors.append(f"{af} exists but is invalid JSON: {e}")
                details[f"agent_{af}"] = "invalid"
        else:
            missing_agent_files.append(af)
            details[f"agent_{af}"] = "missing"

    if missing_agent_files:
        errors.append(
            f"Missing .agent/ governance config files: "
            + ", ".join(missing_agent_files)
        )

    # Check governance scripts (v1.2.0 deployable stubs)
    governance_scripts = {
        "scripts/startup_read_gate.py": "gate",
        "scripts/pre_gpt_review_gate.py": "gate",
        "scripts/pre_task_gate.py": "gate",
        "scripts/state_machine_runtime.py": "check_transition",
        "scripts/human_decision_record.py": "validate_record",
    }
    missing_scripts = []
    for script_path, core_func in governance_scripts.items():
        sp = root / script_path
        if sp.exists():
            try:
                content = sp.read_text(encoding="utf-8")
                # Check CLI entry point
                if 'if __name__' not in content:
                    errors.append(
                        f"{script_path} missing CLI entry point "
                        f"(if __name__ == \"__main__\")"
                    )
                # Check core function exists
                if f"def {core_func}(" not in content:
                    errors.append(
                        f"{script_path} missing core function: "
                        f"def {core_func}()"
                    )
                details[f"script_{script_path}"] = "exists"
            except OSError as e:
                errors.append(f"{script_path} exists but cannot be read: {e}")
                details[f"script_{script_path}"] = "unreadable"
        else:
            missing_scripts.append(script_path)
            details[f"script_{script_path}"] = "missing"

    if missing_scripts:
        errors.append(
            f"Missing governance scripts: " + ", ".join(missing_scripts)
        )

    # Check conversation binding and registry schema (v1.3.0)
    cb_path = root / ".agent" / "CONVERSATION_BINDING.json"
    cr_path = root / ".agent" / "CONVERSATION_REGISTRY.schema.json"
    if not cb_path.exists():
        errors.append(".agent/CONVERSATION_BINDING.json not found")
        details["conversation_binding"] = "missing"
    elif not cr_path.exists():
        errors.append(".agent/CONVERSATION_REGISTRY.schema.json not found")
        details["conversation_registry_schema"] = "missing"
    else:
        try:
            from validate_conversation_registry import validate_binding
        except ImportError as e:
            errors.append(f"validate_conversation_registry.py import failed: {e}")
            details["conversation_binding"] = "validator_unavailable"
        else:
            result = validate_binding(str(cb_path), project_root=str(root.resolve()))
            details["conversation_binding"] = "exists"
            details["conversation_registry_schema"] = "exists"
            details["conversation_registry_validation"] = result.get("summary", {})
            for err in result.get("errors", []):
                errors.append(f"CONVERSATION_BINDING validation: {err}")

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "details": details,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Generate AWSP-compliant project directory structure",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--project-root", required=True,
                        help="Root directory of the project")
    parser.add_argument("--dry-run", action="store_true",
                        help="Preview only, do not create files")
    parser.add_argument("--force", action="store_true",
                        help="Overwrite existing files")
    parser.add_argument("--validate", action="store_true",
                        help="Validate existing scaffold instead of creating")
    args = parser.parse_args()

    if args.validate:
        result = validate_scaffold(args.project_root)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        sys.exit(0 if result["valid"] else 1)
    else:
        result = create_scaffold(args.project_root, dry_run=args.dry_run, force=args.force)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        if result["errors"]:
            print("\nERRORS:")
            for e in result["errors"]:
                print(f"  {e}")
            sys.exit(1)
        elif args.dry_run:
            print("\nDRY RUN: No files created. Use without --dry-run to create.")
        else:
            print(f"\nAWSP scaffold created at: {args.project_root}")
        sys.exit(0)


if __name__ == "__main__":
    main()
