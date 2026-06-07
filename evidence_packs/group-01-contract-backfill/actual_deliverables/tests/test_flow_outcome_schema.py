"""Test FLOW_OUTCOME schema validation rules.

Covers:
1. terminal=false + no next_task_spec_path or required_next_action → FAIL
2. accepted + allow_next_stage=true + no next_stage or next_task_spec_path → FAIL
3. human_required must have terminal=true and allow_next_stage=false
4. blocked must have required_next_action
5. valid fixture must pass
"""

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
FIXTURES = ROOT / "tests" / "fixtures"

try:
    import jsonschema
    HAVE_JSONSCHEMA = True
except ImportError:
    HAVE_JSONSCHEMA = False


def load_schema(name):
    path = ROOT / "contracts" / name
    return json.loads(path.read_text(encoding="utf-8"))


def validate(schema, instance):
    if HAVE_JSONSCHEMA:
        jsonschema.validate(instance, schema)
    else:
        # Manual validation fallback
        _manual_validate(schema, instance)


def _manual_validate(schema, instance):
    """Manual validation of key schema rules when jsonschema not installed."""
    errors = []
    props = schema.get("properties", {})

    # Check required fields
    required = schema.get("required", [])
    for r in required:
        if r not in instance:
            errors.append(f"Missing required field: {r}")

    # Check allOf rules
    for rule in schema.get("allOf", []):
        if_cond = rule.get("if", {})
        then_cond = rule.get("then", {})

        # Check if condition matches
        if _matches_if(if_cond, instance):
            # Check then requirements
            then_req = then_cond.get("required", [])
            for r in then_req:
                if r not in instance:
                    errors.append(f"Rule violation: missing '{r}' (required by conditional)")

            # Check property constraints in then
            then_props = then_cond.get("properties", {})
            for prop, constraint in then_props.items():
                if prop in instance and "const" in constraint:
                    if instance[prop] != constraint["const"]:
                        errors.append(f"Rule violation: {prop} must be {constraint['const']}, got {instance[prop]}")

            # Check anyOf in then
            any_of = then_cond.get("anyOf", [])
            if any_of:
                satisfied = False
                for option in any_of:
                    opt_req = option.get("required", [])
                    if all(r in instance for r in opt_req):
                        satisfied = True
                        break
                if not satisfied:
                    reqs = [o.get("required", []) for o in any_of]
                    errors.append(f"Rule violation: must satisfy one of {reqs}")

    if errors:
        raise AssertionError("\n".join(errors))


def _matches_if(if_cond, instance):
    """Check if an if-condition matches the instance."""
    if_props = if_cond.get("properties", {})
    for prop, constraint in if_props.items():
        if "const" in constraint:
            if instance.get(prop) != constraint["const"]:
                return False
    all_of = if_cond.get("allOf", [])
    for sub in all_of:
        sub_props = sub.get("properties", {})
        for prop, constraint in sub_props.items():
            if "const" in constraint:
                if instance.get(prop) != constraint["const"]:
                    return False
    return True


def test_valid_fixture():
    """Test 1: Valid FLOW_OUTCOME fixture validates successfully."""
    schema = load_schema("FLOW_OUTCOME.schema.json")
    instance = json.loads((FIXTURES / "valid_flow_outcome.json").read_text(encoding="utf-8"))
    validate(schema, instance)


def test_terminal_false_no_next_action():
    """Test 2: terminal=false without next_task_spec_path or required_next_action."""
    schema = load_schema("FLOW_OUTCOME.schema.json")
    instance = json.loads((FIXTURES / "invalid_terminal_false_no_next_action.json").read_text(encoding="utf-8"))
    with pytest.raises((AssertionError, Exception)):
        validate(schema, instance)


def test_human_required_rules():
    """Test 3: business_decision=human_required must set terminal=true, allow_next_stage=false, and require next_action."""
    schema = load_schema("FLOW_OUTCOME.schema.json")
    instance = {
        "task_id": "TEST-HR",
        "stage": "S3",
        "transport_status": "success",
        "business_decision": "human_required",
        "dispatch_status": "stopped",
        "overall_status": "human_required",
        "allow_next_stage": False,
        "required_next_action": "Human must attest baseline",
        "terminal": True,
        "errors": []
    }
    validate(schema, instance)


def test_human_required_missing_next_action():
    """Test 4: human_required without required_next_action must fail."""
    schema = load_schema("FLOW_OUTCOME.schema.json")
    instance = {
        "task_id": "TEST-HR-FAIL",
        "stage": "S3",
        "transport_status": "success",
        "business_decision": "human_required",
        "dispatch_status": "stopped",
        "overall_status": "human_required",
        "allow_next_stage": False,
        "terminal": True,
        "errors": []
    }
    with pytest.raises((AssertionError, Exception)):
        validate(schema, instance)


def test_accepted_allow_next_no_next_stage():
    """Test 5: accepted + allow_next_stage=true without next_stage or next_task_spec_path must fail."""
    schema = load_schema("FLOW_OUTCOME.schema.json")
    instance = {
        "task_id": "TEST-MISSING",
        "stage": "S3",
        "transport_status": "success",
        "business_decision": "accepted",
        "dispatch_status": "ready_to_dispatch",
        "overall_status": "accepted",
        "allow_next_stage": True,
        "terminal": False,
        "errors": []
    }
    with pytest.raises((AssertionError, Exception)):
        validate(schema, instance)


def test_blocked_must_have_next_action():
    """Test 6: blocked must have required_next_action."""
    schema = load_schema("FLOW_OUTCOME.schema.json")
    # Valid: blocked with next action
    instance_valid = {
        "task_id": "TEST-BLOCKED",
        "stage": "S3",
        "transport_status": "success",
        "business_decision": "blocked",
        "dispatch_status": "stopped",
        "overall_status": "blocked",
        "allow_next_stage": False,
        "required_next_action": "Reconciliation required",
        "terminal": True,
        "errors": ["Missing evidence"]
    }
    try:
        validate(schema, instance_valid)
        valid_ok = True
    except Exception as e:
        valid_ok = False

    # Invalid: blocked without next action
    instance_invalid = {
        "task_id": "TEST-BLOCKED-FAIL",
        "stage": "S3",
        "transport_status": "success",
        "business_decision": "blocked",
        "dispatch_status": "stopped",
        "overall_status": "blocked",
        "allow_next_stage": False,
        "terminal": True,
        "errors": []
    }
    with pytest.raises((AssertionError, Exception)):
        validate(schema, instance_invalid)
    assert valid_ok, "Valid blocked case also failed"


def test_transport_success_not_business_accepted():
    """Test 7: transport_status=success does not imply business_decision=accepted."""
    schema = load_schema("FLOW_OUTCOME.schema.json")
    instance = {
        "task_id": "TEST-TRANSPORT",
        "stage": "S3",
        "transport_status": "success",
        "business_decision": "human_required",
        "dispatch_status": "stopped",
        "overall_status": "human_required",
        "allow_next_stage": False,
        "required_next_action": "Human must verify",
        "terminal": True,
        "errors": []
    }
    validate(schema, instance)


def test_ready_to_dispatch_not_dispatched():
    """Test 8: dispatch_status=ready_to_dispatch with terminal=true must fail."""
    schema = load_schema("FLOW_OUTCOME.schema.json")
    instance = {
        "task_id": "TEST-RTD-AS-DONE",
        "stage": "S3",
        "transport_status": "success",
        "business_decision": "accepted",
        "dispatch_status": "ready_to_dispatch",
        "overall_status": "accepted",
        "allow_next_stage": True,
        "next_task_spec_path": "task.json",
        "terminal": True,
        "errors": []
    }
    with pytest.raises((AssertionError, Exception)):
        validate(schema, instance)


def run_all_tests():
    tests = [
        ("valid fixture", test_valid_fixture),
        ("terminal=false without next action", test_terminal_false_no_next_action),
        ("human_required rules", test_human_required_rules),
        ("human_required missing next_action", test_human_required_missing_next_action),
        ("accepted+allow_next without next stage", test_accepted_allow_next_no_next_stage),
        ("blocked must have next_action", test_blocked_must_have_next_action),
        ("transport success != business accepted", test_transport_success_not_business_accepted),
        ("ready_to_dispatch not dispatched (terminal)", test_ready_to_dispatch_not_dispatched),
    ]

    passed = 0
    failed = 0
    print("=" * 60)
    print("FLOW_OUTCOME Schema Tests")
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
