"""Tests for DRY-RUN-DISPATCH-10-A1 — v2 dry-run dispatch classification.

Tests cover:
  1. Classification rules (v2 fail-closed)
  2. Collision detection (conversation-only)
  3. Error reason mapping
  4. Report structure
"""

import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

REPO = Path(__file__).resolve().parent.parent
SCRIPTS = REPO / "scripts"
sys.path.insert(0, str(SCRIPTS))

import dry_run_dispatch_10 as dry_run


# ── 1. Classification Rules ──────────────────────────────────────────


class TestClassifyPacket:
    """Test _classify_packet with v2 fail-closed gates."""

    def _make_inputs(self, binding_status="active", resolved=True,
                     tab_match_status="exact_match", target_id="t-123",
                     dispatchable=True, conv_id="conv-1"):
        project_info = {"binding_status": binding_status}
        target = {
            "resolved": resolved,
            "tab_match_status": tab_match_status,
            "target_id": target_id,
            "conversation_id": conv_id,
        }
        packet = {"dispatchable": dispatchable}
        return project_info, target, packet

    def test_pending_manual_binding(self):
        """Binding status pending -> non_dispatchable_pending."""
        info, target, packet = self._make_inputs(
            binding_status="pending_manual_binding"
        )
        result = dry_run._classify_packet("proj", info, target, packet, set())
        assert result == "non_dispatchable_pending"

    def test_collision_blocks_dispatch(self):
        """Resolved but in collision set -> non_dispatchable_collision."""
        info, target, packet = self._make_inputs()
        result = dry_run._classify_packet(
            "proj", info, target, packet, {"proj"}
        )
        assert result == "non_dispatchable_collision"

    def test_exact_match_dispatchable(self):
        """All good -> dispatchable."""
        info, target, packet = self._make_inputs()
        result = dry_run._classify_packet("proj", info, target, packet, set())
        assert result == "dispatchable"

    def test_ambiguous_tab_blocked(self):
        """Ambiguous tab match -> blocked_ambiguous_tab."""
        info, target, packet = self._make_inputs(
            tab_match_status="ambiguous", dispatchable=False
        )
        result = dry_run._classify_packet("proj", info, target, packet, set())
        assert result == "blocked_ambiguous_tab"

    def test_no_match_tab_unresolved(self):
        """No tab match -> human_required_tab_unresolved."""
        info, target, packet = self._make_inputs(
            tab_match_status="no_match", dispatchable=False
        )
        result = dry_run._classify_packet("proj", info, target, packet, set())
        assert result == "human_required_tab_unresolved"

    def test_cdp_unreachable_tab_unresolved(self):
        """CDP unreachable -> human_required_tab_unresolved."""
        info, target, packet = self._make_inputs(
            tab_match_status="cdp_unreachable", dispatchable=False
        )
        result = dry_run._classify_packet("proj", info, target, packet, set())
        assert result == "human_required_tab_unresolved"

    def test_missing_target_id(self):
        """Resolved but no target_id -> human_required_missing_target_id."""
        info, target, packet = self._make_inputs(
            tab_match_status="exact_match", target_id=None, dispatchable=False
        )
        result = dry_run._classify_packet("proj", info, target, packet, set())
        assert result == "human_required_missing_target_id"

    def test_generic_human_required(self):
        """Packet not dispatchable for other reasons -> human_required."""
        info, target, packet = self._make_inputs(
            tab_match_status="exact_match", target_id="t-1",
            dispatchable=False
        )
        packet["error"] = "some other error"
        result = dry_run._classify_packet("proj", info, target, packet, set())
        assert result == "human_required"

    def test_priority_pending_before_collision(self):
        """Pending takes priority over collision."""
        info, target, packet = self._make_inputs(
            binding_status="pending_manual_binding"
        )
        result = dry_run._classify_packet(
            "proj", info, target, packet, {"proj"}
        )
        assert result == "non_dispatchable_pending"

    def test_priority_collision_before_tab_check(self):
        """Collision takes priority over tab status check."""
        info, target, packet = self._make_inputs(
            tab_match_status="no_match"
        )
        result = dry_run._classify_packet(
            "proj", info, target, packet, {"proj"}
        )
        assert result == "non_dispatchable_collision"

    def test_no_chat_url_tab_unresolved(self):
        """No chat_url -> human_required_tab_unresolved."""
        info, target, packet = self._make_inputs(
            tab_match_status="no_chat_url", dispatchable=False
        )
        result = dry_run._classify_packet("proj", info, target, packet, set())
        assert result == "human_required_tab_unresolved"


# ── 2. Collision Detection ───────────────────────────────────────────


class TestFindCollisionProjects:
    """Conversation-only collision detection (v2)."""

    def test_no_collisions(self):
        targets = [
            {"resolved": True, "project_id": "a", "conversation_id": "conv-a"},
            {"resolved": True, "project_id": "b", "conversation_id": "conv-b"},
        ]
        result = dry_run._find_collision_projects(targets)
        assert result == set()

    def test_conversation_collision(self):
        targets = [
            {"resolved": True, "project_id": "a", "conversation_id": "conv-shared"},
            {"resolved": True, "project_id": "b", "conversation_id": "conv-shared"},
        ]
        result = dry_run._find_collision_projects(targets)
        assert result == {"a", "b"}

    def test_shared_cdp_not_collision(self):
        """Shared CDP endpoint is expected, not a collision."""
        targets = [
            {"resolved": True, "project_id": "a", "conversation_id": "conv-a",
             "cdp_endpoint": "http://localhost:9222"},
            {"resolved": True, "project_id": "b", "conversation_id": "conv-b",
             "cdp_endpoint": "http://localhost:9222"},
        ]
        result = dry_run._find_collision_projects(targets)
        assert result == set()

    def test_unresolved_not_counted(self):
        targets = [
            {"resolved": True, "project_id": "a", "conversation_id": "conv-a"},
            {"resolved": False, "project_id": "b"},
        ]
        result = dry_run._find_collision_projects(targets)
        assert result == set()


# ── 3. Helper Functions ──────────────────────────────────────────────


class TestHelpers:
    """Test helper utility functions."""

    def test_build_test_task_spec(self):
        spec = dry_run._build_test_task_spec("my-project")
        assert spec["task_id"] == "DRYRUN-MY-PROJECT-001"
        assert spec["dry_run"] is True
        assert spec["scope"] == "gated_capture_only"

    def test_build_test_message(self):
        msg = dry_run._build_test_message("proj-alpha")
        assert "proj-alpha" in msg
        assert "Do not process" in msg

    def test_utc_now_format(self):
        ts = dry_run._utc_now()
        assert ts.endswith("Z")
        assert "T" in ts


# ── 4. Report Structure ──────────────────────────────────────────────


class TestReportStructure:
    """Verify dry-run report has v2 required fields."""

    @patch.object(dry_run, "build_all_dispatch_packets")
    def test_report_has_v2_summary_fields(self, mock_packets):
        """Report summary should include v2 classification counts."""
        mock_packets.return_value = [
            {"classification": "dispatchable", "dispatchable": True,
             "project_id": "a", "error": None, "packet": {}},
            {"classification": "blocked_ambiguous_tab", "dispatchable": False,
             "project_id": "b", "error": "ambiguous", "packet": None},
            {"classification": "human_required_tab_unresolved", "dispatchable": False,
             "project_id": "c", "error": "no match", "packet": None},
            {"classification": "human_required_missing_target_id", "dispatchable": False,
             "project_id": "d", "error": "missing id", "packet": None},
            {"classification": "non_dispatchable_pending", "dispatchable": False,
             "project_id": "e", "error": "pending", "packet": None},
        ]
        report = dry_run.generate_report()

        assert report["report_id"] == "DRY_RUN_DISPATCH_10"
        assert report["sent"] is False
        s = report["summary"]
        assert s["total"] == 5
        assert s["dispatchable_count"] == 1
        assert s.get("blocked_tab_count", 0) == 1
        assert s.get("tab_unresolved_count", 0) == 1
        assert s.get("missing_target_id_count", 0) == 1
        assert s["pending_count"] == 1

    @patch.object(dry_run, "build_all_dispatch_packets")
    def test_report_has_packets(self, mock_packets):
        """Report should include packet list."""
        mock_packets.return_value = []
        report = dry_run.generate_report()
        assert "packets" in report
        assert report["summary"]["total"] == 0
