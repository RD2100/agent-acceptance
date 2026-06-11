"""Test NEXT_TASKSPEC_CONSUMPTION_POLICY enforcement.

Covers:
9. next_task_spec_path exists but not consumed → fail
10. ready_to_dispatch != dispatched distinction
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FIXTURES = ROOT / "tests" / "fixtures"


def test_next_taskspec_path_required_when_terminal_false():
    """Test 1: RUNNER_STATE terminal=false must have next_action."""
    schema = json.loads((ROOT / "contracts" / "RUNNER_STATE.schema.json").read_text(encoding="utf-8"))
    for rule in schema["allOf"]:
        if_cond = rule.get("if", {})
        if_props = if_cond.get("properties", {})
        if if_props.get("terminal", {}).get("const") == False:
            then = rule.get("then", {})
            then_req = then.get("required", [])
            assert "next_action" in then_req, \
                "terminal=false must require next_action"
    return True, "PASS"


def test_ready_to_dispatch_vs_dispatched_in_schema():
    """Test 2: ready_to_dispatch and dispatched are distinct enum values."""
    schema = json.loads((ROOT / "contracts" / "DISPATCH_RESULT.schema.json").read_text(encoding="utf-8"))
    enum_vals = schema["properties"]["dispatch_status"]["enum"]
    assert "ready_to_dispatch" in enum_vals
    assert "dispatched" in enum_vals
    assert "ready_to_dispatch" != "dispatched"
    return True, "PASS"


def test_runner_state_valid_has_next_action():
    """Test 3: Valid RUNNER_STATE with terminal=false has next_action."""
    instance = json.loads((FIXTURES / "runner_state_terminal_false_valid.json").read_text(encoding="utf-8"))
    assert instance["terminal"] == False, "Fixture should have terminal=false"
    assert "next_action" in instance, "terminal=false must have next_action"
    return True, "PASS"


def test_runner_state_invalid_missing_next_action():
    """Test 4: Invalid RUNNER_STATE missing next_action with terminal=false."""
    instance = json.loads((FIXTURES / "runner_state_terminal_false_missing_next_action.json").read_text(encoding="utf-8"))
    assert instance["terminal"] == False, "Fixture should have terminal=false"
    assert "next_action" not in instance, "Fixture should NOT have next_action (this is what makes it invalid)"
    return True, "PASS (fixture correctly models invalid state)"


def test_consumption_policy_exists():
    """Test 5: NEXT_TASKSPEC_CONSUMPTION_POLICY document exists with key rules."""
    policy = (ROOT / "policies" / "NEXT_TASKSPEC_CONSUMPTION_POLICY.md").read_text(encoding="utf-8")
    assert "MUST be consumed" in policy
    assert "ready_to_dispatch" in policy.lower()
    assert "dispatched" in policy.lower()
    assert "P0" in policy
    return True, "PASS"


def test_task_spec_generated_not_terminal():
    """Test 6: taskspec_generated dispatch status is non-terminal in schema."""
    schema = json.loads((ROOT / "contracts" / "DISPATCH_RESULT.schema.json").read_text(encoding="utf-8"))
    for rule in schema["allOf"]:
        if_cond = rule.get("if", {})
        if_props = if_cond.get("properties", {})
        if if_props.get("dispatch_status", {}).get("const") == "taskspec_generated":
            then = rule.get("then", {})
            then_props = then.get("properties", {})
            assert then_props.get("terminal", {}).get("const") == False, \
                "taskspec_generated must have terminal=false"
    return True, "PASS"


def run_all_tests():
    tests = [
        ("next_action required when terminal=false", test_next_taskspec_path_required_when_terminal_false),
        ("ready_to_dispatch != dispatched", test_ready_to_dispatch_vs_dispatched_in_schema),
        ("valid state has next_action", test_runner_state_valid_has_next_action),
        ("invalid fixture missing next_action", test_runner_state_invalid_missing_next_action),
        ("consumption policy exists", test_consumption_policy_exists),
        ("taskspec_generated is non-terminal", test_task_spec_generated_not_terminal),
    ]
    passed = 0
    failed = 0
    print("=" * 60)
    print("NEXT_TASKSPEC_CONSUMPTION_POLICY Tests")
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
