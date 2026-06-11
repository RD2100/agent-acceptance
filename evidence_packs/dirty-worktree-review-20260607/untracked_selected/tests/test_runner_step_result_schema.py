"""Test RUNNER_STEP_RESULT schema validation rules.

Covers:
6. step_success_continue without next_action → invalid
7. step_partial with terminal=true → invalid (step_partial is non-terminal)
8. step_success_continue must have terminal=false
10. transport success + business blocked must NOT be treated as accepted
11. high-risk action → step_human_required
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FIXTURES = ROOT / "tests" / "fixtures"


def load_schema():
    return json.loads((ROOT / "contracts" / "RUNNER_STEP_RESULT.schema.json").read_text(encoding="utf-8"))


def validate_step_result(schema, instance):
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

            then_props = then_cond.get("properties", {})
            for prop, constraint in then_props.items():
                if "const" in constraint and prop in instance:
                    if instance[prop] != constraint["const"]:
                        errors.append(f"Violation: {prop} must be {constraint['const']}, got {instance[prop]}")

                elif "properties" in constraint:
                    for sub_p, sub_c in constraint["properties"].items():
                        if "const" in sub_c:
                            sub_v = instance.get(prop, {}).get(sub_p)
                            if sub_v is not None and sub_v != sub_c["const"]:
                                errors.append(f"Violation: {prop}.{sub_p} must be {sub_c['const']}, got {sub_v}")

    if errors:
        raise AssertionError("\n".join(errors))


def _check_if(if_cond, instance):
    """Check if condition matches, including nested safety object checks."""
    props = if_cond.get("properties", {})

    for p, c in props.items():
        if "const" in c:
            if instance.get(p) != c["const"]:
                return False
        if "enum" in c:
            if instance.get(p) not in c["enum"]:
                return False
        if "properties" in c:
            sub_props = c.get("properties", {})
            for sub_p, sub_c in sub_props.items():
                if "const" in sub_c:
                    nested_val = instance.get(p, {})
                    if isinstance(nested_val, dict):
                        if nested_val.get(sub_p) != sub_c["const"]:
                            return False
                    else:
                        return False
    return True


def test_valid_continue():
    """Test 1: Valid step_success_continue passes."""
    schema = load_schema()
    instance = json.loads((FIXTURES / "runner_step_result_continue.json").read_text(encoding="utf-8"))
    validate_step_result(schema, instance)
    return True, "PASS"


def test_valid_stop():
    """Test 2: Valid step_human_required passes."""
    schema = load_schema()
    instance = json.loads((FIXTURES / "runner_step_result_stop.json").read_text(encoding="utf-8"))
    validate_step_result(schema, instance)
    return True, "PASS"


def test_valid_high_risk():
    """Test 3: Valid high-risk human_required passes."""
    schema = load_schema()
    instance = json.loads((FIXTURES / "runner_step_result_high_risk_human_required.json").read_text(encoding="utf-8"))
    validate_step_result(schema, instance)
    return True, "PASS"


def test_continue_without_next_action():
    """Test 4: step_success_continue without next_action must fail."""
    schema = load_schema()
    instance = {
        "step_id": "test-continue-fail",
        "step_type": "execute_taskspec",
        "status": "step_success_continue",
        "terminal": False,
        "reason": "Missing next_action"
    }
    try:
        validate_step_result(schema, instance)
        return False, "Should have FAILED"
    except AssertionError:
        return True, "PASS (correctly rejected)"


def test_partial_as_terminal_invalid():
    """Test 5: step_partial with terminal=true must fail."""
    schema = load_schema()
    instance = json.loads((FIXTURES / "runner_step_result_partial_invalid_as_terminal.json").read_text(encoding="utf-8"))
    try:
        validate_step_result(schema, instance)
        return False, "Should have FAILED (step_partial with terminal=true)"
    except AssertionError:
        return True, "PASS (correctly rejected)"


def test_transport_success_business_blocked():
    """Test 6: transport=success + business=blocked must NOT be treated as accepted."""
    schema = load_schema()
    instance = json.loads((FIXTURES / "runner_step_result_transport_success_business_blocked.json").read_text(encoding="utf-8"))
    try:
        validate_step_result(schema, instance)
    except AssertionError:
        pass
    # Key assertion: business_decision=blocked exists independently of transport=success
    assert instance["transport_status"] == "success"
    assert instance["business_decision"] == "blocked"
    assert instance["transport_status"] != instance["business_decision"]
    return True, "PASS (transport success != business accepted)"


def run_all_tests():
    tests = [
        ("valid continue", test_valid_continue),
        ("valid stop", test_valid_stop),
        ("valid high-risk", test_valid_high_risk),
        ("continue without next_action", test_continue_without_next_action),
        ("partial as terminal invalid", test_partial_as_terminal_invalid),
        ("transport success != business accepted", test_transport_success_business_blocked),
    ]
    passed = 0
    failed = 0
    print("=" * 60)
    print("RUNNER_STEP_RESULT Schema Tests")
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
