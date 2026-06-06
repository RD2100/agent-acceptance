"""Test minimal memory compiler."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from scripts.memory_compiler import extract_lessons_from_review, extract_lessons_from_ledger, find_audit_ledger


def test_audit_ledger_found():
    ledger = find_audit_ledger()
    assert ledger is not None, "WORKFLOW_AUDIT_LEDGER.yaml should exist"


def test_extract_from_ledger():
    ledger = find_audit_ledger()
    lessons = extract_lessons_from_ledger(ledger)
    assert len(lessons) > 0, "Should extract lessons from ledger"


def test_extract_summary_only_pattern():
    text = "summary-only evidence pack detected. overall_judgment: blocked"
    lessons = extract_lessons_from_review(text, "test-001", "TEST")
    assert any("summary-only" in l["lesson"] for l in lessons)


def test_extract_ready_for_review_as_closed():
    text = "ready_for_review was counted as closed. overall_judgment: blocked"
    lessons = extract_lessons_from_review(text, "test-002", "TEST2")
    assert any("ready_for_review" in l["lesson"] for l in lessons)


def test_extract_manifest_mismatch():
    text = "manifest 与 ZIP 不一致，SHA256 不匹配"
    lessons = extract_lessons_from_review(text, "test-003", "TEST3")
    assert any("manifest" in l["lesson"] for l in lessons)


def test_extract_accepted():
    text = "overall_judgment: accepted"
    lessons = extract_lessons_from_review(text, "test-004", "TEST4")
    assert any("accepted" in l["lesson"] for l in lessons)


def run_all_tests():
    tests = [
        ("audit ledger found", test_audit_ledger_found),
        ("extract from ledger", test_extract_from_ledger),
        ("extract summary-only", test_extract_summary_only_pattern),
        ("extract ready_for_review", test_extract_ready_for_review_as_closed),
        ("extract manifest mismatch", test_extract_manifest_mismatch),
        ("extract accepted", test_extract_accepted),
    ]
    passed = failed = 0
    print("=" * 60)
    print("Memory Compiler — Tests")
    print("=" * 60)
    for name, fn in tests:
        try:
            fn()
            print(f"  [PASS] {name}")
            passed += 1
        except Exception as e:
            print(f"  [FAIL] {name}: {e}")
            failed += 1
    print(f"\n  Results: {passed}/{passed+failed} passed")
    return failed == 0


if __name__ == "__main__":
    sys.exit(0 if run_all_tests() else 1)
