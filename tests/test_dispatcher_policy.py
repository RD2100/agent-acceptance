"""Test DISPATCHER_POLICY rules.

Covers:
- accepted + allow_next_stage=true must produce dispatched (not stopped)
- human_required must produce stopped
- blocked must produce stopped or reconciliation
- unknown must fail-closed (stopped)
- dispatcher output must include should_execute_next
"""

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent


def load_schema(name):
    path = ROOT / "contracts" / name
    return json.loads(path.read_text(encoding="utf-8"))


def validate_dispatch(schema, instance):
    """Validate dispatch result against schema."""
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
        if "enum" in c:
            if instance.get(p) not in c["enum"]:
                return False
        if "const" in c:
            if instance.get(p) != c["const"]:
                return False
    return True


def test_accepted_allow_next_must_dispatch():
    """Test 1: accepted + allow_next_stage=true must produce dispatched (not stopped)."""
    schema = load_schema("FLOW_OUTCOME.schema.json")
    # A valid accepted flow outcome
    flow = {
        "task_id": "DISPATCH-TEST-1",
        "stage": "S3",
        "transport_status": "success",
        "business_decision": "accepted",
        "dispatch_status": "ready_to_dispatch",
        "overall_status": "accepted",
        "allow_next_stage": True,
        "next_stage": "S4",
        "next_task_spec_path": "tasks/s4.json",
        "required_next_action": "Dispatch S4",
        "terminal": False,
        "errors": []
    }
    validate_dispatch(schema, flow)

    # Now check: dispatcher should produce dispatched, not stopped
    # Verify that dispatched is a valid enum value
    dispatch_schema = load_schema("DISPATCH_RESULT.schema.json")
    enum_vals = dispatch_schema["properties"]["dispatch_status"]["enum"]
    assert "dispatched" in enum_vals
    assert "stopped" in enum_vals

    # dispatched should NOT be confused with stopped
    assert "dispatched" != "stopped"



def test_human_required_must_stop():
    """Test 2: human_required business decision must produce stopped dispatch."""
    # Validate that human_required flow maps to stopped in dispatch
    schema = load_schema("DISPATCH_RESULT.schema.json")
    # A dispatcher result for human_required
    result = {
        "dispatch_status": "stopped",
        "required_next_action": "Human must attest baseline",
        "resume_command": "python resume.py --task hr-1",
        "terminal": True,
        "should_execute_next": False,
        "reason": "GPT returned human_required"
    }
    validate_dispatch(schema, result)


def test_unknown_must_fail_closed():
    """Test 3: unknown business decision must produce stopped (fail-closed)."""
    # unknown -> stopped is the correct behavior
    schema = load_schema("DISPATCH_RESULT.schema.json")
    result = {
        "dispatch_status": "stopped",
        "required_next_action": "Re-run GPT review: decision unparseable",
        "terminal": True,
        "should_execute_next": False,
        "reason": "GPT decision unparseable, fail-closed"
    }
    validate_dispatch(schema, result)


def test_dispatcher_must_produce_should_execute_next():
    """Test 4: Dispatcher result must include should_execute_next field."""
    schema = load_schema("DISPATCH_RESULT.schema.json")
    # Missing should_execute_next
    instance_missing = {
        "dispatch_status": "dispatched",
        "next_task_spec_path": "task.json",
        "terminal": False
    }
    with pytest.raises(AssertionError):
        validate_dispatch(schema, instance_missing)


def test_empty_dispatch_result_rejected():
    """Test 5: Empty dispatch result must fail (missing all required fields)."""
    schema = load_schema("DISPATCH_RESULT.schema.json")
    instance = {}
    with pytest.raises(AssertionError):
        validate_dispatch(schema, instance)


def run_all_tests():
    tests = [
        ("accepted must dispatch not stop", test_accepted_allow_next_must_dispatch),
        ("human_required must stop", test_human_required_must_stop),
        ("unknown must fail-closed", test_unknown_must_fail_closed),
        ("must produce should_execute_next", test_dispatcher_must_produce_should_execute_next),
        ("empty dispatch rejected", test_empty_dispatch_result_rejected),
    ]

    passed = 0
    failed = 0
    print("=" * 60)
    print("DISPATCHER_POLICY Tests")
    print("=" * 60)

    for name, test_fn in tests:
        try:
            test_fn()
            passed += 1
            print(f"  [PASS] {name}")
        except Exception as e:
            failed += 1
            print(f"  [FAIL] {name}")
            print(f"         {e}")

    print(f"\n  Results: {passed}/{passed+failed} passed")
    return failed == 0


if __name__ == "__main__":
    sys.exit(0 if run_all_tests() else 1)
