"""Tests for SHARED-CDP-DISPATCH-PACKET-V2-A1 — v2 dispatch packet structure.

Tests cover:
  1. v2 packet fields (target_id, capture_policy, isolation_model, etc.)
  2. Non-dispatchable targets produce correct error packets
  3. Dispatch mode propagation
"""

import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

REPO = Path(__file__).resolve().parent.parent
SCRIPTS = REPO / "scripts"
sys.path.insert(0, str(SCRIPTS))

import multi_project_router as router


# ── Fixtures ──────────────────────────────────────────────────────────


def _make_v2_target(overrides: dict | None = None) -> dict:
    """Build a fully-resolved v2 target."""
    target = {
        "project_id": "proj-test",
        "resolved": True,
        "cdp_endpoint": "http://localhost:9222",
        "cdp_active": True,
        "conversation_id": "conv-test-001",
        "chat_url": "https://chatgpt.com/c/conv-test-001",
        "target_id": "cdp-target-abc123",
        "target_url": "https://chatgpt.com/c/conv-test-001",
        "tab_match_status": "exact_match",
        "agent_id": "agent-test-001",
        "agent_role": "executor",
        "binding_status": "active",
        "capture_policy": {
            "must_match_run_id": True,
            "must_match_task_id": True,
            "must_include_end_marker": True,
            "forbid_last_message_only_capture": True,
        },
    }
    if overrides:
        target.update(overrides)
    return target


# ── 1. v2 Packet Fields ─────────────────────────────────────────────


class TestV2PacketFields:
    """Verify v2 dispatch packet contains all required fields."""

    def test_packet_has_target_id(self):
        target = _make_v2_target()
        packet = router.build_dispatch_packet(
            target, {"task_id": "T001"}, "Test message"
        )
        assert packet["dispatchable"] is True
        assert packet["target_id"] == "cdp-target-abc123"

    def test_packet_has_target_url(self):
        target = _make_v2_target()
        packet = router.build_dispatch_packet(
            target, {"task_id": "T001"}, "Test message"
        )
        assert packet["target_url"] == "https://chatgpt.com/c/conv-test-001"

    def test_packet_has_tab_match_status(self):
        target = _make_v2_target()
        packet = router.build_dispatch_packet(
            target, {"task_id": "T001"}, "Test message"
        )
        assert packet["tab_match_status"] == "exact_match"

    def test_packet_has_capture_policy(self):
        target = _make_v2_target()
        packet = router.build_dispatch_packet(
            target, {"task_id": "T001"}, "Test message"
        )
        cp = packet["capture_policy"]
        assert cp["must_match_run_id"] is True
        assert cp["must_match_task_id"] is True
        assert cp["must_include_end_marker"] is True
        assert cp["forbid_last_message_only_capture"] is True

    def test_packet_has_expected_identifiers(self):
        target = _make_v2_target()
        task_spec = {"task_id": "T001", "run_id": "RUN-001"}
        packet = router.build_dispatch_packet(target, task_spec, "msg")
        assert packet["expected_task_id"] == "T001"
        assert packet["expected_run_id"] == "RUN-001"
        assert packet["expected_end_marker"] == "END_OF_GPT_RESPONSE"
        assert packet["forbid_last_message_only_capture"] is True

    def test_packet_has_architecture_metadata(self):
        target = _make_v2_target()
        packet = router.build_dispatch_packet(
            target, {"task_id": "T001"}, "msg"
        )
        assert packet["cdp_mode"] == "shared_single_chrome"
        assert packet["isolation_model"] == "conversation_target_bound"

    def test_packet_dispatch_mode_default(self):
        target = _make_v2_target()
        packet = router.build_dispatch_packet(
            target, {"task_id": "T001"}, "msg"
        )
        assert packet["dispatch_mode"] == "dry_run"

    def test_packet_dispatch_mode_live(self):
        target = _make_v2_target()
        packet = router.build_dispatch_packet(
            target, {"task_id": "T001"}, "msg",
            dispatch_mode="human_gated_live",
        )
        assert packet["dispatch_mode"] == "human_gated_live"

    def test_packet_core_fields_preserved(self):
        """v1 fields should still be present for backward compatibility."""
        target = _make_v2_target()
        packet = router.build_dispatch_packet(
            target, {"task_id": "T001"}, "Execute task"
        )
        assert packet["project_id"] == "proj-test"
        assert packet["cdp_endpoint"] == "http://localhost:9222"
        assert packet["conversation_id"] == "conv-test-001"
        assert packet["chat_url"] == "https://chatgpt.com/c/conv-test-001"
        assert packet["agent_id"] == "agent-test-001"
        assert packet["task_spec"]["task_id"] == "T001"
        assert packet["message_text"] == "Execute task"
        assert packet["message_length"] == len("Execute task")
        assert "built_at" in packet


# ── 2. Non-Dispatchable Targets ──────────────────────────────────────


class TestNonDispatchable:
    """Non-resolved targets should produce non-dispatchable packets."""

    def test_unresolved_target(self):
        target = {"project_id": "fake", "resolved": False, "error": "Not found"}
        packet = router.build_dispatch_packet(target, {"task_id": "T001"}, "msg")
        assert packet["dispatchable"] is False
        assert "error" in packet

    def test_no_target_id_blocked_by_fail_closed(self):
        """v2 FAIL-CLOSED: target_id=None with tab_match_status != exact_match -> blocked."""
        target = _make_v2_target({"target_id": None, "tab_match_status": "no_match"})
        packet = router.build_dispatch_packet(target, {"task_id": "T001"}, "msg")
        assert packet["dispatchable"] is False
        assert packet.get("blocked_reason") == "tab_match_status_not_exact"

    def test_no_target_id_exact_match_blocked(self):
        """v2 FAIL-CLOSED: even with exact_match, missing target_id -> blocked."""
        target = _make_v2_target({"target_id": None, "tab_match_status": "exact_match"})
        packet = router.build_dispatch_packet(target, {"task_id": "T001"}, "msg")
        assert packet["dispatchable"] is False
        assert packet.get("blocked_reason") == "missing_target_id"

    def test_no_target_url_blocked(self):
        """v2 FAIL-CLOSED: missing target_url -> blocked."""
        target = _make_v2_target({
            "target_id": "some-id",
            "target_url": None,
            "tab_match_status": "exact_match",
        })
        packet = router.build_dispatch_packet(target, {"task_id": "T001"}, "msg")
        assert packet["dispatchable"] is False
        assert packet.get("blocked_reason") == "missing_target_url"

    def test_ambiguous_tab_blocked_by_fail_closed(self):
        """v2 FAIL-CLOSED (T-001): ambiguous tab_match_status -> blocked at packet level."""
        target = _make_v2_target({"tab_match_status": "ambiguous", "target_id": None})
        packet = router.build_dispatch_packet(target, {"task_id": "T001"}, "msg")
        assert packet["dispatchable"] is False
        assert packet.get("blocked_reason") == "tab_match_status_not_exact"

    def test_pending_project_not_resolved(self):
        """Pending projects don't resolve -> non-dispatchable."""
        with patch.object(router, "_check_cdp", return_value=False):
            target = router.resolve_target("project-alpha")
        assert target["resolved"] is False
        packet = router.build_dispatch_packet(target, {"task_id": "T001"}, "msg")
        assert packet["dispatchable"] is False


# ── 3. Capture Policy ────────────────────────────────────────────────


class TestCapturePolicy:
    """Test capture policy handling in dispatch packets."""

    def test_default_capture_policy_when_missing(self):
        """If target has no capture_policy, defaults are used."""
        target = _make_v2_target({"capture_policy": None})
        packet = router.build_dispatch_packet(target, {"task_id": "T001"}, "msg")
        cp = packet["capture_policy"]
        assert cp["must_match_run_id"] is True
        assert cp["forbid_last_message_only_capture"] is True

    def test_capture_policy_from_binding(self):
        """Capture policy from binding should propagate to packet."""
        target = _make_v2_target({
            "capture_policy": {
                "must_match_run_id": True,
                "must_match_task_id": False,
                "must_include_end_marker": True,
                "forbid_last_message_only_capture": True,
            }
        })
        packet = router.build_dispatch_packet(target, {"task_id": "T001"}, "msg")
        assert packet["capture_policy"]["must_match_task_id"] is False

    def test_forbid_last_message_always_true(self):
        """Top-level forbid flag must always be true."""
        target = _make_v2_target()
        packet = router.build_dispatch_packet(target, {"task_id": "T001"}, "msg")
        assert packet["forbid_last_message_only_capture"] is True


# ── 4. Resolve Target v2 Fields ──────────────────────────────────────


class TestResolveTargetV2:
    """Verify resolve_target includes v2 fields."""

    def test_active_project_has_target_fields(self):
        """Active project with CDP should include target_id fields."""
        with patch.object(router, "_check_cdp", return_value=False):
            target = router.resolve_target("agent-acceptance")
        # CDP is mocked as down, so target_id will be None
        assert target["resolved"] is True
        assert "target_id" in target
        assert "target_url" in target
        assert "tab_match_status" in target

    def test_pending_project_no_target_fields(self):
        """Pending projects don't need tab resolution."""
        with patch.object(router, "_check_cdp", return_value=False):
            target = router.resolve_target("project-alpha")
        assert target["resolved"] is False
