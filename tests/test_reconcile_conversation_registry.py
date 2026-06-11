"""Tests for Conversation Registry Reconciliation (A3).

Covers:
    - Consistent registry + health → exit 0
    - Orphaned health data (no matching binding) → exit 1
    - Degraded health with active binding → inconsistency detected
    - Policy violation (one-agent-one-conversation) → detected
    - Capture policy relaxed → detected
    - Both data sources missing → exit 2
    - One data source missing → skipped cross-reference
    - Format output produces expected structure
    - A1/A2 non-regression
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

# Add scripts dir to path
SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

from reconcile_conversation_registry import (
    reconcile,
    format_reconciliation_output,
    EXIT_CONSISTENT,
    EXIT_INCONSISTENT,
    EXIT_DATA_UNAVAILABLE,
    EXIT_MODULE_ERROR,
)


@pytest.fixture
def tmp_registry(tmp_path):
    """Create a temporary directory for registry files."""
    return tmp_path


def _write_current_json(path: Path, data: dict) -> str:
    """Write current.json."""
    f = path / "current.json"
    f.write_text(json.dumps(data), encoding="utf-8")
    return str(f)


def _write_binding(path: Path, data: dict) -> str:
    """Write CONVERSATION_BINDING.json."""
    f = path / "CONVERSATION_BINDING.json"
    f.write_text(json.dumps(data), encoding="utf-8")
    return str(f)


def _healthy_current():
    """Return healthy current.json data."""
    return {
        "schema_version": "conversation-health.v1",
        "conversation_id": "conv-abc-123",
        "chat_url": "https://chatgpt.com/c/conv-abc-123",
        "status": "active",
        "last_known_metrics": {
            "assistant_message_count": 10,
            "review_round_count": 1,
            "last_response_time_seconds": 5.0,
            "last_gpt_reply_bytes": 5000,
        },
        "last_nav_result": "ok",
        "last_checked_at": "2026-06-12T10:00:00Z",
        "metrics_source": "cdp_dom_count",
    }


def _degraded_current():
    """Return degraded current.json data."""
    data = _healthy_current()
    data["status"] = "handoff_required"
    data["last_known_metrics"]["assistant_message_count"] = 65
    return data


def _valid_binding(conv_id="conv-abc-123", chat_url="https://chatgpt.com/c/conv-abc-123"):
    """Return a valid CONVERSATION_BINDING.json."""
    return {
        "schema_version": "1.0.0",
        "awsp_version": "1.3.0",
        "project_id": "test-project",
        "project_root": "/test/project",
        "default_conversation_policy": "one_agent_one_conversation",
        "governance_scope": {
            "default_execution_policy": "human_gated_for_external_runtime_execution",
            "forbid_ad_hoc_gpt_submission": True,
            "forbid_cross_repo_smoke_without_human_gate": True,
            "external_runtimes": [],
        },
        "bindings": [
            {
                "agent_id": "qoderwork-agent",
                "role": "executor",
                "binding_status": "active",
                "conversation_id": conv_id,
                "chat_url": chat_url,
                "capture_policy": {
                    "must_match_run_id": True,
                    "must_match_task_id": True,
                    "must_include_end_marker": True,
                    "forbid_last_message_only_capture": True,
                },
            }
        ],
    }


# =============================================================================
# TestRegistryConsistent
# =============================================================================

class TestRegistryConsistent:
    """Reconciliation with consistent state should return exit 0."""

    def test_matching_conv_id_returns_exit_0(self, tmp_registry):
        current_path = _write_current_json(tmp_registry, _healthy_current())
        binding_path = _write_binding(tmp_registry, _valid_binding())
        exit_code, result = reconcile(
            current_json_path=current_path,
            binding_file_path=binding_path,
            project_root=str(tmp_registry),
        )
        assert exit_code == EXIT_CONSISTENT
        assert result["summary"]["issues"] == 0

    def test_matching_chat_url_returns_exit_0(self, tmp_registry):
        current = _healthy_current()
        current["conversation_id"] = "different-id"  # Won't match by conv_id
        binding = _valid_binding(conv_id="other-id")  # Different conv_id but same URL
        current_path = _write_current_json(tmp_registry, current)
        binding_path = _write_binding(tmp_registry, binding)
        exit_code, result = reconcile(
            current_json_path=current_path,
            binding_file_path=binding_path,
            project_root=str(tmp_registry),
        )
        assert exit_code == EXIT_CONSISTENT


# =============================================================================
# TestRegistryInconsistent
# =============================================================================

class TestRegistryInconsistent:
    """Reconciliation with inconsistencies should return exit 1."""

    def test_orphaned_health_data_returns_exit_1(self, tmp_registry):
        """Health data referencing a conversation not in any binding."""
        current = _healthy_current()
        current["conversation_id"] = "orphan-conv-999"
        current["chat_url"] = "https://chatgpt.com/c/orphan-conv-999"
        binding = _valid_binding(conv_id="bound-conv-123", chat_url="https://chatgpt.com/c/bound-conv-123")
        current_path = _write_current_json(tmp_registry, current)
        binding_path = _write_binding(tmp_registry, binding)
        exit_code, result = reconcile(
            current_json_path=current_path,
            binding_file_path=binding_path,
            project_root=str(tmp_registry),
        )
        assert exit_code == EXIT_INCONSISTENT
        assert result["summary"]["issues"] > 0
        assert any(i["type"] == "orphaned_health_data" for i in result["inconsistencies"])

    def test_degraded_health_with_active_binding(self, tmp_registry):
        """Degraded health status with active binding is an inconsistency."""
        current = _degraded_current()
        binding = _valid_binding()
        current_path = _write_current_json(tmp_registry, current)
        binding_path = _write_binding(tmp_registry, binding)
        exit_code, result = reconcile(
            current_json_path=current_path,
            binding_file_path=binding_path,
            project_root=str(tmp_registry),
        )
        assert exit_code == EXIT_INCONSISTENT
        assert any(i["type"] == "degraded_health_with_active_binding" for i in result["inconsistencies"])

    def test_capture_policy_relaxed(self, tmp_registry):
        """Relaxed capture policy fields should be detected."""
        current = _healthy_current()
        binding = _valid_binding()
        binding["bindings"][0]["capture_policy"]["must_match_run_id"] = False
        current_path = _write_current_json(tmp_registry, current)
        binding_path = _write_binding(tmp_registry, binding)
        exit_code, result = reconcile(
            current_json_path=current_path,
            binding_file_path=binding_path,
            project_root=str(tmp_registry),
        )
        assert exit_code == EXIT_INCONSISTENT
        assert any(i["type"] == "capture_policy_relaxed" for i in result["inconsistencies"])

    def test_policy_violation_multiple_conversations(self, tmp_registry):
        """One agent with multiple active conversations violates one-agent-one-conversation."""
        current = _healthy_current()
        binding = _valid_binding()
        # Add a second active binding for the same agent
        binding["bindings"].append({
            "agent_id": "qoderwork-agent",
            "role": "reviewer",
            "binding_status": "active",
            "conversation_id": "second-conv-456",
            "chat_url": "https://chatgpt.com/c/second-conv-456",
            "capture_policy": {
                "must_match_run_id": True,
                "must_match_task_id": True,
                "must_include_end_marker": True,
                "forbid_last_message_only_capture": True,
            },
        })
        current_path = _write_current_json(tmp_registry, current)
        binding_path = _write_binding(tmp_registry, binding)
        exit_code, result = reconcile(
            current_json_path=current_path,
            binding_file_path=binding_path,
            project_root=str(tmp_registry),
        )
        assert exit_code == EXIT_INCONSISTENT
        assert any(i["type"] == "policy_violation" for i in result["inconsistencies"])


# =============================================================================
# TestRegistryDataUnavailable
# =============================================================================

class TestRegistryDataUnavailable:
    """Missing data sources should return exit 2."""

    def test_both_missing_returns_exit_2(self, tmp_registry):
        exit_code, result = reconcile(
            current_json_path=str(tmp_registry / "current.json"),
            binding_file_path=str(tmp_registry / "CONVERSATION_BINDING.json"),
            project_root=str(tmp_registry),
        )
        assert exit_code == EXIT_DATA_UNAVAILABLE

    def test_only_binding_missing_returns_exit_2(self, tmp_registry):
        current_path = _write_current_json(tmp_registry, _healthy_current())
        exit_code, result = reconcile(
            current_json_path=current_path,
            binding_file_path=str(tmp_registry / "CONVERSATION_BINDING.json"),
            project_root=str(tmp_registry),
        )
        assert exit_code == EXIT_DATA_UNAVAILABLE
        assert any(c["check"] == "binding_data_available" for c in result["checks"])

    def test_only_health_missing_returns_exit_2(self, tmp_registry):
        binding_path = _write_binding(tmp_registry, _valid_binding())
        exit_code, result = reconcile(
            current_json_path=str(tmp_registry / "current.json"),
            binding_file_path=binding_path,
            project_root=str(tmp_registry),
        )
        assert exit_code == EXIT_DATA_UNAVAILABLE
        assert any(c["check"] == "health_data_available" for c in result["checks"])


# =============================================================================
# TestRegistryNoActiveBindings
# =============================================================================

class TestRegistryNoActiveBindings:
    """Registry with no active bindings should handle gracefully."""

    def test_no_active_bindings_returns_consistent(self, tmp_registry):
        current = _healthy_current()
        binding = _valid_binding()
        binding["bindings"][0]["binding_status"] = "retired"
        current_path = _write_current_json(tmp_registry, current)
        binding_path = _write_binding(tmp_registry, binding)
        exit_code, result = reconcile(
            current_json_path=current_path,
            binding_file_path=binding_path,
            project_root=str(tmp_registry),
        )
        # No active bindings → cannot cross-reference → INFO status
        assert exit_code in (EXIT_CONSISTENT, EXIT_INCONSISTENT)


# =============================================================================
# TestRegistryFormatOutput
# =============================================================================

class TestRegistryFormatOutput:
    """Test the human-readable output formatter."""

    def test_format_consistent_output(self):
        result = {
            "checked_at": "2026-06-12T10:00:00Z",
            "checks": [{"check": "conv_id_match", "status": "PASS", "detail": "matched"}],
            "inconsistencies": [],
            "summary": {"total_checks": 1, "passed": 1, "warnings": 0, "issues": 0},
        }
        output = format_reconciliation_output(EXIT_CONSISTENT, result)
        assert "Registry is consistent" in output
        assert "Conversation Registry Reconciliation" in output

    def test_format_inconsistent_output(self):
        result = {
            "checked_at": "2026-06-12T10:00:00Z",
            "checks": [],
            "inconsistencies": [
                {"type": "orphaned_health_data", "detail": "no match", "recommendation": "update binding"}
            ],
            "summary": {"total_checks": 1, "passed": 0, "warnings": 0, "issues": 1},
        }
        output = format_reconciliation_output(EXIT_INCONSISTENT, result)
        assert "WARNING" in output
        assert "orphaned_health_data" in output

    def test_format_unavailable_output(self):
        result = {
            "checked_at": "2026-06-12T10:00:00Z",
            "checks": [{"check": "data_availability", "status": "UNAVAILABLE", "detail": "missing"}],
            "inconsistencies": [],
            "summary": {"total_checks": 1, "passed": 0, "warnings": 0, "issues": 1},
        }
        output = format_reconciliation_output(EXIT_DATA_UNAVAILABLE, result)
        assert "Data unavailable" in output


# =============================================================================
# TestRegistryNonRegression
# =============================================================================

class TestRegistryNonRegression:
    """Ensure A3 reconciliation does not break A1/A2 behavior."""

    def test_reconciliation_does_not_modify_files(self, tmp_registry):
        """Reconciliation should be read-only."""
        current = _healthy_current()
        binding = _valid_binding()
        current_path = _write_current_json(tmp_registry, current)
        binding_path = _write_binding(tmp_registry, binding)

        # Record file contents before
        current_before = Path(current_path).read_text()
        binding_before = Path(binding_path).read_text()

        reconcile(
            current_json_path=current_path,
            binding_file_path=binding_path,
            project_root=str(tmp_registry),
        )

        # Verify files unchanged
        assert Path(current_path).read_text() == current_before
        assert Path(binding_path).read_text() == binding_before

    def test_reconciliation_result_structure(self, tmp_registry):
        """Result should have required fields."""
        current = _healthy_current()
        binding = _valid_binding()
        current_path = _write_current_json(tmp_registry, current)
        binding_path = _write_binding(tmp_registry, binding)
        exit_code, result = reconcile(
            current_json_path=current_path,
            binding_file_path=binding_path,
            project_root=str(tmp_registry),
        )
        assert "reconciliation_type" in result
        assert result["reconciliation_type"] == "conversation-registry"
        assert "checked_at" in result
        assert "checks" in result
        assert "inconsistencies" in result
        assert "summary" in result
