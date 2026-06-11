"""Test handoff trigger detection."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from scripts.check_handoff_needed import check_handoff


def test_normal_conversation():
    result = check_handoff(assistant_message_count=10, response_time_seconds=15)
    assert result["handoff_needed"] is False
    assert result["force_handoff"] is False


def test_force_handoff_message_count():
    result = check_handoff(assistant_message_count=60)
    assert result["handoff_needed"] is True
    assert result["force_handoff"] is True
    assert any(">= 60" in r for r in result["reasons"])


def test_force_handoff_short_reply():
    """Short reply alone is SUGGEST, not FORCE (consensus semantics from GPT R1 review)."""
    result = check_handoff(last_gpt_reply_bytes=500)
    assert result["handoff_needed"] is False
    assert result["force_handoff"] is False
    assert result["suggested_only"] is True
    assert any("< 2000" in r for r in result["reasons"])


def test_force_handoff_many_rounds():
    result = check_handoff(review_round_count=5)
    assert result["handoff_needed"] is True
    assert result["force_handoff"] is True


def test_current_conversation():
    """Test with actual current conversation stats (82 msgs, 90s response)."""
    result = check_handoff(
        assistant_message_count=82,
        response_time_seconds=90,
        review_round_count=0,
        last_gpt_reply_bytes=22224,
    )
    assert result["handoff_needed"] is True
    assert result["force_handoff"] is True
    assert result["recommended_action"] == "generate_handoff"


def run_all_tests():
    tests = [
        ("normal conversation OK", test_normal_conversation),
        ("force handoff msg count", test_force_handoff_message_count),
        ("force handoff short reply", test_force_handoff_short_reply),
        ("force handoff many rounds", test_force_handoff_many_rounds),
        ("current conversation triggers handoff", test_current_conversation),
    ]
    passed = failed = 0
    print("=" * 60)
    print("Handoff Trigger — Tests")
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
