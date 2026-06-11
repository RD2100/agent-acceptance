"""test_verify_gpt_reply.py — Regression tests for verify_gpt_reply.py.

Test cases per HANDOFF_WORKFLOW_HARDENING_PLAN.md section 5.5:
  VRT-001: Valid accepted reply -> PASS
  VRT-002: Valid accepted_with_limitation -> PASS
  VRT-003: Missing run_id -> FAIL
  VRT-004: run_id mismatch -> FAIL
  VRT-005: Missing END_OF_GPT_RESPONSE -> FAIL
  VRT-006: Empty file input -> FAIL
  VRT-007: Verdict flattening attack -> FAIL
  VRT-008: Stale reply -> FAIL (not implemented in verifier)
  VRT-009: Truncated reply -> FAIL
  VRT-010: Invalid verdict value -> FAIL
  VRT-011: Blocked verdict -> valid but not closure_ready
  VRT-012: Missing next_task_authorization for accepted -> FAIL
"""

import json
import pytest
import tempfile
from pathlib import Path

# Import the verify module
from verify_gpt_reply import verify, closure_ready


def write_reply(tmp_path, content: str, filename="reply.txt") -> str:
    """Write reply content to a temp file and return its path."""
    p = tmp_path / filename
    p.write_text(content, encoding="utf-8")
    return str(p)


class TestValidReplies:
    """VRT-001 and VRT-002: Valid replies should pass verification."""

    def test_vrt001_valid_accepted(self, tmp_path, valid_accepted_reply):
        """VRT-001: Normal accepted reply should PASS."""
        path = write_reply(tmp_path, valid_accepted_reply)
        result = verify(path, "TEST-TASK-A1")
        assert result["valid"] is True
        assert result["overall_judgment"] == "accepted"
        assert result["checks"]["has_end_marker"] is True
        assert result["checks"]["has_next_task_auth"] is True
        assert len(result["errors"]) == 0

    def test_vrt002_valid_accepted_with_limitation(self, tmp_path, valid_accepted_with_limitation_reply):
        """VRT-002: accepted_with_limitation with limitations should PASS."""
        path = write_reply(tmp_path, valid_accepted_with_limitation_reply)
        result = verify(path, "TEST-TASK-A2")
        assert result["valid"] is True
        assert result["overall_judgment"] == "accepted_with_limitation"
        assert len(result["errors"]) == 0

    def test_vrt001_closure_ready_accepted(self, tmp_path, valid_accepted_reply):
        """VRT-001 extended: accepted verdict should be closure_ready."""
        path = write_reply(tmp_path, valid_accepted_reply)
        cr = closure_ready(path, "TEST-TASK-A1")
        assert cr["closure_ready"] is True


class TestMissingFields:
    """VRT-003 to VRT-006: Missing required fields should FAIL."""

    def test_vrt003_missing_run_id(self, tmp_path, reply_missing_run_id):
        """VRT-003: Reply without run_id field should FAIL with missing_run_id."""
        path = write_reply(tmp_path, reply_missing_run_id)
        result = verify(path, expected_run_id="EXPECTED_RUN_ID_RD")
        assert result["valid"] is False
        assert "missing_run_id" in result["errors"]
        assert result["checks"].get("run_id_in_reply") is None

    def test_vrt004_run_id_mismatch(self, tmp_path, reply_wrong_run_id):
        """VRT-004: Reply with wrong run_id should FAIL with run_id_mismatch."""
        path = write_reply(tmp_path, reply_wrong_run_id)
        result = verify(path, expected_run_id="EXPECTED_RUN_ID_004_RD")
        assert result["valid"] is False
        assert any("run_id_mismatch" in e for e in result["errors"])
        assert result["checks"].get("run_id_matches") is False

    def test_vrt005_missing_end_marker(self, tmp_path, reply_missing_end_marker):
        """VRT-005: Reply without END_OF_GPT_RESPONSE should FAIL."""
        path = write_reply(tmp_path, reply_missing_end_marker)
        result = verify(path, "TEST-TASK-A5")
        assert result["valid"] is False
        assert "missing END_OF_GPT_RESPONSE" in result["errors"]
        assert result["checks"]["has_end_marker"] is False

    def test_vrt006_empty_file(self, tmp_path):
        """VRT-006: Empty (0-byte) file should FAIL."""
        path = write_reply(tmp_path, "")
        result = verify(path)
        assert result["valid"] is False
        assert result["overall_judgment"] is None
        assert result["size"] == 0

    def test_vrt006_file_not_found(self, tmp_path):
        """VRT-006 extended: Non-existent file should FAIL."""
        result = verify(str(tmp_path / "nonexistent.txt"))
        assert result["valid"] is False
        assert any("not found" in e for e in result["errors"])


class TestVerdictValidation:
    """VRT-007 to VRT-010: Invalid verdict values should FAIL."""

    def test_vrt010_invalid_verdict_rejected(self, tmp_path, reply_invalid_verdict):
        """VRT-010: verdict = 'rejected' (not in valid enum) should FAIL."""
        path = write_reply(tmp_path, reply_invalid_verdict)
        result = verify(path)
        assert result["valid"] is False
        assert any("invalid overall_judgment" in e for e in result["errors"])

    def test_vrt007_uppercase_verdict(self, tmp_path, reply_uppercase_verdict):
        """VRT-007: ACCEPTED (all caps) — verifier lowercases, so this should pass."""
        path = write_reply(tmp_path, reply_uppercase_verdict)
        result = verify(path)
        # The verifier does .lower() on the verdict, so ACCEPTED becomes accepted
        assert result["overall_judgment"] == "accepted"

    def test_vrt007_nonstandard_verdict_pass(self, tmp_path):
        """VRT-007: verdict = 'pass' (non-standard) should FAIL."""
        reply = """overall_judgment: pass
evidence_pack_reviewed: true
blocking_issues: none
run_id: TEST_RD
task_id: TEST-TASK

END_OF_GPT_RESPONSE"""
        path = write_reply(tmp_path, reply)
        result = verify(path)
        assert result["valid"] is False
        assert any("invalid overall_judgment" in e for e in result["errors"])

    def test_vrt009_truncated_reply(self, tmp_path, reply_truncated):
        """VRT-009: Truncated reply (no END_OF_GPT_RESPONSE) should FAIL."""
        path = write_reply(tmp_path, reply_truncated)
        result = verify(path)
        assert result["valid"] is False
        assert "missing END_OF_GPT_RESPONSE" in result["errors"]

    def test_vrt012_accepted_without_next_auth(self, tmp_path):
        """VRT-012: Accepted verdict missing next_task_authorization should FAIL."""
        reply = """overall_judgment: accepted
evidence_pack_reviewed: true
blocking_issues: none
required_fixes: none

run_id: TEST_RUN_ID_012_RD
task_id: TEST-TASK-012

END_OF_GPT_RESPONSE"""
        path = write_reply(tmp_path, reply)
        result = verify(path, "TEST-TASK-012")
        assert result["valid"] is False
        assert "accepted verdict missing next_task_authorization" in result["errors"]


class TestBlockedVerdict:
    """VRT-011: Blocked verdict behavior."""

    def test_vrt011_blocked_verdict_valid_but_not_closure(self, tmp_path):
        """VRT-011: Blocked verdict should be valid but NOT closure_ready."""
        reply = """overall_judgment: blocked
evidence_pack_reviewed: true
blocking_issues:
- issue 1
- issue 2
required_fixes:
- fix 1

run_id: TEST_RUN_ID_011_RD
task_id: TEST-TASK-011

END_OF_GPT_RESPONSE"""
        path = write_reply(tmp_path, reply)
        result = verify(path, "TEST-TASK-011")
        assert result["valid"] is True
        assert result["overall_judgment"] == "blocked"

        cr = closure_ready(path, "TEST-TASK-011")
        assert cr["closure_ready"] is False
        assert "blocked" in cr["reason"].lower()


class TestTaskIdMatching:
    """Test task_id matching behavior."""

    def test_task_id_match(self, tmp_path, valid_accepted_reply):
        """Correct task_id should pass matching check."""
        path = write_reply(tmp_path, valid_accepted_reply)
        result = verify(path, "TEST-TASK-A1")
        assert result["checks"].get("task_id_matches") is True

    def test_task_id_mismatch(self, tmp_path, valid_accepted_reply):
        """Wrong task_id should fail matching check."""
        path = write_reply(tmp_path, valid_accepted_reply)
        result = verify(path, "WRONG-TASK-ID")
        assert result["checks"].get("task_id_matches") is False
        assert result["valid"] is False

    def test_no_expected_task_id(self, tmp_path, valid_accepted_reply):
        """When no expected task_id is provided, matching should be skipped."""
        path = write_reply(tmp_path, valid_accepted_reply)
        result = verify(path)
        # Should still be valid (no task_id comparison)
        assert result["valid"] is True


class TestEdgeCases:
    """Additional edge case tests."""

    def test_reply_with_extra_whitespace(self, tmp_path):
        """Reply with extra whitespace around fields."""
        reply = """overall_judgment:   accepted_with_limitation
evidence_pack_reviewed: true
blocking_issues:

none
required_fixes:

none

run_id: TEST_RD
task_id: TEST-TASK

next_task_authorization:
task_id: NEXT-TASK
authorized: yes

END_OF_GPT_RESPONSE"""
        path = write_reply(tmp_path, reply)
        result = verify(path, "TEST-TASK")
        assert result["valid"] is True
        assert result["overall_judgment"] == "accepted_with_limitation"

    def test_reply_with_unicode_content(self, tmp_path):
        """Reply containing Unicode characters (Chinese)."""
        reply = """overall_judgment: accepted_with_limitation
evidence_pack_reviewed: true
limitations:
-  limitation 1: 中文说明
-  limitation 2: another 说明

run_id: TEST_RD
task_id: TEST-TASK

next_task_authorization:
task_id: NEXT-TASK
authorized: 已授权
execute_immediately: 是
ask_before_starting: 否

END_OF_GPT_RESPONSE"""
        path = write_reply(tmp_path, reply)
        result = verify(path, "TEST-TASK")
        assert result["valid"] is True


class TestStructuredParse:
    """Tests for structured parse fix: task_id extraction must skip
    next_task_authorization block regardless of field ordering."""

    def test_task_id_before_auth_block(self, tmp_path):
        """Footer task_id BEFORE next_task_authorization — should match correctly."""
        reply = """overall_judgment: accepted
evidence_pack_reviewed: true
blocking_issues: none
required_fixes: none

run_id: TEST_RD
task_id: MY-TASK-A1

next_task_authorization:
task_id: NEXT-TASK-A1
authorized: yes
execute_immediately: yes

END_OF_GPT_RESPONSE"""
        path = write_reply(tmp_path, reply)
        result = verify(path, "MY-TASK-A1")
        assert result["valid"] is True
        assert result["checks"]["task_id_in_reply"] == "MY-TASK-A1"

    def test_task_id_after_auth_block(self, tmp_path):
        """Footer task_id AFTER next_task_authorization — structured parse must
        skip the auth block's task_id and find the footer's task_id."""
        reply = """overall_judgment: accepted_with_limitation
evidence_pack_reviewed: true
blocking_issues: none
required_fixes: none
limitations: some limitation

next_task_authorization:
task_id: NEXT-TASK-B1
authorized: yes
execute_immediately: yes

run_id: TEST_RD
task_id: MY-TASK-B1

END_OF_GPT_RESPONSE"""
        path = write_reply(tmp_path, reply)
        result = verify(path, "MY-TASK-B1")
        assert result["valid"] is True
        assert result["checks"]["task_id_in_reply"] == "MY-TASK-B1"
        assert result["checks"]["task_id_matches"] is True

    def test_task_id_only_in_auth_block(self, tmp_path):
        """Only task_id is inside next_task_authorization — should still find it as fallback."""
        reply = """overall_judgment: blocked
evidence_pack_reviewed: true
blocking_issues:
- critical issue

next_task_authorization:
task_id: ONLY-TASK
authorized: no

run_id: TEST_RD

END_OF_GPT_RESPONSE"""
        path = write_reply(tmp_path, reply)
        result = verify(path)
        assert result["overall_judgment"] == "blocked"
        # Fallback: should find the only task_id available
        assert result["checks"]["task_id_in_reply"] == "ONLY-TASK"

    def test_real_gpt_reply_format(self, tmp_path):
        """Simulate exact format from real GPT reply that caused the original false positive."""
        reply = """overall_judgment: accepted_with_limitation
evidence_pack_reviewed: true
attachment_reviewed: true
blocking_issues:

none
required_fixes:

none
limitations:

some limitation here
next_task_authorization:
task_id: VERIFY-GPT-REPLY-STRUCTURED-PARSE-HARDEN-A1
authorized: 已授权
execute_immediately: 是
ask_before_starting: 否

run_id: GPT_REVIEW_FLOW_REGRESSION_TEST_A1_REVIEW_20260609T120034_RD
task_id: GPT-REVIEW-FLOW-REGRESSION-TEST-A1

END_OF_GPT_RESPONSE"""
        path = write_reply(tmp_path, reply)
        result = verify(path, "GPT-REVIEW-FLOW-REGRESSION-TEST-A1")
        assert result["valid"] is True
        assert result["checks"]["task_id_in_reply"] == "GPT-REVIEW-FLOW-REGRESSION-TEST-A1"
        assert result["checks"]["task_id_matches"] is True
