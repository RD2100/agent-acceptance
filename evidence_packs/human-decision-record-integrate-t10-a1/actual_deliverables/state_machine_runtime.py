#!/usr/bin/env python3
"""
state_machine_runtime.py — Process state machine runtime enforcement.

Provides state transition guards that integrate startup_read_gate,
pre_gpt_review_gate, and human_decision_record as conditions for
state transitions.

Per PROCESS_STATE_MACHINE.json and hardening plan §5.7.3.

Transitions with implemented guards:
  T01: draft → gate_passing (evidence pack + startup read gate)
  T10: human_required → gate_passing (human decision record validation)

Usage:
    python scripts/state_machine_runtime.py \
        --action check-transition \
        --from-state draft \
        --to-state gate_passing \
        [--startup-proof-path <proof.json>] \
        [--evidence-pack-dir <pack_dir>] \
        [--required-reads <reads.json>] \
        [--decision-record-path <record.json>] \
        [--strict]
"""

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

# State definitions from PROCESS_STATE_MACHINE.json
STATES = {
    "draft": {
        "is_initial": True,
        "is_final": False,
        "exit_conditions": ["evidence_pack_linter_pass", "evidence_pack_complete", "startup_read_gate_pass"],
    },
    "gate_passing": {
        "is_initial": False,
        "is_final": False,
        "entry_conditions": ["evidence_pack_linter_pass", "evidence_pack_complete", "startup_read_gate_pass"],
        "exit_conditions": ["pre_gpt_review_gate_all_pass", "attachment_uploaded", "prompt_ready"],
    },
    "gpt_reviewing": {
        "is_initial": False,
        "is_final": False,
        "entry_conditions": ["pre_gpt_review_gate_all_pass", "attachment_uploaded_and_confirmed", "prompt_sent", "user_bubble_confirmed"],
        "exit_conditions": ["gpt_response_received", "verify_gpt_reply_pass"],
    },
    "accepted": {
        "is_initial": False,
        "is_final": False,
        "entry_conditions": ["verdict=accepted", "verify_gpt_reply_pass"],
        "exit_conditions": ["closure_conditions_met", "next_task_authorization_generated"],
    },
    "accepted_with_limitation": {
        "is_initial": False,
        "is_final": False,
        "entry_conditions": ["verdict=accepted_with_limitation", "verify_gpt_reply_pass"],
        "exit_conditions": ["limitations_addressed", "closure_conditions_met", "next_task_authorization_generated"],
    },
    "blocked": {
        "is_initial": False,
        "is_final": False,
        "entry_conditions": ["verdict=blocked"],
        "exit_conditions": ["fixes_applied", "evidence_pack_rebuilt"],
    },
    "human_required": {
        "is_initial": False,
        "is_final": False,
        "entry_conditions": ["verdict=human_required", "safety_rule_triggered"],
        "exit_conditions": ["human_decision_recorded", "decision_evidence_attached"],
    },
    "closed": {
        "is_initial": False,
        "is_final": True,
        "entry_conditions": ["closure_conditions_met", "next_task_authorization_generated"],
        "exit_conditions": [],
    },
}

VALID_TRANSITIONS = {
    ("draft", "gate_passing"),              # T01
    ("gate_passing", "gpt_reviewing"),      # T02
    ("gpt_reviewing", "accepted"),          # T03
    ("gpt_reviewing", "accepted_with_limitation"), # T04
    ("gpt_reviewing", "blocked"),           # T05
    ("gpt_reviewing", "human_required"),    # T06
    ("accepted", "closed"),                 # T07
    ("accepted_with_limitation", "closed"), # T08
    ("blocked", "draft"),                   # T09
    ("human_required", "gate_passing"),     # T10
}


def is_valid_transition(from_state: str, to_state: str) -> bool:
    """Check if a state transition is valid per the state machine."""
    if from_state not in STATES or to_state not in STATES:
        return False
    return (from_state, to_state) in VALID_TRANSITIONS


def check_draft_to_gate_passing(
    evidence_pack_dir: str = None,
    startup_proof_path: str = None,
    required_reads_path: str = None,
    strict: bool = False,
) -> dict:
    """Check all guard conditions for draft → gate_passing transition.

    Returns dict with:
        transition_allowed: bool
        guards: dict of individual guard results
        errors: list of error messages
    """
    guards = {}
    errors = []

    # Guard 1: evidence_pack_linter_pass + evidence_pack_complete
    if evidence_pack_dir:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        try:
            from evidence_pack_linter import lint
            lint_result = lint(evidence_pack_dir)
            guards["evidence_pack_linter_pass"] = lint_result.get("valid", False)
            if not guards["evidence_pack_linter_pass"]:
                errors.extend(lint_result.get("errors", []))

            # Check pack completeness
            pack_path = Path(evidence_pack_dir)
            has_deliverables = False
            ad = pack_path / "actual_deliverables"
            if ad.is_dir() and list(ad.rglob("*")):
                has_deliverables = True
            guards["evidence_pack_complete"] = has_deliverables
            if not has_deliverables:
                errors.append("evidence pack has no deliverables")
        except ImportError as e:
            guards["evidence_pack_linter_pass"] = False
            guards["evidence_pack_complete"] = False
            errors.append(f"cannot import evidence_pack_linter: {e}")
    else:
        guards["evidence_pack_linter_pass"] = None
        guards["evidence_pack_complete"] = None

    # Guard 2: startup_read_gate_pass
    if startup_proof_path:
        try:
            from startup_read_gate import gate as startup_gate
            reads_path = required_reads_path
            if not reads_path:
                # Auto-detect
                from pre_gpt_review_gate import resolve_required_reads_path
                reads_path = resolve_required_reads_path()

            if reads_path:
                sr = startup_gate(
                    task_id="",
                    proof_path=startup_proof_path,
                    required_reads_path=reads_path,
                    repo_root=str(REPO),
                    strict=strict,
                )
                guards["startup_read_gate_pass"] = sr.get("gate_passed", False)
                if not guards["startup_read_gate_pass"]:
                    errors.extend(sr.get("errors", []))
            else:
                guards["startup_read_gate_pass"] = False
                errors.append("NEXT_AGENT_REQUIRED_READS.json not found")
        except ImportError as e:
            guards["startup_read_gate_pass"] = False
            errors.append(f"cannot import startup_read_gate: {e}")
    else:
        guards["startup_read_gate_pass"] = None

    # Determine if transition is allowed
    # Fail-closed: ALL guards must be explicitly checked and pass.
    # Any None guard means the check was skipped → transition BLOCKED.
    unchecked = [k for k, v in guards.items() if v is None]
    checked = {k: v for k, v in guards.items() if v is not None}

    if unchecked:
        for g in unchecked:
            errors.append(f"guard not checked: {g} (required for draft → gate_passing)")

    all_pass = all(checked.values()) if checked else False
    transition_allowed = all_pass and len(errors) == 0 and len(unchecked) == 0

    return {
        "transition": "draft → gate_passing",
        "transition_allowed": transition_allowed,
        "guards": guards,
        "errors": errors,
    }


def check_human_required_to_gate_passing(
    decision_record_path: str = None,
) -> dict:
    """Check all guard conditions for human_required → gate_passing (T10).

    T10 guards per PROCESS_STATE_MACHINE.json:
      - human_decision_recorded: a valid decision record exists
      - decision_evidence_attached: evidence files are attached

    Uses human_decision_record.validate_record() for validation.

    Returns dict with:
        transition_allowed: bool
        guards: dict of individual guard results
        errors: list of error messages
    """
    guards = {}
    errors = []

    if decision_record_path:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        try:
            from human_decision_record import validate_record
            vr = validate_record(decision_record_path)
            ec = vr.get("exit_conditions", {})
            guards["human_decision_recorded"] = ec.get("human_decision_recorded", False)
            guards["decision_evidence_attached"] = ec.get("decision_evidence_attached", False)

            if not vr.get("valid", False):
                errors.extend(vr.get("errors", []))
        except ImportError as e:
            guards["human_decision_recorded"] = False
            guards["decision_evidence_attached"] = False
            errors.append(f"cannot import human_decision_record: {e}")
    else:
        guards["human_decision_recorded"] = None
        guards["decision_evidence_attached"] = None

    # Fail-closed: ALL guards must be explicitly checked and pass.
    unchecked = [k for k, v in guards.items() if v is None]
    checked = {k: v for k, v in guards.items() if v is not None}

    if unchecked:
        for g in unchecked:
            errors.append(f"guard not checked: {g} (required for human_required → gate_passing)")

    all_pass = all(checked.values()) if checked else False
    transition_allowed = all_pass and len(errors) == 0 and len(unchecked) == 0

    return {
        "transition": "human_required → gate_passing",
        "transition_allowed": transition_allowed,
        "guards": guards,
        "errors": errors,
    }


def check_transition(
    from_state: str,
    to_state: str,
    evidence_pack_dir: str = None,
    startup_proof_path: str = None,
    required_reads_path: str = None,
    decision_record_path: str = None,
    strict: bool = False,
) -> dict:
    """Check if a state transition is allowed and all guards pass.

    Currently implements guard checks for:
    - draft → gate_passing (T01: evidence pack + startup read gate)
    - human_required → gate_passing (T10: human decision record validation)

    Other transitions return validity-only checks.
    """
    if not is_valid_transition(from_state, to_state):
        return {
            "transition": f"{from_state} → {to_state}",
            "transition_allowed": False,
            "guards": {},
            "errors": [f"invalid transition: {from_state} → {to_state}"],
        }

    if from_state == "draft" and to_state == "gate_passing":
        return check_draft_to_gate_passing(
            evidence_pack_dir=evidence_pack_dir,
            startup_proof_path=startup_proof_path,
            required_reads_path=required_reads_path,
            strict=strict,
        )

    if from_state == "human_required" and to_state == "gate_passing":
        return check_human_required_to_gate_passing(
            decision_record_path=decision_record_path,
        )

    # For other transitions, just confirm validity
    return {
        "transition": f"{from_state} → {to_state}",
        "transition_allowed": True,
        "guards": {},
        "errors": [],
        "note": "guard checks for this transition not yet implemented",
    }


def main():
    parser = argparse.ArgumentParser(
        description="State Machine Runtime — check transition guards"
    )
    parser.add_argument(
        "--action",
        choices=["check-transition", "list-states", "list-transitions"],
        default="check-transition",
    )
    parser.add_argument("--from-state", help="Source state")
    parser.add_argument("--to-state", help="Target state")
    parser.add_argument("--evidence-pack-dir", help="Evidence pack directory")
    parser.add_argument("--startup-proof-path", help="Startup proof JSON path")
    parser.add_argument("--required-reads", help="NEXT_AGENT_REQUIRED_READS.json path")
    parser.add_argument("--decision-record-path", help="Human decision record JSON path (for T10)")
    parser.add_argument("--strict", action="store_true", default=False)

    args = parser.parse_args()

    if args.action == "list-states":
        print(json.dumps(
            {name: {"is_initial": s["is_initial"], "is_final": s["is_final"]}
             for name, s in STATES.items()},
            indent=2,
        ))
        sys.exit(0)

    if args.action == "list-transitions":
        print(json.dumps(
            [{"from": f, "to": t} for f, t in sorted(VALID_TRANSITIONS)],
            indent=2,
        ))
        sys.exit(0)

    if not args.from_state or not args.to_state:
        print("ERROR: --from-state and --to-state required for check-transition")
        sys.exit(1)

    result = check_transition(
        from_state=args.from_state,
        to_state=args.to_state,
        evidence_pack_dir=args.evidence_pack_dir,
        startup_proof_path=args.startup_proof_path,
        required_reads_path=args.required_reads,
        decision_record_path=args.decision_record_path,
        strict=args.strict,
    )

    print(json.dumps(result, indent=2, ensure_ascii=False))
    if result["transition_allowed"]:
        print(f"\nTRANSITION OK: {result['transition']}")
        sys.exit(0)
    else:
        print(f"\nTRANSITION BLOCKED: {result['transition']}")
        for e in result.get("errors", []):
            print(f"  ERROR: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
