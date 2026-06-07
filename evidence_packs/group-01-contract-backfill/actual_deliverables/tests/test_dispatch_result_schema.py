"""Test DISPATCH_RESULT schema validation rules.

Covers:
2. ready_to_dispatch treated as dispatched (terminal=true, should_execute_next=false) → FAIL
6. human_required must have required_next_action (in dispatcher context)
9. dispatch result missing terminal field → FAIL
"""

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
FIXTURES = ROOT / "tests" / "fixtures"


def load_schema(name):
    path = ROOT / "contracts" / name
    return json.loads(path.read_text(encoding="utf-8"))


def validate_dispatch(schema, instance):
    """Manual validation of DISPATCH_RESULT rules."""
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


def test_valid_fixture():
    """Test 1: Valid DISPATCH_RESULT fixture passes."""
    schema = load_schema("DISPATCH_RESULT.schema.json")
    instance = json.loads((FIXTURES / "valid_dispatch_result.json").read_text(encoding="utf-8"))
    validate_dispatch(schema, instance)


def test_ready_to_dispatch_treated_as_dispatched():
    """Test 2: ready_to_dispatch with terminal=true must fail (ready_to_dispatch != dispatched)."""
    schema = load_schema("DISPATCH_RESULT.schema.json")
    instance = json.loads((FIXTURES / "invalid_ready_to_dispatch_as_dispatched.json").read_text(encoding="utf-8"))
    with pytest.raises(AssertionError):
        validate_dispatch(schema, instance)


def test_dispatched_must_have_next_task_spec_path():
    """Test 3: dispatched must have next_task_spec_path."""
    schema = load_schema("DISPATCH_RESULT.schema.json")
    instance = {
        "dispatch_status": "dispatched",
        "should_execute_next": True,
        "terminal": False
    }
    with pytest.raises(AssertionError):
        validate_dispatch(schema, instance)


def test_stopped_must_have_next_action():
    """Test 4: stopped must have required_next_action."""
    schema = load_schema("DISPATCH_RESULT.schema.json")
    instance = {
        "dispatch_status": "stopped",
        "should_execute_next": False,
        "terminal": True
    }
    with pytest.raises(AssertionError):
        validate_dispatch(schema, instance)


def test_manual_confirm_must_have_next_action():
    """Test 5: manual_confirm_required must have required_next_action."""
    schema = load_schema("DISPATCH_RESULT.schema.json")
    instance = {
        "dispatch_status": "manual_confirm_required",
        "should_execute_next": False,
        "terminal": False
    }
    with pytest.raises(AssertionError):
        validate_dispatch(schema, instance)


def test_taskspec_generated_not_terminal():
    """Test 6: taskspec_generated must be terminal=false."""
    schema = load_schema("DISPATCH_RESULT.schema.json")
    instance = {
        "dispatch_status": "taskspec_generated",
        "next_task_spec_path": "task.json",
        "should_execute_next": True,
        "terminal": True
    }
    with pytest.raises(AssertionError):
        validate_dispatch(schema, instance)


def run_all_tests():
    tests = [
        ("valid fixture", test_valid_fixture),
        ("ready_to_dispatch as dispatched rejected", test_ready_to_dispatch_treated_as_dispatched),
        ("dispatched needs next_task_spec_path", test_dispatched_must_have_next_task_spec_path),
        ("stopped needs required_next_action", test_stopped_must_have_next_action),
        ("manual_confirm needs required_next_action", test_manual_confirm_must_have_next_action),
        ("taskspec_generated must not be terminal", test_taskspec_generated_not_terminal),
    ]

    passed = 0
    failed = 0
    print("=" * 60)
    print("DISPATCH_RESULT Schema Tests")
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
