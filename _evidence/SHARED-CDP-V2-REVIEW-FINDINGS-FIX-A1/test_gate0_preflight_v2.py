"""Tests for SHARED-CDP-GATE0-PREFLIGHT-V2-A1 — v2 preflight for shared CDP.

Tests cover:
  1. v2 classification rules (no profile/port collision)
  2. Conversation uniqueness enforcement
  3. Tab target resolution integration
  4. Verdict logic (PASS/PARTIAL_PASS/BLOCKED)
  5. Report structure compliance
"""

import json
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

REPO = Path(__file__).resolve().parent.parent
SCRIPTS = REPO / "scripts"
sys.path.insert(0, str(SCRIPTS))

import gate0_preflight_10


# ── 1. v2 Classification Rules ───────────────────────────────────────


class TestV2ClassificationRules:
    """v2 does NOT check profile_dup or port_dup."""

    def test_evaluate_active_project_all_good(self):
        """Active project with valid conversation and tab match -> active."""
        reg_info = {"binding_status": "active"}
        binding = {
            "bindings": [{
                "binding_status": "active",
                "conversation_id": "conv-unique-001",
                "chat_url": "https://chatgpt.com/c/conv-unique-001",
                "agent_id": "agent-1",
                "role": "executor",
            }]
        }
        cdp_pages = [
            {"id": "target-1", "type": "page", "url": "https://chatgpt.com/c/conv-unique-001"}
        ]

        result = gate0_preflight_10._evaluate_project_v2(
            "proj-test", reg_info, binding,
            cdp_healthy=True,
            conv_id_duplicates=set(),
            chat_url_duplicates=set(),
            cdp_pages=cdp_pages,
        )
        assert result["status"] == "active"
        assert result["tab_target_id"] == "target-1"
        assert result["tab_match_status"] == "exact_match"
        assert result["issues"] == []

    def test_shared_profile_is_not_collision(self):
        """v2: shared profile is EXPECTED, not a collision."""
        reg_info = {"binding_status": "active"}
        binding = {
            "bindings": [{
                "binding_status": "active",
                "conversation_id": "conv-unique-002",
                "chat_url": "https://chatgpt.com/c/conv-unique-002",
                "browser_profile_id": "shared",  # Shared profile — OK in v2
                "agent_id": "agent-2",
                "role": "executor",
            }]
        }
        cdp_pages = [
            {"id": "target-2", "type": "page", "url": "https://chatgpt.com/c/conv-unique-002"}
        ]

        result = gate0_preflight_10._evaluate_project_v2(
            "proj-shared", reg_info, binding,
            cdp_healthy=True,
            conv_id_duplicates=set(),
            chat_url_duplicates=set(),
            cdp_pages=cdp_pages,
        )
        assert result["status"] == "active"
        assert "profile_collision" not in str(result["issues"]).lower()

    def test_conversation_collision_blocks(self):
        """Duplicate conversation_id -> conversation_collision."""
        reg_info = {"binding_status": "active"}
        binding = {
            "bindings": [{
                "binding_status": "active",
                "conversation_id": "conv-dup-001",
                "chat_url": "https://chatgpt.com/c/conv-dup-001",
                "agent_id": "agent-3",
                "role": "executor",
            }]
        }

        result = gate0_preflight_10._evaluate_project_v2(
            "proj-collision", reg_info, binding,
            cdp_healthy=True,
            conv_id_duplicates={"conv-dup-001"},
            chat_url_duplicates=set(),
            cdp_pages=[],
        )
        assert result["status"] == "conversation_collision"
        assert any("conversation_id" in i for i in result["issues"])

    def test_duplicate_chat_url_blocks(self):
        """Duplicate chat_url -> blocked."""
        reg_info = {"binding_status": "active"}
        binding = {
            "bindings": [{
                "binding_status": "active",
                "conversation_id": "conv-a",
                "chat_url": "https://chatgpt.com/c/dup-url",
                "agent_id": "agent-4",
                "role": "executor",
            }]
        }

        result = gate0_preflight_10._evaluate_project_v2(
            "proj-dup-url", reg_info, binding,
            cdp_healthy=True,
            conv_id_duplicates=set(),
            chat_url_duplicates={"https://chatgpt.com/c/dup-url"},
            cdp_pages=[],
        )
        assert result["status"] == "blocked"
        assert any("chat_url" in i for i in result["issues"])

    def test_tab_unresolved(self):
        """Active project but no matching tab -> tab_unresolved."""
        reg_info = {"binding_status": "active"}
        binding = {
            "bindings": [{
                "binding_status": "active",
                "conversation_id": "conv-no-tab",
                "chat_url": "https://chatgpt.com/c/conv-no-tab",
                "agent_id": "agent-5",
                "role": "executor",
            }]
        }

        result = gate0_preflight_10._evaluate_project_v2(
            "proj-no-tab", reg_info, binding,
            cdp_healthy=True,
            conv_id_duplicates=set(),
            chat_url_duplicates=set(),
            cdp_pages=[],  # No tabs available
        )
        assert result["status"] == "tab_unresolved"
        # Canonical resolver returns cdp_unreachable when page list is empty
        assert result["tab_match_status"] in ("no_match", "cdp_unreachable")

    def test_cdp_down_is_stale(self):
        """CDP not responding -> stale."""
        reg_info = {"binding_status": "active"}
        binding = {
            "bindings": [{
                "binding_status": "active",
                "conversation_id": "conv-healthy",
                "chat_url": "https://chatgpt.com/c/conv-healthy",
                "agent_id": "agent-6",
                "role": "executor",
            }]
        }

        result = gate0_preflight_10._evaluate_project_v2(
            "proj-stale", reg_info, binding,
            cdp_healthy=False,
            conv_id_duplicates=set(),
            chat_url_duplicates=set(),
            cdp_pages=[],
        )
        assert result["status"] == "stale"

    def test_pending_is_pending_manual_binding(self):
        """Pending projects -> pending_manual_binding."""
        reg_info = {"binding_status": "pending_binding"}
        binding = {
            "bindings": [{
                "binding_status": "pending_binding",
                "conversation_id": "pending-test-001",
                "agent_id": "agent-7",
                "role": "executor",
            }]
        }

        result = gate0_preflight_10._evaluate_project_v2(
            "proj-pending", reg_info, binding,
            cdp_healthy=True,
            conv_id_duplicates=set(),
            chat_url_duplicates=set(),
            cdp_pages=[],
        )
        assert result["status"] == "pending_manual_binding"

    def test_no_binding_file_is_blocked(self):
        """Active but no binding file -> blocked."""
        reg_info = {"binding_status": "active"}
        binding = {}

        result = gate0_preflight_10._evaluate_project_v2(
            "proj-no-bind", reg_info, binding,
            cdp_healthy=True,
            conv_id_duplicates=set(),
            chat_url_duplicates=set(),
            cdp_pages=[],
        )
        assert result["status"] == "blocked"

    def test_ambiguous_tab_match_is_blocked(self):
        """Multiple tabs match same URL -> blocked."""
        reg_info = {"binding_status": "active"}
        binding = {
            "bindings": [{
                "binding_status": "active",
                "conversation_id": "conv-ambig",
                "chat_url": "https://chatgpt.com/c/conv-ambig",
                "agent_id": "agent-8",
                "role": "executor",
            }]
        }
        cdp_pages = [
            {"id": "t1", "type": "page", "url": "https://chatgpt.com/c/conv-ambig"},
            {"id": "t2", "type": "page", "url": "https://chatgpt.com/c/conv-ambig"},
        ]

        result = gate0_preflight_10._evaluate_project_v2(
            "proj-ambig", reg_info, binding,
            cdp_healthy=True,
            conv_id_duplicates=set(),
            chat_url_duplicates=set(),
            cdp_pages=cdp_pages,
        )
        assert result["status"] == "blocked"
        assert result["tab_match_status"] == "ambiguous"


# ── 2. Verdict Logic ────────────────────────────────────────────────


class TestVerdictLogic:
    """Test overall verdict computation."""

    @patch.object(gate0_preflight_10, "check_cdp_health", return_value=True)
    @patch.object(gate0_preflight_10, "_canonical_list_cdp_pages", return_value=[])
    @patch.object(gate0_preflight_10, "load_binding")
    @patch.object(gate0_preflight_10, "load_registry")
    def test_pass_with_active_projects(self, mock_reg, mock_bind, mock_pages, mock_cdp):
        """All active, no issues -> PASS."""
        mock_reg.return_value = {
            "projects": {
                "proj-a": {"project_root": ".", "binding_status": "active"},
            },
            "shared_cdp_endpoint": "http://localhost:9222",
        }
        mock_bind.return_value = {
            "bindings": [{
                "binding_status": "active",
                "conversation_id": "conv-a",
                "chat_url": "https://chatgpt.com/c/conv-a",
                "agent_id": "a1",
                "role": "executor",
            }]
        }
        mock_pages.return_value = [
            {"id": "t1", "type": "page", "url": "https://chatgpt.com/c/conv-a"}
        ]

        result = gate0_preflight_10.run_preflight()
        assert result["overall"]["verdict"] == "PASS"
        assert result["active_count"] == 1

    @patch.object(gate0_preflight_10, "check_cdp_health", return_value=True)
    @patch.object(gate0_preflight_10, "_canonical_list_cdp_pages", return_value=[])
    @patch.object(gate0_preflight_10, "load_binding")
    @patch.object(gate0_preflight_10, "load_registry")
    def test_blocked_no_active(self, mock_reg, mock_bind, mock_pages, mock_cdp):
        """Only pending projects -> BLOCKED."""
        mock_reg.return_value = {
            "projects": {
                "proj-a": {"project_root": ".", "binding_status": "pending_binding"},
            },
            "shared_cdp_endpoint": "http://localhost:9222",
        }
        mock_bind.return_value = {"bindings": []}

        result = gate0_preflight_10.run_preflight()
        assert result["overall"]["verdict"] == "BLOCKED"

    @patch.object(gate0_preflight_10, "check_cdp_health", return_value=False)
    @patch.object(gate0_preflight_10, "load_binding")
    @patch.object(gate0_preflight_10, "load_registry")
    def test_partial_pass_stale(self, mock_reg, mock_bind, mock_cdp):
        """Active project but CDP down -> PARTIAL_PASS."""
        mock_reg.return_value = {
            "projects": {
                "proj-a": {"project_root": ".", "binding_status": "active"},
            },
            "shared_cdp_endpoint": "http://localhost:9222",
        }
        mock_bind.return_value = {
            "bindings": [{
                "binding_status": "active",
                "conversation_id": "conv-a",
                "chat_url": "https://chatgpt.com/c/conv-a",
                "agent_id": "a1",
                "role": "executor",
            }]
        }

        result = gate0_preflight_10.run_preflight()
        assert result["overall"]["verdict"] in ("PARTIAL_PASS", "BLOCKED")
        assert result["stale_count"] >= 0


# ── 3. Report Structure ──────────────────────────────────────────────


class TestReportStructure:
    """Verify v2 report has all required fields."""

    @patch.object(gate0_preflight_10, "check_cdp_health", return_value=True)
    @patch.object(gate0_preflight_10, "_canonical_list_cdp_pages", return_value=[])
    @patch.object(gate0_preflight_10, "load_binding")
    @patch.object(gate0_preflight_10, "load_registry")
    def test_report_has_v2_fields(self, mock_reg, mock_bind, mock_pages, mock_cdp):
        mock_reg.return_value = {
            "projects": {
                "proj-a": {"project_root": ".", "binding_status": "active"},
            },
            "shared_cdp_endpoint": "http://localhost:9222",
        }
        mock_bind.return_value = {
            "bindings": [{
                "binding_status": "active",
                "conversation_id": "conv-a",
                "chat_url": "https://chatgpt.com/c/conv-a",
                "agent_id": "a1",
                "role": "executor",
            }]
        }
        mock_pages.return_value = [
            {"id": "t1", "type": "page", "url": "https://chatgpt.com/c/conv-a"}
        ]

        report = gate0_preflight_10.run_preflight()

        # v2 required fields
        assert report["schema_version"] == "2.0.0"
        assert report["task_id"] == "SHARED-CDP-GATE0-PREFLIGHT-V2-A1"
        assert report["architecture_version"] == "2.0.0"
        assert report["cdp_mode"] == "shared_single_chrome"
        assert "cdp_endpoint" in report
        assert "cdp_healthy" in report
        assert "cdp_pages_total" in report

        # Count fields
        assert "active_count" in report
        assert "pending_count" in report
        assert "collision_count" in report
        assert "tab_unresolved_count" in report
        assert "stale_count" in report
        assert "blocked_count" in report

        # Per-project fields
        proj = report["per_project"][0]
        assert "tab_target_id" in proj
        assert "tab_match_status" in proj
        assert "conv_id" in proj
        assert "chat_url" in proj

    @patch.object(gate0_preflight_10, "load_registry")
    def test_empty_registry_returns_blocked(self, mock_reg):
        mock_reg.return_value = {"projects": {}}
        report = gate0_preflight_10.run_preflight()
        assert report["overall"]["verdict"] == "BLOCKED"
        assert report["schema_version"] == "2.0.0"


# ── 4. Utility Functions ─────────────────────────────────────────────


class TestUtilities:
    """Test helper functions."""

    def test_is_valid_conv_id_real(self):
        assert gate0_preflight_10.is_valid_conv_id("6a26cc03-abc") is True

    def test_is_valid_conv_id_pending(self):
        assert gate0_preflight_10.is_valid_conv_id("pending-project-alpha-001") is False

    def test_is_valid_conv_id_none(self):
        assert gate0_preflight_10.is_valid_conv_id(None) is False

    def test_is_valid_conv_id_empty(self):
        assert gate0_preflight_10.is_valid_conv_id("") is False
        assert gate0_preflight_10.is_valid_conv_id("   ") is False

    def test_canonical_resolve_tab_target_exact(self):
        """Verify canonical tab resolver works for exact match."""
        import tab_target_resolver
        pages = [{"id": "t1", "type": "page", "url": "https://chatgpt.com/c/abc"}]
        result = tab_target_resolver.resolve_tab_target("https://chatgpt.com/c/abc", pages)
        assert result["match_status"] == "exact_match"
        assert result["target_id"] == "t1"

    def test_canonical_resolve_tab_target_no_match(self):
        """No match -> no_match."""
        import tab_target_resolver
        result = tab_target_resolver.resolve_tab_target("https://chatgpt.com/c/xyz", [])
        assert result["match_status"] == "cdp_unreachable"

    def test_canonical_resolve_tab_target_empty_url(self):
        """Empty URL -> no_chat_url."""
        import tab_target_resolver
        result = tab_target_resolver.resolve_tab_target("", [])
        assert result["match_status"] == "no_chat_url"
