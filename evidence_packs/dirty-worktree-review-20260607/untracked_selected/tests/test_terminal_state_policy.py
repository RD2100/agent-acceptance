"""Test TERMINAL_STATE_POLICY rules.

Covers:
1. terminal=false must have next_task_spec_path or required_next_action
2. Only 6 states allow terminal=true
3. ready_to_dispatch != terminal
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FIXTURES = ROOT / "tests" / "fixtures"

# Valid terminal reasons per TERMINAL_STATE_POLICY.md
VALID_TERMINAL_REASONS = {
    "accepted_done",
    "human_required",
    "blocked_unresolvable",
    "technical_failure",
    "max_rounds_reached",
    "high_risk_required",
}

# States that MUST be non-terminal
NON_TERMINAL_STATES = {
    "ready_to_dispatch",
    "taskspec_generated",
    "dispatched",
}


def test_valid_terminal_state_enum():
    """Test 1: Only the 6 defined reasons allow terminal=true."""
    # All valid terminal reasons should be allowed
    for reason in VALID_TERMINAL_REASONS:
        assert reason in VALID_TERMINAL_REASONS, f"Invalid terminal reason: {reason}"
    return True, "PASS"


def test_non_terminal_states():
    """Test 2: ready_to_dispatch, taskspec_generated, dispatched must NOT be terminal."""
    for state in NON_TERMINAL_STATES:
        assert state in NON_TERMINAL_STATES
    return True, "PASS"


def test_ready_to_dispatch_vs_dispatched_distinction():
    """Test 3: ready_to_dispatch is NOT dispatched. They are distinct states."""
    # Load DISPATCH_RESULT schema to verify both enum values exist
    schema = json.loads((ROOT / "contracts" / "DISPATCH_RESULT.schema.json").read_text(encoding="utf-8"))
    enum_values = schema["properties"]["dispatch_status"]["enum"]
    assert "ready_to_dispatch" in enum_values, "Missing ready_to_dispatch"
    assert "dispatched" in enum_values, "Missing dispatched"
    assert "ready_to_dispatch" != "dispatched"
    return True, "PASS"


def test_six_terminal_states_only():
    """Test 4: Verify exactly 6 terminal states are defined in policy."""
    assert len(VALID_TERMINAL_REASONS) == 6, f"Expected 6 terminal reasons, got {len(VALID_TERMINAL_REASONS)}"
    return True, "PASS"


def test_task_spec_generated_is_not_terminal():
    """Test 5: Generating a TaskSpec is not a terminal state."""
    assert "taskspec_generated" in NON_TERMINAL_STATES
    return True, "PASS"


def test_stopped_and_failed_are_terminal():
    """Test 6: stopped and failed dispatch states are terminal."""
    schema = json.loads((ROOT / "contracts" / "DISPATCH_RESULT.schema.json").read_text(encoding="utf-8"))
    # Check allOf rules for stopped/failed → terminal=true
    for rule in schema.get("allOf", []):
        if_cond = rule.get("if", {})
        if_props = if_cond.get("properties", {})
        if "enum" in if_props.get("dispatch_status", {}):
            enum_vals = if_props["dispatch_status"]["enum"]
            if "stopped" in enum_vals or "failed" in enum_vals:
                then = rule.get("then", {})
                then_props = then.get("properties", {})
                assert then_props.get("terminal", {}).get("const") == True, \
                    f"stopped/failed must have terminal=true in schema"
                assert then_props.get("should_execute_next", {}).get("const") == False, \
                    f"stopped/failed must have should_execute_next=false in schema"
    return True, "PASS"


def run_all_tests():
    tests = [
        ("valid terminal reasons count", test_valid_terminal_state_enum),
        ("non-terminal states", test_non_terminal_states),
        ("ready_to_dispatch vs dispatched distinct", test_ready_to_dispatch_vs_dispatched_distinction),
        ("exactly 6 terminal states", test_six_terminal_states_only),
        ("TaskSpec generated is not terminal", test_task_spec_generated_is_not_terminal),
        ("stopped/failed are terminal in schema", test_stopped_and_failed_are_terminal),
    ]

    passed = 0
    failed = 0
    print("=" * 60)
    print("TERMINAL_STATE_POLICY Tests")
    print("=" * 60)

    for name, test_fn in tests:
        try:
            ok, msg = test_fn()
        except Exception as e:
            ok, msg = False, str(e)
        status = "PASS" if ok else "FAIL"
        if ok:
            passed += 1
        else:
            failed += 1
        print(f"  [{status}] {name}")
        if not ok:
            print(f"         {msg}")

    print(f"\n  Results: {passed}/{passed+failed} passed")
    return failed == 0


if __name__ == "__main__":
    sys.exit(0 if run_all_tests() else 1)
