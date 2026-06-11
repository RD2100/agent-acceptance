"""Test RUNNER_STATE schema validation rules.

Covers:
1. terminal=false + no next_action → invalid
2. human_required + terminal=true without resume_command → invalid
3. accepted + terminal=true → invalid (accepted means continue)
4. Valid terminal=false fixture passes
5. Valid human_required fixture passes
6. Recoverable failure state passes
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FIXTURES = ROOT / "tests" / "fixtures"


def load_schema():
    return json.loads((ROOT / "contracts" / "RUNNER_STATE.schema.json").read_text(encoding="utf-8"))


def validate_runner_state(schema, instance):
    errors = []
    required = schema.get("required", [])
    for r in required:
        if r not in instance:
            errors.append(f"Missing required field: {r}")

    all_of = schema.get("allOf", [])
    for rule in all_of:
        if_cond = rule.get("if", {})
        then_cond = rule.get("then", {})

        if _check_if(if_cond, instance):
            then_req = then_cond.get("required", [])
            for r in then_req:
                if r not in instance:
                    errors.append(f"Violation: missing '{r}' when {if_cond}")

            then_props = then_cond.get("properties", {})
            for prop, constraint in then_props.items():
                if "const" in constraint and prop in instance:
                    if instance[prop] != constraint["const"]:
                        errors.append(f"Violation: {prop} must be {constraint['const']}, got {instance[prop]}")

    if errors:
        raise AssertionError("\n".join(errors))


def _check_if(if_cond, instance):
    props = if_cond.get("properties", {})
    for p, c in props.items():
        if "const" in c and instance.get(p) != c["const"]:
            return False
    all_of = if_cond.get("allOf", [])
    for sub in all_of:
        sub_props = sub.get("properties", {})
        for p, c in sub_props.items():
            if "const" in c and instance.get(p) != c["const"]:
                return False
    return True


def test_valid_terminal_false():
    """Test 1: Valid terminal=false fixture passes."""
    schema = load_schema()
    instance = json.loads((FIXTURES / "runner_state_terminal_false_valid.json").read_text(encoding="utf-8"))
    validate_runner_state(schema, instance)
    return True, "PASS"


def test_terminal_false_no_next_action():
    """Test 2: terminal=false without next_action must fail."""
    schema = load_schema()
    instance = json.loads((FIXTURES / "runner_state_terminal_false_missing_next_action.json").read_text(encoding="utf-8"))
    try:
        validate_runner_state(schema, instance)
        return False, "Should have FAILED"
    except AssertionError:
        return True, "PASS (correctly rejected)"


def test_human_required_with_resume():
    """Test 3: human_required + terminal=true with resume_command passes."""
    schema = load_schema()
    instance = json.loads((FIXTURES / "runner_state_terminal_true_human_required.json").read_text(encoding="utf-8"))
    validate_runner_state(schema, instance)
    return True, "PASS"


def test_human_required_without_resume():
    """Test 4: human_required + terminal=true without resume_command must fail."""
    schema = load_schema()
    instance = {
        "runner_id": "test-hr-fail",
        "task_id": "TEST-HR-FAIL",
        "current_step": 1,
        "current_round": 0,
        "terminal": True,
        "last_decision": "human_required",
        "heartbeat": "2026-06-02T07:00:00Z",
        "reason": "Missing resume_command"
    }
    try:
        validate_runner_state(schema, instance)
        return False, "Should have FAILED (human_required without resume_command)"
    except AssertionError:
        return True, "PASS (correctly rejected)"


def test_accepted_cannot_be_terminal():
    """Test 5: accepted + terminal=true must fail (accepted means continue)."""
    schema = load_schema()
    instance = {
        "runner_id": "test-accepted-fail",
        "task_id": "TEST-ACCEPT-FAIL",
        "current_step": 3,
        "current_round": 1,
        "terminal": True,
        "last_decision": "accepted",
        "next_action": "Continue",
        "heartbeat": "2026-06-02T07:00:00Z",
        "reason": "Accepted but set terminal=true"
    }
    try:
        validate_runner_state(schema, instance)
        return False, "Should have FAILED (accepted with terminal=true)"
    except AssertionError:
        return True, "PASS (correctly rejected)"


def test_recoverable_failure_state():
    """Test 6: Recoverable failure state with retries and resume_command passes."""
    schema = load_schema()
    instance = json.loads((FIXTURES / "runner_state_recoverable_failure.json").read_text(encoding="utf-8"))
    validate_runner_state(schema, instance)
    return True, "PASS"


def run_all_tests():
    tests = [
        ("valid terminal=false", test_valid_terminal_false),
        ("terminal=false missing next_action", test_terminal_false_no_next_action),
        ("human_required with resume", test_human_required_with_resume),
        ("human_required without resume", test_human_required_without_resume),
        ("accepted cannot be terminal", test_accepted_cannot_be_terminal),
        ("recoverable failure state", test_recoverable_failure_state),
    ]
    passed = 0
    failed = 0
    print("=" * 60)
    print("RUNNER_STATE Schema Tests")
    print("=" * 60)
    for name, test_fn in tests:
        try:
            ok, msg = test_fn()
        except Exception as e:
            ok, msg = False, str(e)
        status = "PASS" if ok else "FAIL"
        if ok: passed += 1
        else: failed += 1
        print(f"  [{status}] {name}")
        if not ok: print(f"         {msg}")
    print(f"\n  Results: {passed}/{passed+failed} passed")
    return failed == 0


if __name__ == "__main__":
    sys.exit(0 if run_all_tests() else 1)
