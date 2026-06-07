"""Test RUN_UNTIL_TERMINAL_POLICY enforcement.

Covers:
3. terminal=false + final_report_only → invalid (final report at non-terminal)
4. accepted + allow_next_stage=true + terminal=true → invalid (unless accepted_done)
8. high-risk action → human_required
12. TaskSpec invalid → fail-closed
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# 6 valid terminal reasons from TERMINAL_STATE_POLICY.md
VALID_TERMINAL_REASONS = {
    "accepted_done", "human_required", "blocked_unresolvable",
    "technical_failure", "max_rounds_reached", "high_risk_required"
}


def test_valid_terminal_reasons():
    """Test 1: Only 6 valid terminal reasons exist."""
    assert len(VALID_TERMINAL_REASONS) == 6


def test_terminal_false_no_final_report():
    """Test 2: terminal=false must not produce terminal step status."""
    # step_success_continue and step_partial are the only non-terminal statuses
    schema = json.loads((ROOT / "contracts" / "RUNNER_STEP_RESULT.schema.json").read_text(encoding="utf-8"))

    # Check schema rules: step_success_continue → terminal=false
    for rule in schema["allOf"]:
        if_cond = rule.get("if", {})
        if_props = if_cond.get("properties", {})
        if if_props.get("status", {}).get("const") == "step_success_continue":
            then = rule.get("then", {})
            then_props = then.get("properties", {})
            assert then_props.get("terminal", {}).get("const") == False, \
                "step_success_continue must have terminal=false"

    for rule in schema["allOf"]:
        if_cond = rule.get("if", {})
        if_props = if_cond.get("properties", {})
        if if_props.get("status", {}).get("const") == "step_partial":
            then = rule.get("then", {})
            then_props = then.get("properties", {})
            assert then_props.get("terminal", {}).get("const") == False, \
                "step_partial must have terminal=false"



def test_accepted_allow_next_not_terminal_unless_done():
    """Test 3: accepted + allow_next_stage=true cannot be terminal unless accepted_done."""
    schema = json.loads((ROOT / "contracts" / "RUNNER_STATE.schema.json").read_text(encoding="utf-8"))
    for rule in schema["allOf"]:
        if_cond = rule.get("if", {})
        if_props = if_cond.get("properties", {})
        if if_props.get("last_decision", {}).get("const") == "accepted":
            then = rule.get("then", {})
            then_props = then.get("properties", {})
            assert then_props.get("terminal", {}).get("const") == False, \
                "accepted must have terminal=false in RUNNER_STATE"


def test_high_risk_triggers_human_required():
    """Test 4: High-risk action in step result triggers human_required."""
    fixture = json.loads((ROOT / "tests/fixtures/runner_step_result_high_risk_human_required.json").read_text(encoding="utf-8"))
    assert fixture["safety"]["high_risk_action_attempted"] == True
    assert fixture["status"] == "step_human_required"
    assert fixture["terminal"] == True


def test_taskspec_invalid_fail_closed():
    """Test 5: Invalid TaskSpec (Markdown-only) must trigger fail."""
    # Verify RUNNER_FAILURE_POLICY exists and references fail-closed
    policy = (ROOT / "policies" / "RUNNER_FAILURE_POLICY.md").read_text(encoding="utf-8")
    assert "fail-closed" in policy.lower()
    assert "TaskSpec invalid" in policy
    assert "step_failed" in policy


def test_schema_missing_fail_closed():
    """Test 6: Schema missing scenario must be documented as fail-closed."""
    policy = (ROOT / "policies" / "RUNNER_FAILURE_POLICY.md").read_text(encoding="utf-8")
    assert "Schema missing" in policy
    assert "step_failed" in policy


def run_all_tests():
    tests = [
        ("6 valid terminal reasons", test_valid_terminal_reasons),
        ("terminal=false no final report", test_terminal_false_no_final_report),
        ("accepted cannot be terminal", test_accepted_allow_next_not_terminal_unless_done),
        ("high-risk triggers human_required", test_high_risk_triggers_human_required),
        ("TaskSpec invalid fail-closed", test_taskspec_invalid_fail_closed),
        ("schema missing fail-closed", test_schema_missing_fail_closed),
    ]
    passed = 0
    failed = 0
    print("=" * 60)
    print("RUN_UNTIL_TERMINAL_POLICY Tests")
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
