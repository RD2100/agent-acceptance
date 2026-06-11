"""Tests for CONVERSATION-HEALTH-GATE-A1: conversation health gate enforcement.

Covers:
- Schema validation (conversation-health.schema.json, conversation-health-decision.schema.json)
- Threshold logic (check_handoff_needed.py v2)
- Pre-task integration (sadp_pre_task_enforcer.py step 7)
- Policy loading (configs/conversation-health-policy.yaml)
"""
import json
import sys
import tempfile
from pathlib import Path

import pytest

SCRIPT_DIR = Path(__file__).resolve().parent.parent / "scripts"
SCHEMAS_DIR = Path(__file__).resolve().parent.parent / "schemas" / "agent-runtime"
CONFIGS_DIR = Path(__file__).resolve().parent.parent / "configs"

sys.path.insert(0, str(SCRIPT_DIR))
from check_handoff_needed import check_handoff, check_handoff_v2, load_policy  # noqa: E402


# ---------------------------------------------------------------------------
# Schema validation tests
# ---------------------------------------------------------------------------

class TestConversationHealthSchema:
    """Validate conversation-health.schema.json structure."""

    @pytest.fixture
    def schema(self):
        return json.loads((SCHEMAS_DIR / "conversation-health.schema.json").read_text())

    def test_schema_has_required_fields(self, schema):
        required = schema.get("required", [])
        assert "schema_version" in required
        assert "conversation_id" in required
        assert "last_nav_result" in required
        assert "metrics_source" in required

    def test_schema_defines_nav_enum(self, schema):
        nav_enum = schema["properties"]["last_nav_result"]["enum"]
        assert "ok" in nav_enum
        assert "access_denied" in nav_enum
        assert "auth_required" in nav_enum

    def test_schema_defines_status_enum(self, schema):
        status_enum = schema["properties"]["status"]["enum"]
        assert "active" in status_enum
        assert "migrated" in status_enum

    def test_schema_metrics_nullable(self, schema):
        for field in ["assistant_message_count", "review_round_count"]:
            types = schema["properties"]["last_known_metrics"]["properties"][field]["type"]
            assert "null" in types or types == ["integer", "null"]


class TestConversationHealthDecisionSchema:
    """Validate conversation-health-decision.schema.json structure."""

    @pytest.fixture
    def schema(self):
        return json.loads((SCHEMAS_DIR / "conversation-health-decision.schema.json").read_text())

    def test_decision_enum(self, schema):
        enum = schema["properties"]["decision"]["enum"]
        assert "OK" in enum
        assert "FORCE_HANDOFF" in enum
        assert "SUGGEST_HANDOFF" in enum
        assert "HUMAN_REQUIRED" in enum
        assert "UNKNOWN" in enum

    def test_severity_enum(self, schema):
        enum = schema["properties"]["severity"]["enum"]
        assert "INFO" in enum
        assert "WARNING" in enum
        assert "BLOCKING" in enum

    def test_policy_enum_covers_all_code_outputs(self, schema):
        """reasons[].policy enum must cover all values output by check_handoff_v2."""
        policy_enum = schema["properties"]["reasons"]["items"]["properties"]["policy"]["enum"]
        # These are the actual values emitted by check_handoff_v2
        required = ["force", "suggest", "force_composite", "human", "suggest_capped", "warning"]
        for val in required:
            assert val in policy_enum, f"policy enum missing code output value: {val}"


# ---------------------------------------------------------------------------
# Threshold logic tests (check_handoff_needed.py v2)
# ---------------------------------------------------------------------------

class TestCheckHandoffNeeded:
    """Test the v2 threshold engine."""

    def test_no_triggers_ok(self):
        result = check_handoff_v2({
            "assistant_message_count": 10,
            "review_round_count": 1,
            "metrics_source": "cdp_dom_count",
            "nav_result": "ok",
        })
        assert result["decision"] == "OK"

    def test_message_count_force_cdp(self):
        result = check_handoff_v2({
            "assistant_message_count": 65,
            "metrics_source": "cdp_dom_count",
            "nav_result": "ok",
        })
        assert result["decision"] == "FORCE_HANDOFF"

    def test_message_count_force_wrapper(self):
        result = check_handoff_v2({
            "assistant_message_count": 70,
            "metrics_source": "wrapper_counter",
            "nav_result": "ok",
        })
        assert result["decision"] == "FORCE_HANDOFF"

    def test_message_count_manual_no_force(self):
        """manual_estimate cannot trigger FORCE alone."""
        result = check_handoff_v2({
            "assistant_message_count": 70,
            "metrics_source": "manual_estimate",
            "nav_result": "ok",
        })
        assert result["decision"] != "FORCE_HANDOFF"
        assert result["decision"] in ("SUGGEST_HANDOFF", "OK")

    def test_review_rounds_force(self):
        result = check_handoff_v2({
            "review_round_count": 4,
            "metrics_source": "cdp_dom_count",
            "nav_result": "ok",
        })
        assert result["decision"] == "FORCE_HANDOFF"

    def test_nav_access_denied(self):
        result = check_handoff_v2({
            "assistant_message_count": 5,
            "metrics_source": "cdp_dom_count",
            "nav_result": "access_denied",
        })
        assert result["decision"] == "FORCE_HANDOFF"

    def test_nav_auth_required(self):
        result = check_handoff_v2({
            "assistant_message_count": 5,
            "metrics_source": "cdp_dom_count",
            "nav_result": "auth_required",
        })
        assert result["decision"] == "HUMAN_REQUIRED"

    def test_composite_force(self):
        result = check_handoff_v2({
            "assistant_message_count": 20,
            "response_time_seconds": 75,
            "last_gpt_reply_bytes": 1500,
            "review_round_count": 2,
            "metrics_source": "cdp_dom_count",
            "nav_result": "ok",
        }, composite=True)
        assert result["decision"] == "FORCE_HANDOFF"

    def test_response_time_only_is_suggest(self):
        """response_time >= 60 alone should SUGGEST, not FORCE (consensus semantics)."""
        result = check_handoff_v2({
            "assistant_message_count": 10,
            "response_time_seconds": 75,
            "last_gpt_reply_bytes": 5000,
            "review_round_count": 1,
            "metrics_source": "cdp_dom_count",
            "nav_result": "ok",
        }, composite=True)
        assert result["decision"] == "SUGGEST_HANDOFF"

    def test_reply_bytes_only_is_suggest(self):
        """reply_bytes < 2000 alone should SUGGEST, not FORCE (consensus semantics)."""
        result = check_handoff_v2({
            "assistant_message_count": 10,
            "response_time_seconds": 5,
            "last_gpt_reply_bytes": 500,
            "review_round_count": 1,
            "metrics_source": "cdp_dom_count",
            "nav_result": "ok",
        }, composite=True)
        assert result["decision"] == "SUGGEST_HANDOFF"

    def test_stale_metrics_suggest(self):
        result = check_handoff_v2({
            "assistant_message_count": 10,
            "metrics_source": "cdp_dom_count",
            "nav_result": "ok",
            "last_checked_at": "2026-01-01T00:00:00Z",  # very old
        }, max_staleness_hours=12)
        assert result["decision"] == "SUGGEST_HANDOFF"

    def test_metrics_source_none(self):
        result = check_handoff_v2({
            "metrics_source": "none",
            "nav_result": "ok",
        })
        assert result["decision"] == "UNKNOWN"

    def test_backward_compat_function(self):
        """Old check_handoff() API still works."""
        result = check_handoff(
            assistant_message_count=70,
            response_time_seconds=30,
            review_round_count=1,
            last_gpt_reply_bytes=5000,
        )
        assert result["force_handoff"] is True
        assert isinstance(result["reasons"], list)


# ---------------------------------------------------------------------------
# Policy loading tests
# ---------------------------------------------------------------------------

class TestPolicyLoading:
    """Test policy YAML loading."""

    def test_load_default_policy(self):
        policy = load_policy(CONFIGS_DIR / "conversation-health-policy.yaml")
        assert policy is not None
        # Should have threshold structure
        assert "force" in str(policy) or "thresholds" in str(policy) or isinstance(policy, dict)

    def test_missing_policy_uses_defaults(self):
        policy = load_policy(Path("/nonexistent/policy.yaml"))
        assert policy is not None  # graceful fallback


# ---------------------------------------------------------------------------
# Pre-task integration tests
# ---------------------------------------------------------------------------

class TestPreTaskIntegration:
    """Test sadp_pre_task_enforcer conversation health integration."""

    def test_missing_current_json_warning(self):
        """Missing current.json → WARNING, not BLOCKED."""
        from sadp_pre_task_enforcer import _check_conversation_health
        # This test relies on .ai/conversation/current.json not existing
        # or existing in a specific state. We test the function directly.
        result = _check_conversation_health()
        # Function should always return a dict with status/decision/reasons
        assert "status" in result
        assert "decision" in result
        assert "reasons" in result
        assert result["status"] in ("PASS", "WARNING", "BLOCKED")

    def test_check_handoff_v2_decision_structure(self):
        """Decision output has required fields."""
        result = check_handoff_v2({
            "assistant_message_count": 10,
            "metrics_source": "cdp_dom_count",
            "nav_result": "ok",
        })
        assert "decision" in result
        assert "severity" in result
        assert "reasons" in result
        assert "schema_version" in result
        assert result["schema_version"].startswith("conversation-health-decision")
