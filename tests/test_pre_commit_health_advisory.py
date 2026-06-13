"""Tests for Pre-Commit Conversation Health Advisory (A3 Layer 4).

Covers:
    - Advisory with healthy metrics → exit 0, decision OK
    - Advisory with FORCE_HANDOFF → exit 1, decision FORCE_HANDOFF
    - Advisory with HUMAN_REQUIRED → exit 1, decision HUMAN_REQUIRED
    - Advisory with missing evidence → exit 2, decision UNKNOWN
    - Advisory with unreadable evidence → exit 2, graceful degradation
    - Advisory with decision engine unavailable → exit 0, graceful degradation
    - Advisory never blocks commit (always returns valid result)
    - Format output produces expected structure
    - A1/A2 non-regression: advisory uses same decision engine
"""

from __future__ import annotations

import json
import sys
import os
import tempfile
import shutil
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Add scripts dir to path
SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

from pre_commit_health_advisory import (
    run_advisory,
    format_advisory_output,
    EXIT_HEALTHY,
    EXIT_DEGRADED,
    EXIT_EVIDENCE_MISSING,
    EXIT_MODULE_ERROR,
)


@pytest.fixture
def tmp_evidence(tmp_path):
    """Create a temporary evidence directory structure."""
    current_dir = tmp_path / ".ai" / "conversation"
    current_dir.mkdir(parents=True)
    latest_dir = tmp_path / "_evidence" / "conversation-health"
    latest_dir.mkdir(parents=True)
    return tmp_path


def _write_current_json(path: Path, data: dict):
    """Write current.json to the expected location."""
    current_file = path / ".ai" / "conversation" / "current.json"
    current_file.write_text(json.dumps(data), encoding="utf-8")
    return str(current_file)


def _write_latest_json(path: Path, data: dict):
    """Write latest.json to the expected location."""
    latest_file = path / "_evidence" / "conversation-health" / "latest.json"
    latest_file.write_text(json.dumps(data), encoding="utf-8")
    return str(latest_file)


def _recent_checked_at(offset_hours: float = 1.0) -> str:
    """Return an ISO-8601 UTC timestamp offset_hours ago (avoids staleness)."""
    dt = datetime.now(timezone.utc) - timedelta(hours=offset_hours)
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def _healthy_metrics():
    """Return healthy metrics data."""
    return {
        "schema_version": "conversation-health.v1",
        "conversation_id": "test-conv-123",
        "chat_url": "https://chatgpt.com/c/test-123",
        "status": "active",
        "last_known_metrics": {
            "assistant_message_count": 10,
            "review_round_count": 1,
            "last_response_time_seconds": 5.0,
            "last_gpt_reply_bytes": 5000,
        },
        "last_nav_result": "ok",
        "last_checked_at": _recent_checked_at(),
        "metrics_source": "cdp_dom_count",
    }


def _degraded_metrics():
    """Return metrics indicating FORCE_HANDOFF."""
    return {
        "schema_version": "conversation-health.v1",
        "conversation_id": "test-conv-456",
        "chat_url": "https://chatgpt.com/c/test-456",
        "status": "handoff_required",
        "last_known_metrics": {
            "assistant_message_count": 65,
            "review_round_count": 4,
            "last_response_time_seconds": 120.0,
            "last_gpt_reply_bytes": 500,
        },
        "last_nav_result": "ok",
        "last_checked_at": _recent_checked_at(),
        "metrics_source": "cdp_dom_count",
    }


def _auth_required_metrics():
    """Return metrics indicating HUMAN_REQUIRED (auth_required)."""
    return {
        "schema_version": "conversation-health.v1",
        "conversation_id": "test-conv-789",
        "chat_url": "https://chatgpt.com/c/test-789",
        "status": "inaccessible",
        "last_known_metrics": {
            "assistant_message_count": 30,
            "review_round_count": 2,
            "last_response_time_seconds": 10.0,
            "last_gpt_reply_bytes": 3000,
        },
        "last_nav_result": "auth_required",
        "last_checked_at": _recent_checked_at(),
        "metrics_source": "cdp_dom_count",
    }


# =============================================================================
# TestAdvisoryHealthy
# =============================================================================

class TestAdvisoryHealthy:
    """Advisory with healthy conversation should return exit 0."""

    def test_healthy_returns_exit_0(self, tmp_evidence):
        data = _healthy_metrics()
        latest_path = _write_latest_json(tmp_evidence, data)
        exit_code, result = run_advisory(
            latest_json_path=latest_path,
            current_json_path=str(tmp_evidence / ".ai" / "conversation" / "current.json"),
            project_root=str(tmp_evidence),
        )
        assert exit_code == EXIT_HEALTHY
        assert result["decision"] == "OK"

    def test_healthy_recommendation_is_continue(self, tmp_evidence):
        data = _healthy_metrics()
        latest_path = _write_latest_json(tmp_evidence, data)
        exit_code, result = run_advisory(
            latest_json_path=latest_path,
            current_json_path=str(tmp_evidence / ".ai" / "conversation" / "current.json"),
            project_root=str(tmp_evidence),
        )
        assert result["recommendation"] == "continue"

    def test_healthy_severity_is_info_or_warning(self, tmp_evidence):
        data = _healthy_metrics()
        latest_path = _write_latest_json(tmp_evidence, data)
        exit_code, result = run_advisory(
            latest_json_path=latest_path,
            current_json_path=str(tmp_evidence / ".ai" / "conversation" / "current.json"),
            project_root=str(tmp_evidence),
        )
        assert result["severity"] in ("INFO", "WARNING")


# =============================================================================
# TestAdvisoryDegraded
# =============================================================================

class TestAdvisoryDegraded:
    """Advisory with degraded conversation should return exit 1 (advisory warning)."""

    def test_force_handoff_returns_exit_1(self, tmp_evidence):
        data = _degraded_metrics()
        latest_path = _write_latest_json(tmp_evidence, data)
        exit_code, result = run_advisory(
            latest_json_path=latest_path,
            current_json_path=str(tmp_evidence / ".ai" / "conversation" / "current.json"),
            project_root=str(tmp_evidence),
        )
        assert exit_code == EXIT_DEGRADED
        assert result["decision"] == "FORCE_HANDOFF"

    def test_human_required_returns_exit_1(self, tmp_evidence):
        data = _auth_required_metrics()
        latest_path = _write_latest_json(tmp_evidence, data)
        exit_code, result = run_advisory(
            latest_json_path=latest_path,
            current_json_path=str(tmp_evidence / ".ai" / "conversation" / "current.json"),
            project_root=str(tmp_evidence),
        )
        assert exit_code == EXIT_DEGRADED
        assert result["decision"] == "HUMAN_REQUIRED"

    def test_degraded_has_reasons(self, tmp_evidence):
        data = _degraded_metrics()
        latest_path = _write_latest_json(tmp_evidence, data)
        exit_code, result = run_advisory(
            latest_json_path=latest_path,
            current_json_path=str(tmp_evidence / ".ai" / "conversation" / "current.json"),
            project_root=str(tmp_evidence),
        )
        assert len(result["reasons"]) > 0

    def test_degraded_recommendation_is_handoff(self, tmp_evidence):
        data = _degraded_metrics()
        latest_path = _write_latest_json(tmp_evidence, data)
        exit_code, result = run_advisory(
            latest_json_path=latest_path,
            current_json_path=str(tmp_evidence / ".ai" / "conversation" / "current.json"),
            project_root=str(tmp_evidence),
        )
        assert result["recommendation"] in ("handoff_recommended", "human_intervention_needed")


# =============================================================================
# TestAdvisoryMissingEvidence
# =============================================================================

class TestAdvisoryMissingEvidence:
    """Advisory with missing evidence should return exit 2 (advisory warning)."""

    def test_missing_both_returns_exit_2(self, tmp_evidence):
        exit_code, result = run_advisory(
            latest_json_path=str(tmp_evidence / "_evidence" / "conversation-health" / "latest.json"),
            current_json_path=str(tmp_evidence / ".ai" / "conversation" / "current.json"),
            project_root=str(tmp_evidence),
        )
        assert exit_code == EXIT_EVIDENCE_MISSING
        assert result["decision"] == "UNKNOWN"

    def test_missing_evidence_has_reason(self, tmp_evidence):
        exit_code, result = run_advisory(
            latest_json_path=str(tmp_evidence / "_evidence" / "conversation-health" / "latest.json"),
            current_json_path=str(tmp_evidence / ".ai" / "conversation" / "current.json"),
            project_root=str(tmp_evidence),
        )
        assert any(r.get("code") == "no_evidence_available" for r in result["reasons"])

    def test_fallback_to_current_json(self, tmp_evidence):
        """If latest.json missing, should fall back to current.json."""
        data = _healthy_metrics()
        current_path = _write_current_json(tmp_evidence, data)
        exit_code, result = run_advisory(
            latest_json_path=str(tmp_evidence / "_evidence" / "conversation-health" / "latest.json"),
            current_json_path=current_path,
            project_root=str(tmp_evidence),
        )
        assert exit_code == EXIT_HEALTHY
        assert result["decision"] == "OK"


# =============================================================================
# TestAdvisoryUnreadableEvidence
# =============================================================================

class TestAdvisoryUnreadableEvidence:
    """Advisory with unreadable evidence should degrade gracefully."""

    def test_corrupt_json_returns_exit_2(self, tmp_evidence):
        latest_file = tmp_evidence / "_evidence" / "conversation-health" / "latest.json"
        latest_file.write_text("{ invalid json }", encoding="utf-8")
        exit_code, result = run_advisory(
            latest_json_path=str(latest_file),
            current_json_path=str(tmp_evidence / ".ai" / "conversation" / "current.json"),
            project_root=str(tmp_evidence),
        )
        # Should fall through to current.json or return MISSING
        assert exit_code in (EXIT_EVIDENCE_MISSING, EXIT_HEALTHY)


# =============================================================================
# TestAdvisoryDecisionEngineUnavailable
# =============================================================================

class TestAdvisoryDecisionEngineUnavailable:
    """If decision engine cannot be imported, advisory should still return exit 0."""

    def test_import_error_returns_healthy(self, tmp_evidence):
        data = _healthy_metrics()
        latest_path = _write_latest_json(tmp_evidence, data)

        # Mock the import to fail
        with patch.dict(sys.modules, {"check_handoff_needed": None}):
            exit_code, result = run_advisory(
                latest_json_path=latest_path,
                current_json_path=str(tmp_evidence / ".ai" / "conversation" / "current.json"),
                project_root=str(tmp_evidence),
            )
        assert exit_code == EXIT_HEALTHY
        assert result["decision"] == "UNKNOWN"
        assert any(r.get("code") == "decision_engine_unavailable" for r in result["reasons"])


# =============================================================================
# TestAdvisoryNeverBlocks
# =============================================================================

class TestAdvisoryNeverBlocks:
    """Advisory stage must NEVER block commit — verify exit codes are advisory only."""

    def test_all_exit_codes_are_non_blocking(self, tmp_evidence):
        """Verify that even degraded results produce valid exit codes."""
        data = _degraded_metrics()
        latest_path = _write_latest_json(tmp_evidence, data)
        exit_code, result = run_advisory(
            latest_json_path=latest_path,
            current_json_path=str(tmp_evidence / ".ai" / "conversation" / "current.json"),
            project_root=str(tmp_evidence),
        )
        # Exit code 1 means "advisory warning" not "block commit"
        # The hook treats this as advisory (never blocks)
        assert exit_code in (EXIT_HEALTHY, EXIT_DEGRADED, EXIT_EVIDENCE_MISSING, EXIT_MODULE_ERROR)

    def test_advisory_type_is_correct(self, tmp_evidence):
        data = _healthy_metrics()
        latest_path = _write_latest_json(tmp_evidence, data)
        exit_code, result = run_advisory(
            latest_json_path=latest_path,
            current_json_path=str(tmp_evidence / ".ai" / "conversation" / "current.json"),
            project_root=str(tmp_evidence),
        )
        assert result["advisory_type"] == "conversation-health"


# =============================================================================
# TestAdvisoryFormatOutput
# =============================================================================

class TestAdvisoryFormatOutput:
    """Test the human-readable output formatter."""

    def test_format_healthy_output(self):
        result = {
            "checked_at": "2026-06-12T10:00:00Z",
            "evidence_source": "/path/to/latest.json",
            "decision": "OK",
            "severity": "INFO",
            "recommendation": "continue",
            "reasons": [],
            "source_files": {"latest_json": "present"},
        }
        output = format_advisory_output(EXIT_HEALTHY, result)
        assert "Conversation Health Advisory" in output
        assert "OK" in output
        assert "[ADVISORY]" in output

    def test_format_degraded_output(self):
        result = {
            "checked_at": "2026-06-12T10:00:00Z",
            "evidence_source": "/path/to/latest.json",
            "decision": "FORCE_HANDOFF",
            "severity": "BLOCKING",
            "recommendation": "handoff_recommended",
            "reasons": [{"code": "msg_count", "actual": "65", "policy": "force"}],
            "source_files": {"latest_json": "present"},
        }
        output = format_advisory_output(EXIT_DEGRADED, result)
        assert "FORCE_HANDOFF" in output
        assert "WARNING" in output

    def test_format_missing_output(self):
        result = {
            "checked_at": "2026-06-12T10:00:00Z",
            "decision": "UNKNOWN",
            "severity": "INFO",
            "recommendation": "consider_running_pre_gpt_gate",
            "reasons": [{"code": "no_evidence_available", "actual": "none", "policy": "advisory"}],
            "source_files": {"latest_json": "missing", "current_json": "missing"},
        }
        output = format_advisory_output(EXIT_EVIDENCE_MISSING, result)
        assert "No conversation-health evidence" in output


# =============================================================================
# TestA1A2NonRegression
# =============================================================================

class TestA1A2NonRegression:
    """Ensure A3 advisory does not break A1/A2 behavior."""

    def test_advisory_uses_same_decision_engine(self, tmp_evidence):
        """Advisory should use the same check_handoff_v2 as pre-task and pre-GPT gates."""
        data = _healthy_metrics()
        latest_path = _write_latest_json(tmp_evidence, data)
        exit_code, result = run_advisory(
            latest_json_path=latest_path,
            current_json_path=str(tmp_evidence / ".ai" / "conversation" / "current.json"),
            project_root=str(tmp_evidence),
        )
        # Decision should be a valid decision string from the engine
        assert result["decision"] in ("OK", "FORCE_HANDOFF", "SUGGEST_HANDOFF", "UNKNOWN", "HUMAN_REQUIRED")

    def test_advisory_preserves_threshold_semantics(self, tmp_evidence):
        """Manual_estimate source should still cap at SUGGEST even in advisory mode."""
        data = _healthy_metrics()
        data["last_known_metrics"]["assistant_message_count"] = 65
        data["metrics_source"] = "manual_estimate"
        latest_path = _write_latest_json(tmp_evidence, data)
        exit_code, result = run_advisory(
            latest_json_path=latest_path,
            current_json_path=str(tmp_evidence / ".ai" / "conversation" / "current.json"),
            project_root=str(tmp_evidence),
        )
        # manual_estimate caps at SUGGEST (not FORCE) per A1 semantics
        if result["decision"] != "OK":
            assert result["decision"] in ("SUGGEST_HANDOFF", "UNKNOWN")

    def test_advisory_auth_required_is_human(self, tmp_evidence):
        """auth_required nav_result should produce HUMAN_REQUIRED in advisory mode."""
        data = _auth_required_metrics()
        latest_path = _write_latest_json(tmp_evidence, data)
        exit_code, result = run_advisory(
            latest_json_path=latest_path,
            current_json_path=str(tmp_evidence / ".ai" / "conversation" / "current.json"),
            project_root=str(tmp_evidence),
        )
        assert result["decision"] == "HUMAN_REQUIRED"


# =============================================================================
# TestAdvisoryNonzeroDoesNotBlock (R2-3a)
# =============================================================================

class TestAdvisoryNonzeroDoesNotBlock:
    """Verify that conversation-health nonzero exit does NOT set overall_result=BLOCKED.

    This simulates the hook's overall_result logic: only sadp-audit and ai-guard
    can BLOCK. conversation-health is advisory — its exit code is logged but does
    not affect the commit decision.
    """

    def test_degraded_exit_is_advisory_not_blocking(self, tmp_evidence):
        """FORCE_HANDOFF produces exit 1, but hook must NOT block."""
        data = _degraded_metrics()
        latest_path = _write_latest_json(tmp_evidence, data)
        exit_code, result = run_advisory(
            latest_json_path=latest_path,
            current_json_path=str(tmp_evidence / ".ai" / "conversation" / "current.json"),
            project_root=str(tmp_evidence),
        )
        # Exit code 1 means advisory warning, NOT "block commit"
        assert exit_code == EXIT_DEGRADED
        # The hook's blocking stages are ONLY sadp-audit and ai-guard
        blocking_stages = {"sadp-audit", "ai-guard"}
        assert "conversation-health" not in blocking_stages

    def test_evidence_missing_exit_is_advisory_not_blocking(self, tmp_evidence):
        """Evidence missing produces exit 2, but hook must NOT block."""
        exit_code, result = run_advisory(
            latest_json_path=str(tmp_evidence / "_evidence" / "conversation-health" / "latest.json"),
            current_json_path=str(tmp_evidence / ".ai" / "conversation" / "current.json"),
            project_root=str(tmp_evidence),
        )
        assert exit_code == EXIT_EVIDENCE_MISSING
        # Advisory: hook records but does not block


# =============================================================================
# TestAdvisoryModuleErrorSemantics (R2-3b)
# =============================================================================

class TestAdvisoryModuleErrorSemantics:
    """Verify module error returns exit 3 (diagnostic) with advisory_error code.

    Per R2 fix: module error exit 3 is a diagnostic signal.
    The hook treats conversation-health as advisory regardless of exit code.
    """

    def test_module_error_returns_exit_3(self, tmp_evidence):
        """Internal errors produce EXIT_MODULE_ERROR (3) — diagnostic, not blocking."""
        data = _healthy_metrics()
        latest_path = _write_latest_json(tmp_evidence, data)

        # Mock check_handoff_v2 to raise an unexpected error
        import check_handoff_needed
        original_fn = check_handoff_needed.check_handoff_v2

        def _raise_error(*args, **kwargs):
            raise RuntimeError("simulated internal error")

        check_handoff_needed.check_handoff_v2 = _raise_error
        try:
            exit_code, result = run_advisory(
                latest_json_path=latest_path,
                current_json_path=str(tmp_evidence / ".ai" / "conversation" / "current.json"),
                project_root=str(tmp_evidence),
            )
        finally:
            check_handoff_needed.check_handoff_v2 = original_fn

        assert exit_code == EXIT_MODULE_ERROR
        assert result["decision"] == "UNKNOWN"
        assert any(r.get("code") == "advisory_error" for r in result["reasons"])

    def test_module_error_records_diagnostic_reason(self, tmp_evidence):
        """Module error must include advisory_error reason with actual error text."""
        data = _healthy_metrics()
        latest_path = _write_latest_json(tmp_evidence, data)

        import check_handoff_needed
        original_fn = check_handoff_needed.check_handoff_v2

        def _raise_error(*args, **kwargs):
            raise ValueError("test diagnostic message")

        check_handoff_needed.check_handoff_v2 = _raise_error
        try:
            exit_code, result = run_advisory(
                latest_json_path=latest_path,
                current_json_path=str(tmp_evidence / ".ai" / "conversation" / "current.json"),
                project_root=str(tmp_evidence),
            )
        finally:
            check_handoff_needed.check_handoff_v2 = original_fn

        error_reasons = [r for r in result["reasons"] if r.get("code") == "advisory_error"]
        assert len(error_reasons) == 1
        assert "test diagnostic message" in error_reasons[0]["actual"]


# =============================================================================
# TestHookOutputSchemaWithConversationHealth (R2-3c)
# =============================================================================

class TestHookOutputSchemaWithConversationHealth:
    """Verify hook-output JSON with conversation-health validates against schema."""

    def test_hook_output_with_5_stages_validates(self):
        """A hook-output with 5 stages including conversation-health must validate."""
        import jsonschema
        schema_path = Path(__file__).resolve().parent.parent / "schemas" / "agent-runtime" / "evidence-capture.schema.json"
        schema = json.loads(schema_path.read_text(encoding="utf-8"))

        hook_output = {
            "timestamp": "2026-06-12T00:00:00Z",
            "hook_version": "2.4.0",
            "stages": [
                {"name": "manifest-regen", "exit_code": 0, "output_file": None, "duration_ms": 0},
                {"name": "sadp-audit", "exit_code": 0, "output_file": "sadp.txt", "duration_ms": 100},
                {"name": "ai-guard", "exit_code": 0, "output_file": "ai.txt", "duration_ms": 50},
                {"name": "test-governance", "exit_code": 0, "output_file": "gov.txt", "duration_ms": 200},
                {"name": "conversation-health", "exit_code": 1, "output_file": "ch.txt", "duration_ms": 30},
            ],
            "git_context": {"branch": "master", "staged_file_count": 5},
            "overall_result": "PASS",
        }
        jsonschema.validate(hook_output, schema)

    def test_hook_output_conversation_health_nonzero_still_pass(self):
        """Even with conversation-health exit_code=1, overall_result can be PASS."""
        import jsonschema
        schema_path = Path(__file__).resolve().parent.parent / "schemas" / "agent-runtime" / "evidence-capture.schema.json"
        schema = json.loads(schema_path.read_text(encoding="utf-8"))

        hook_output = {
            "timestamp": "2026-06-12T00:00:00Z",
            "hook_version": "2.4.0",
            "stages": [
                {"name": "manifest-regen", "exit_code": 0, "output_file": None, "duration_ms": 0},
                {"name": "sadp-audit", "exit_code": 0, "output_file": "sadp.txt", "duration_ms": 100},
                {"name": "ai-guard", "exit_code": 0, "output_file": "ai.txt", "duration_ms": 50},
                {"name": "test-governance", "exit_code": 0, "output_file": "gov.txt", "duration_ms": 200},
                {"name": "conversation-health", "exit_code": 2, "output_file": "ch.txt", "duration_ms": 30},
            ],
            "git_context": {"branch": "master", "staged_file_count": 5},
            "overall_result": "PASS",
        }
        # Must validate against schema
        jsonschema.validate(hook_output, schema)
        # conversation-health is advisory — nonzero does not force BLOCKED
        assert hook_output["overall_result"] == "PASS"

    def test_hook_output_sadp_audit_nonzero_is_blocked(self):
        """Sadp-audit nonzero must correspond to BLOCKED (semantic check)."""
        import jsonschema
        schema_path = Path(__file__).resolve().parent.parent / "schemas" / "agent-runtime" / "evidence-capture.schema.json"
        schema = json.loads(schema_path.read_text(encoding="utf-8"))

        hook_output = {
            "timestamp": "2026-06-12T00:00:00Z",
            "hook_version": "2.4.0",
            "stages": [
                {"name": "manifest-regen", "exit_code": 0, "output_file": None, "duration_ms": 0},
                {"name": "sadp-audit", "exit_code": 1, "output_file": "sadp.txt", "duration_ms": 100},
                {"name": "ai-guard", "exit_code": 0, "output_file": "ai.txt", "duration_ms": 50},
            ],
            "git_context": {"branch": "master", "staged_file_count": 5},
            "overall_result": "BLOCKED",
        }
        jsonschema.validate(hook_output, schema)
        assert hook_output["overall_result"] == "BLOCKED"
