"""Test TASKSPEC schema validation rules.

Covers:
5. TaskSpec with only Markdown (missing required fields) → FAIL
6. high_risk=true must require human review
7. valid TaskSpec fixture must pass
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


def validate_strict(schema, instance):
    """Manual strict validation of TASKSPEC rules."""
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
            then_props = then_cond.get("properties", {})
            for prop, constraint in then_props.items():
                if "const" in constraint:
                    if instance.get(prop) != constraint["const"]:
                        val = instance.get(prop)
                        expected = constraint["const"]
                        errors.append(f"Violation: {prop} must be '{expected}', got '{val}'")

    if errors:
        raise AssertionError("\n".join(errors))


def _check_if(if_cond, instance):
    if_props = if_cond.get("properties", {})
    for prop, constraint in if_props.items():
        if "const" in constraint:
            if instance.get(prop) != constraint["const"]:
                return False
    return True


def test_valid_fixture():
    """Test 1: Valid TASKSPEC fixture passes."""
    schema = load_schema("TASKSPEC.schema.json")
    instance = json.loads((FIXTURES / "valid_taskspec.json").read_text(encoding="utf-8"))
    validate_strict(schema, instance)


def test_markdown_only_rejected():
    """Test 2: TaskSpec that is only Markdown (missing required JSON fields) must fail."""
    schema = load_schema("TASKSPEC.schema.json")
    instance = json.loads((FIXTURES / "invalid_markdown_only_taskspec.json").read_text(encoding="utf-8"))
    with pytest.raises(AssertionError):
        validate_strict(schema, instance)


def test_high_risk_must_require_human():
    """Test 3: high_risk=true must set review_by=human and terminal_conditions.terminal=true."""
    schema = load_schema("TASKSPEC.schema.json")
    instance = {
        "task_id": "TEST-HIGH-RISK",
        "stage": "S4",
        "goal": "Delete production data",
        "allowed_actions": ["delete_files"],
        "forbidden_actions": [],
        "required_outputs": ["report.md"],
        "terminal_conditions": {
            "terminal": True,
            "reason": "high_risk_required",
            "allowed_terminal_reasons": ["accepted_done", "human_required", "blocked_unresolvable", "technical_failure", "max_rounds_reached", "high_risk_required"]
        },
        "high_risk": True,
        "review_by": "human",
        "schema_version": "1.0.0"
    }
    validate_strict(schema, instance)


def test_high_risk_without_human_review():
    """Test 4: high_risk=true with review_by=gpt must fail."""
    schema = load_schema("TASKSPEC.schema.json")
    instance = {
        "task_id": "TEST-HIGH-RISK-FAIL",
        "stage": "S4",
        "goal": "Delete production data",
        "allowed_actions": ["delete_files"],
        "forbidden_actions": [],
        "required_outputs": ["report.md"],
        "terminal_conditions": {
            "terminal": True,
            "reason": "accepted_done",
            "allowed_terminal_reasons": ["accepted_done"]
        },
        "high_risk": True,
        "review_by": "gpt",
        "schema_version": "1.0.0"
    }
    with pytest.raises(AssertionError):
        validate_strict(schema, instance)


def test_missing_terminal_conditions():
    """Test 5: TaskSpec missing terminal_conditions must fail."""
    schema = load_schema("TASKSPEC.schema.json")
    instance = {
        "task_id": "TEST-NO-TERM",
        "stage": "S3",
        "goal": "Run tests",
        "allowed_actions": ["run_tests"],
        "forbidden_actions": [],
        "required_outputs": ["report.md"],
        "schema_version": "1.0.0"
    }
    with pytest.raises(AssertionError):
        validate_strict(schema, instance)


def run_all_tests():
    tests = [
        ("valid fixture", test_valid_fixture),
        ("Markdown-only rejected", test_markdown_only_rejected),
        ("high_risk requires human", test_high_risk_must_require_human),
        ("high_risk without human review", test_high_risk_without_human_review),
        ("missing terminal_conditions", test_missing_terminal_conditions),
    ]

    passed = 0
    failed = 0
    print("=" * 60)
    print("TASKSPEC Schema Tests")
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
