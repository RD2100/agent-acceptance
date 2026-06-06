"""Test GPT reply completeness validation."""

import sys, tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from scripts.validate_gpt_reply_completeness import check_completeness


def test_review_too_short():
    result = check_completeness("nonexistent.txt", "review")
    assert result["complete"] is False
    assert result["file_size"] == 0


def test_review_no_required_fields():
    fp = Path(tempfile.gettempdir()) / "test_short_review.txt"
    fp.write_text("short reply without fields", encoding="utf-8")
    result = check_completeness(str(fp), "review")
    assert result["complete"] is False
    fp.unlink()


def test_handoff_too_short():
    fp = Path(tempfile.gettempdir()) / "test_short_handoff.txt"
    fp.write_text("END_OF_HANDOFF", encoding="utf-8")
    result = check_completeness(str(fp), "handoff")
    assert result["complete"] is False  # < 8000 bytes
    fp.unlink()


def test_handoff_valid():
    fp = Path(tempfile.gettempdir()) / "test_valid_handoff.txt"
    content = "# Handoff\n\n" + "x" * 8000 + "\nEND_OF_HANDOFF\n"
    fp.write_text(content, encoding="utf-8")
    result = check_completeness(str(fp), "handoff")
    assert result["complete"] is True
    fp.unlink()


def run_all_tests():
    tests = [
        ("review too short", test_review_too_short),
        ("review missing fields", test_review_no_required_fields),
        ("handoff too short", test_handoff_too_short),
        ("handoff valid", test_handoff_valid),
    ]
    passed = failed = 0
    print("=" * 60)
    print("GPT Reply Completeness — Tests")
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
