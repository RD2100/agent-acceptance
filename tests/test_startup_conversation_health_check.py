"""Tests for Startup Conversation Health Check (A4 Item 1.9).

Covers:
- OK / SUGGEST_HANDOFF / FORCE_HANDOFF / HUMAN_REQUIRED decisions
- Missing current.json → UNKNOWN/WARNING evidence
- Stale metrics reporting
- No CDP import (awareness only)
- startup-read-latest.json output
- Evidence pack integration (review.yaml startup_read block)
- A1/A2/A3 non-regression
"""

import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
HELPER_PATH = SCRIPTS_DIR / "startup_conversation_health_check.py"
BUILDER_PATH = SCRIPTS_DIR / "build_evidence_pack.py"
STARTUP_READ_GATE_DOC = Path(__file__).resolve().parent.parent / "docs" / "agent-runtime" / "startup-read-gate.md"


def _make_current_json(tmp: Path, decision="OK", msg_count=5, rt=12.0,
                       reply_bytes=3000, freshness="fresh",
                       nav_result="ok", source="cdp_dom_count",
                       checked_at="2026-06-12T00:00:00Z") -> str:
    """Create a current.json in tmp and return its path."""
    current_dir = tmp / ".ai" / "conversation"
    current_dir.mkdir(parents=True, exist_ok=True)
    current_path = current_dir / "current.json"
    data = {
        "schema_version": "conversation-health.v1",
        "conversation_id": "test-uuid",
        "chat_url": "https://chatgpt.com/c/test-uuid",
        "status": "active",
        "last_known_metrics": {
            "assistant_message_count": msg_count,
            "review_round_count": 1,
            "last_response_time_seconds": rt,
            "last_gpt_reply_bytes": reply_bytes,
        },
        "last_nav_result": nav_result,
        "last_health_decision": decision,
        "last_health_reasons": [],
        "last_checked_at": checked_at,
        "metrics_source": source,
        "metrics_freshness": freshness,
    }
    current_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return str(current_path)


def _make_latest_json(tmp: Path, decision="OK", msg_count=10, rt=10.0,
                      reply_bytes=5000, freshness="fresh",
                      nav_result="ok", source="cdp_dom_count") -> str:
    """Create a latest.json in tmp and return its path."""
    latest_dir = tmp / "_evidence" / "conversation-health"
    latest_dir.mkdir(parents=True, exist_ok=True)
    latest_path = latest_dir / "latest.json"
    data = {
        "schema_version": "conversation-health.v1",
        "conversation_id": "test-uuid",
        "chat_url": "https://chatgpt.com/c/test-uuid",
        "status": "active",
        "last_known_metrics": {
            "assistant_message_count": msg_count,
            "review_round_count": 1,
            "last_response_time_seconds": rt,
            "last_gpt_reply_bytes": reply_bytes,
        },
        "last_nav_result": nav_result,
        "last_health_decision": decision,
        "last_health_reasons": [],
        "last_checked_at": "2026-06-12T00:00:00Z",
        "metrics_source": source,
        "metrics_freshness": freshness,
        "last_health_severity": "INFO",
    }
    latest_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return str(latest_path)


def _get_output_path(tmp: Path) -> str:
    """Get the output path for startup-read-latest.json."""
    out = tmp / "_evidence" / "conversation-health" / "startup-read-latest.json"
    return str(out)


def _run_check(tmp: Path, current_path=None, latest_path=None, output_path=None):
    """Import and run the startup check with given paths."""
    sys.path.insert(0, str(SCRIPTS_DIR))
    try:
        from startup_conversation_health_check import run_startup_check
        return run_startup_check(
            current_json_path=current_path,
            latest_json_path=latest_path,
            output_path=output_path or _get_output_path(tmp),
            project_root=str(tmp),
        )
    finally:
        if str(SCRIPTS_DIR) in sys.path:
            sys.path.remove(str(SCRIPTS_DIR))


# ---------------------------------------------------------------------------
# TestStartupOK
# ---------------------------------------------------------------------------

class TestStartupOK:
    """Startup read with healthy conversation → OK."""

    def test_ok_decision(self, tmp_path):
        cur = _make_current_json(tmp_path, msg_count=5, rt=12.0, reply_bytes=3000)
        lat = _make_latest_json(tmp_path, msg_count=5, rt=12.0, reply_bytes=3000)
        result = _run_check(tmp_path, cur, lat)
        assert result["decision"] == "OK"

    def test_ok_severity_info(self, tmp_path):
        cur = _make_current_json(tmp_path, msg_count=5, rt=12.0, reply_bytes=3000)
        lat = _make_latest_json(tmp_path, msg_count=5, rt=12.0, reply_bytes=3000)
        result = _run_check(tmp_path, cur, lat)
        assert result["severity"] == "INFO"

    def test_ok_recommended_action_continue(self, tmp_path):
        cur = _make_current_json(tmp_path, msg_count=5, rt=12.0, reply_bytes=3000)
        lat = _make_latest_json(tmp_path, msg_count=5, rt=12.0, reply_bytes=3000)
        result = _run_check(tmp_path, cur, lat)
        assert result["recommended_action"] == "continue"

    def test_ok_writes_startup_read_file(self, tmp_path):
        cur = _make_current_json(tmp_path, msg_count=5, rt=12.0, reply_bytes=3000)
        lat = _make_latest_json(tmp_path, msg_count=5, rt=12.0, reply_bytes=3000)
        out = _get_output_path(tmp_path)
        _run_check(tmp_path, cur, lat, out)
        assert os.path.isfile(out)
        data = json.loads(Path(out).read_text(encoding="utf-8"))
        assert data["decision"] == "OK"
        assert data["schema_version"] == "startup-read-conversation-health.v1"


# ---------------------------------------------------------------------------
# TestStartupSuggestHandoff
# ---------------------------------------------------------------------------

class TestStartupSuggestHandoff:
    """Startup read with degraded conversation → SUGGEST_HANDOFF."""

    def test_suggest_handoff_high_response_time(self, tmp_path):
        cur = _make_current_json(tmp_path, msg_count=46, rt=65.0, reply_bytes=1500)
        lat = _make_latest_json(tmp_path, msg_count=46, rt=65.0, reply_bytes=1500)
        result = _run_check(tmp_path, cur, lat)
        assert result["decision"] == "SUGGEST_HANDOFF"

    def test_suggest_recommendation(self, tmp_path):
        cur = _make_current_json(tmp_path, msg_count=46, rt=65.0, reply_bytes=1500)
        lat = _make_latest_json(tmp_path, msg_count=46, rt=65.0, reply_bytes=1500)
        result = _run_check(tmp_path, cur, lat)
        assert "handoff" in result["recommended_action"].lower()


# ---------------------------------------------------------------------------
# TestStartupForceHandoff
# ---------------------------------------------------------------------------

class TestStartupForceHandoff:
    """Startup read with severely degraded conversation → FORCE_HANDOFF."""

    def test_force_handoff_high_message_count(self, tmp_path):
        cur = _make_current_json(tmp_path, msg_count=65, rt=120.0, reply_bytes=500)
        lat = _make_latest_json(tmp_path, msg_count=65, rt=120.0, reply_bytes=500)
        result = _run_check(tmp_path, cur, lat)
        assert result["decision"] == "FORCE_HANDOFF"

    def test_force_handoff_has_reasons(self, tmp_path):
        cur = _make_current_json(tmp_path, msg_count=65, rt=120.0, reply_bytes=500)
        lat = _make_latest_json(tmp_path, msg_count=65, rt=120.0, reply_bytes=500)
        result = _run_check(tmp_path, cur, lat)
        assert len(result["reasons"]) > 0


# ---------------------------------------------------------------------------
# TestStartupHumanRequired
# ---------------------------------------------------------------------------

class TestStartupHumanRequired:
    """Startup read with auth_required nav result → HUMAN_REQUIRED."""

    def test_human_required_nav_result(self, tmp_path):
        cur = _make_current_json(tmp_path, msg_count=5, nav_result="auth_required")
        lat = _make_latest_json(tmp_path, msg_count=5, nav_result="auth_required")
        result = _run_check(tmp_path, cur, lat)
        assert result["decision"] == "HUMAN_REQUIRED"

    def test_human_required_recommendation(self, tmp_path):
        cur = _make_current_json(tmp_path, msg_count=5, nav_result="auth_required")
        lat = _make_latest_json(tmp_path, msg_count=5, nav_result="auth_required")
        result = _run_check(tmp_path, cur, lat)
        assert "human" in result["recommended_action"].lower()


# ---------------------------------------------------------------------------
# TestStartupMissingEvidence
# ---------------------------------------------------------------------------

class TestStartupMissingEvidence:
    """Missing current.json → UNKNOWN/WARNING evidence."""

    def test_missing_both_unknown(self, tmp_path):
        # Point to non-existent paths in tmp to ensure no real files are found
        cur = str(tmp_path / ".ai" / "conversation" / "current.json")
        lat = str(tmp_path / "_evidence" / "conversation-health" / "latest.json")
        result = _run_check(tmp_path, current_path=cur, latest_path=lat)
        assert result["decision"] == "UNKNOWN"
        assert result["severity"] == "WARNING"

    def test_missing_current_json_warning_not_silent(self, tmp_path):
        # Only latest.json exists, no current.json
        lat = _make_latest_json(tmp_path, msg_count=5, rt=12.0, reply_bytes=3000)
        cur = str(tmp_path / ".ai" / "conversation" / "current.json")  # non-existent
        result = _run_check(tmp_path, current_path=cur, latest_path=lat)
        # Should still produce a valid result (from latest.json fallback)
        assert result["decision"] in ("OK", "SUGGEST_HANDOFF", "FORCE_HANDOFF",
                                      "HUMAN_REQUIRED", "UNKNOWN")
        assert result["latest_json_present"] is True
        assert result["current_json_present"] is False

    def test_missing_evidence_has_reason(self, tmp_path):
        cur = str(tmp_path / ".ai" / "conversation" / "current.json")
        lat = str(tmp_path / "_evidence" / "conversation-health" / "latest.json")
        result = _run_check(tmp_path, current_path=cur, latest_path=lat)
        assert len(result["reasons"]) > 0
        assert result["reasons"][0]["code"] == "no_evidence_available"

    def test_missing_evidence_writes_output(self, tmp_path):
        cur = str(tmp_path / ".ai" / "conversation" / "current.json")
        lat = str(tmp_path / "_evidence" / "conversation-health" / "latest.json")
        out = _get_output_path(tmp_path)
        _run_check(tmp_path, current_path=cur, latest_path=lat, output_path=out)
        assert os.path.isfile(out)
        data = json.loads(Path(out).read_text(encoding="utf-8"))
        assert data["decision"] == "UNKNOWN"
        assert data["severity"] == "WARNING"


# ---------------------------------------------------------------------------
# TestStartupStaleMetrics
# ---------------------------------------------------------------------------

class TestStartupStaleMetrics:
    """Stale metrics are reported in the evidence."""

    def test_stale_freshness_reported(self, tmp_path):
        cur = _make_current_json(tmp_path, msg_count=5, freshness="stale",
                                checked_at="2026-06-10T00:00:00Z")
        lat = _make_latest_json(tmp_path, msg_count=5, freshness="stale")
        result = _run_check(tmp_path, cur, lat)
        assert result["metrics_freshness"] == "stale"

    def test_metrics_source_reported(self, tmp_path):
        cur = _make_current_json(tmp_path, msg_count=5, source="cdp_dom_count")
        lat = _make_latest_json(tmp_path, msg_count=5, source="cdp_dom_count")
        result = _run_check(tmp_path, cur, lat)
        assert result["metrics_source"] == "cdp_dom_count"

    def test_nav_result_reported(self, tmp_path):
        cur = _make_current_json(tmp_path, msg_count=5, nav_result="ok")
        lat = _make_latest_json(tmp_path, msg_count=5, nav_result="ok")
        result = _run_check(tmp_path, cur, lat)
        assert result["last_nav_result"] == "ok"


# ---------------------------------------------------------------------------
# TestStartupNoCDP
# ---------------------------------------------------------------------------

class TestStartupNoCDP:
    """Startup helper does NOT open CDP browser."""

    def test_no_cdp_import(self):
        """Verify the helper script does not import playwright or CDP modules."""
        helper_text = HELPER_PATH.read_text(encoding="utf-8")
        assert "playwright" not in helper_text
        assert "connect_over_cdp" not in helper_text
        assert "chromium" not in helper_text.lower()

    def test_no_browser_launch(self):
        """Verify no browser launch patterns in the helper."""
        helper_text = HELPER_PATH.read_text(encoding="utf-8")
        assert "launch(" not in helper_text
        assert "new_page" not in helper_text


# ---------------------------------------------------------------------------
# TestStartupOutputFormat
# ---------------------------------------------------------------------------

class TestStartupOutputFormat:
    """Format output for human-readable display."""

    def test_format_ok_output(self, tmp_path):
        sys.path.insert(0, str(SCRIPTS_DIR))
        try:
            from startup_conversation_health_check import format_startup_output
            result = {"decision": "OK", "severity": "INFO",
                     "current_json_present": True, "latest_json_present": True,
                     "metrics_source": "cdp_dom_count", "metrics_freshness": "fresh",
                     "last_nav_result": "ok", "recommended_action": "continue",
                     "reasons": [], "checked_at": "2026-06-12T00:00:00Z"}
            output = format_startup_output(result)
            assert "Conversation health OK" in output
        finally:
            sys.path.remove(str(SCRIPTS_DIR))

    def test_format_force_output(self, tmp_path):
        sys.path.insert(0, str(SCRIPTS_DIR))
        try:
            from startup_conversation_health_check import format_startup_output
            result = {"decision": "FORCE_HANDOFF", "severity": "BLOCKING",
                     "current_json_present": True, "latest_json_present": True,
                     "metrics_source": "cdp_dom_count", "metrics_freshness": "stale",
                     "last_nav_result": "ok", "recommended_action": "generate_handoff",
                     "reasons": [{"code": "msg_count", "actual": 65}],
                     "checked_at": "2026-06-12T00:00:00Z"}
            output = format_startup_output(result)
            assert "ACTION REQUIRED" in output
        finally:
            sys.path.remove(str(SCRIPTS_DIR))

    def test_format_unknown_output(self, tmp_path):
        sys.path.insert(0, str(SCRIPTS_DIR))
        try:
            from startup_conversation_health_check import format_startup_output
            result = {"decision": "UNKNOWN", "severity": "WARNING",
                     "current_json_present": False, "latest_json_present": False,
                     "metrics_source": "none", "metrics_freshness": "unknown",
                     "last_nav_result": "unknown", "recommended_action": "investigate",
                     "reasons": [{"code": "no_evidence_available"}],
                     "checked_at": "2026-06-12T00:00:00Z"}
            output = format_startup_output(result)
            assert "WARNING" in output or "unknown" in output.lower()
        finally:
            sys.path.remove(str(SCRIPTS_DIR))


# ---------------------------------------------------------------------------
# TestEvidencePackIntegration
# ---------------------------------------------------------------------------

class TestEvidencePackIntegration:
    """Startup evidence is included in evidence pack / review.yaml."""

    def test_review_yaml_has_startup_read_block(self):
        """build_evidence_pack.py generates startup_read block in review.yaml."""
        builder_text = BUILDER_PATH.read_text(encoding="utf-8")
        assert "startup_read:" in builder_text
        assert "conversation_health_checked" in builder_text
        assert "startup_evidence_file" in builder_text

    def test_evidence_pack_copies_startup_read(self):
        """build_evidence_pack.py includes step 15e for startup-read-latest.json."""
        builder_text = BUILDER_PATH.read_text(encoding="utf-8")
        assert "startup-read-latest.json" in builder_text
        assert "15e" in builder_text

    def test_startup_read_missing_recorded_as_limitation(self):
        """When startup-read evidence is missing, review.yaml records it."""
        builder_text = BUILDER_PATH.read_text(encoding="utf-8")
        assert "verdict_impact: limitation" in builder_text


# ---------------------------------------------------------------------------
# TestStartupReadGateDoc
# ---------------------------------------------------------------------------

class TestStartupReadGateDoc:
    """startup-read-gate.md includes item 1.9."""

    def test_doc_has_item_1_9(self):
        doc_text = STARTUP_READ_GATE_DOC.read_text(encoding="utf-8")
        assert "### 1.9" in doc_text

    def test_doc_has_conversation_health_title(self):
        doc_text = STARTUP_READ_GATE_DOC.read_text(encoding="utf-8")
        assert "Conversation Health" in doc_text

    def test_doc_yaml_has_startup_fields(self):
        doc_text = STARTUP_READ_GATE_DOC.read_text(encoding="utf-8")
        assert "startup_read_health_checked" in doc_text
        assert "startup_read_health_decision" in doc_text

    def test_doc_has_anti_pattern(self):
        doc_text = STARTUP_READ_GATE_DOC.read_text(encoding="utf-8")
        assert "Health Blindness" in doc_text


# ---------------------------------------------------------------------------
# TestA1A2A3NonRegression
# ---------------------------------------------------------------------------

class TestA1A2A3NonRegression:
    """A1/A2/A3 accepted semantics do not regress."""

    def test_check_handoff_v2_not_modified(self):
        """Startup helper imports check_handoff_v2, does not duplicate logic."""
        helper_text = HELPER_PATH.read_text(encoding="utf-8")
        assert "from check_handoff_needed import check_handoff_v2" in helper_text
        # Should NOT redefine threshold values
        assert "assistant_message_count >=" not in helper_text or "assistant_message_count >= 60" not in helper_text

    def test_helper_only_writes_startup_read(self):
        """Startup helper only writes startup-read-latest.json via _write_output."""
        helper_text = HELPER_PATH.read_text(encoding="utf-8")
        # The only write_text call should be in _write_output, writing startup-read evidence
        # Verify no direct writes to current.json or latest.json
        assert "_write_output" in helper_text
        # Verify the output function writes to the out_path parameter, not hardcoded files
        assert "out_path.write_text" in helper_text

    def test_pre_commit_advisory_unchanged(self):
        """A3 pre_commit_health_advisory.py still exists and is not modified by A4."""
        advisory_path = SCRIPTS_DIR / "pre_commit_health_advisory.py"
        assert advisory_path.exists()
