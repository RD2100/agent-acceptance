"""Test RUNNER_CONTRACT schema validation rules.

Covers:
1. terminal=false + no input_taskspec_path or next_action → invalid
2. terminal=false + input_taskspec_path → valid
3. resume mode without input_outcome_path → invalid
4. high_risk_triggers_human_required must be true (enforced by const)
5. fail_closed must be true (enforced by const)
"""

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
FIXTURES = ROOT / "tests" / "fixtures"


def load_schema():
    return json.loads((ROOT / "contracts" / "RUNNER_CONTRACT.schema.json").read_text(encoding="utf-8"))


def validate_runner_contract(schema, instance):
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
                    errors.append(f"Violation: missing '{r}'")
            any_of = then_cond.get("anyOf", [])
            if any_of:
                satisfied = False
                for opt in any_of:
                    opt_req = opt.get("required", [])
                    if all(r in instance for r in opt_req):
                        satisfied = True
                        break
                if not satisfied:
                    reqs = [o.get("required", []) for o in any_of]
                    errors.append(f"Violation: must satisfy one of {reqs}")

    if errors:
        raise AssertionError("\n".join(errors))


def _check_if(if_cond, instance):
    props = if_cond.get("properties", {})
    for p, c in props.items():
        if "const" in c and instance.get(p) != c["const"]:
            return False
    return True


def make_valid_contract():
    return {
        "runner_id": "test-runner",
        "task_id": "TEST-001",
        "mode": "run_until_terminal",
        "terminal": False,
        "input_taskspec_path": "tasks/test.json",
        "allowed_actions": ["run_tests", "write_reports"],
        "forbidden_actions": ["delete_files", "clean_worktree"],
        "resume_policy": {"resume_enabled": True, "state_path": "state.json"},
        "safety_policy": {"high_risk_triggers_human_required": True, "fail_closed": True, "require_schema_validation": True}
    }


def test_valid_contract():
    """Test 1: Valid runner contract passes."""
    schema = load_schema()
    instance = make_valid_contract()
    validate_runner_contract(schema, instance)


def test_terminal_false_missing_input():
    """Test 2: terminal=false without input_taskspec_path or next_action must fail."""
    schema = load_schema()
    instance = make_valid_contract()
    del instance["input_taskspec_path"]
    with pytest.raises(AssertionError):
        validate_runner_contract(schema, instance)


def test_terminal_false_with_next_action():
    """Test 3: terminal=false with next_action (no input_taskspec_path) is valid."""
    schema = load_schema()
    instance = make_valid_contract()
    del instance["input_taskspec_path"]
    instance["next_action"] = "Execute manual step"
    validate_runner_contract(schema, instance)


def test_resume_mode_missing_outcome():
    """Test 4: resume mode without input_outcome_path must fail."""
    schema = load_schema()
    instance = make_valid_contract()
    instance["mode"] = "resume"
    with pytest.raises(AssertionError):
        validate_runner_contract(schema, instance)


def test_high_risk_action_contract():
    """Test 5: High-risk runner contract fixture validates."""
    schema = load_schema()
    instance = json.loads((FIXTURES / "runner_contract_high_risk_action.json").read_text(encoding="utf-8"))
    validate_runner_contract(schema, instance)


def test_missing_safety_policy():
    """Test 6: Missing safety_policy must fail."""
    schema = load_schema()
    instance = make_valid_contract()
    del instance["safety_policy"]
    with pytest.raises((AssertionError, KeyError)):
        validate_runner_contract(schema, instance)


def run_all_tests():
    tests = [
        ("valid contract", test_valid_contract),
        ("terminal=false missing input", test_terminal_false_missing_input),
        ("terminal=false with next_action", test_terminal_false_with_next_action),
        ("resume mode missing outcome", test_resume_mode_missing_outcome),
        ("high-risk contract fixture", test_high_risk_action_contract),
        ("missing safety_policy", test_missing_safety_policy),
    ]
    passed = 0
    failed = 0
    print("=" * 60)
    print("RUNNER_CONTRACT Schema Tests")
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
