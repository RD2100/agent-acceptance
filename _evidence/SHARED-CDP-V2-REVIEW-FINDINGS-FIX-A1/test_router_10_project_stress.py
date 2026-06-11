"""Phase 3 Stress Test: 10-Project Multi-Project Router (v2 Shared Chrome).

Stress-tests the multi_project_router.py against the real 10-project
PROJECT_REGISTRY.json with single_chrome_shared_cdp architecture.
Uses actual registry and binding files on disk; only _check_cdp is mocked.

Classes:
  TestRouter10ProjectLoad          - Registry structure & shared architecture
  TestRouter10ProjectResolve       - resolve_target / resolve_all semantics
  TestRouter10ProjectIsolation     - verify_isolation at scale (conversation-only)
  TestRouter10ProjectDispatch      - build_dispatch_packet for every status
  TestRouter10ProjectClassification - active vs pending classification
"""

import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

REPO = Path(__file__).resolve().parent.parent
SCRIPTS = REPO / "scripts"
sys.path.insert(0, str(SCRIPTS))

import multi_project_router  # noqa: E402

# ── Constants ──────────────────────────────────────────────────────────

EXPECTED_PROJECTS = 10
SHARED_CDP_ENDPOINT = "http://localhost:9222"
ACTIVE_PROJECT = "agent-acceptance"
BOUND_PROJECTS = []
PENDING_PROJECTS = [
    "project-alpha", "project-beta", "project-gamma",
    "project-delta", "project-epsilon", "project-zeta",
    "project-eta", "project-theta", "project-iota",
]


# ── Helpers ────────────────────────────────────────────────────────────


def _make_target(
    project_id: str,
    conv_id: str,
    resolved: bool = True,
) -> dict:
    """Build a synthetic resolved target (shared CDP, conversation-isolated, v2 fields)."""
    if not resolved:
        return {"project_id": project_id, "resolved": False, "error": "unreachable"}
    return {
        "project_id": project_id,
        "resolved": True,
        "cdp_endpoint": SHARED_CDP_ENDPOINT,
        "cdp_active": False,
        "conversation_id": conv_id,
        "chat_url": f"https://chatgpt.com/c/{conv_id}",
        "target_id": f"cdp-target-{project_id}",
        "target_url": f"https://chatgpt.com/c/{conv_id}",
        "tab_match_status": "exact_match",
        "agent_id": f"agent-{project_id}",
        "agent_role": "executor",
        "binding_status": "active",
    }


# ═══════════════════════════════════════════════════════════════════════
# 1. TestRouter10ProjectLoad  (3 tests)
# ═══════════════════════════════════════════════════════════════════════


class TestRouter10ProjectLoad:
    """Verify the real PROJECT_REGISTRY.json on disk (v2 shared-CDP)."""

    def test_registry_has_10_projects(self):
        reg = multi_project_router.load_registry()
        projects = reg.get("projects", {})
        assert len(projects) == EXPECTED_PROJECTS, (
            f"Expected {EXPECTED_PROJECTS} projects, got {len(projects)}"
        )

    def test_registry_declares_shared_architecture(self):
        reg = multi_project_router.load_registry()
        assert reg.get("architecture") == "single_chrome_shared_cdp"
        assert reg.get("shared_cdp_endpoint") == SHARED_CDP_ENDPOINT
        assert reg.get("shared_cdp_port") == 9222

    def test_all_projects_share_cdp(self):
        """No project should have a unique cdp_port — all share the same Chrome."""
        reg = multi_project_router.load_registry()
        for pid, info in reg["projects"].items():
            # v2 registry should NOT have per-project cdp_port or cdp_endpoint
            assert "cdp_port" not in info, (
                f"{pid} should not have cdp_port in v2 shared-CDP architecture"
            )


# ═══════════════════════════════════════════════════════════════════════
# 2. TestRouter10ProjectResolve  (4 tests)
# ═══════════════════════════════════════════════════════════════════════


class TestRouter10ProjectResolve:
    """Resolve targets using the real registry and binding files."""

    def test_resolve_all_returns_10(self):
        with patch.object(multi_project_router, "_check_cdp", return_value=False):
            results = multi_project_router.resolve_all()
        assert len(results) == EXPECTED_PROJECTS, (
            f"resolve_all must return {EXPECTED_PROJECTS} results"
        )
        project_ids = {r["project_id"] for r in results}
        assert ACTIVE_PROJECT in project_ids
        for pp in PENDING_PROJECTS + BOUND_PROJECTS:
            assert pp in project_ids, f"Missing project: {pp}"

    def test_resolve_active_project(self):
        with patch.object(multi_project_router, "_check_cdp", return_value=False):
            result = multi_project_router.resolve_target(ACTIVE_PROJECT)
        assert result["resolved"] is True, (
            f"agent-acceptance should resolve: {result.get('error')}"
        )
        assert result["cdp_endpoint"] == SHARED_CDP_ENDPOINT  # shared!
        assert result["conversation_id"] is not None
        assert result["agent_id"] is not None
        assert result["binding_status"] == "active"
        assert result["chat_url"] is not None

    def test_resolve_pending_projects(self):
        """Pending projects have binding files but no active agents."""
        pending_id = PENDING_PROJECTS[0]
        with patch.object(multi_project_router, "_check_cdp", return_value=False):
            result = multi_project_router.resolve_target(pending_id)
        assert result["resolved"] is False
        assert "no active" in result.get("error", "").lower()
        assert result.get("binding_count", 0) > 0, (
            "Binding file should be loaded even for pending projects"
        )
        # Verify registry shows pending status
        reg = multi_project_router.load_registry()
        assert reg["projects"][pending_id]["binding_status"] == "pending_binding"

    def test_resolve_nonexistent_project(self):
        with patch.object(multi_project_router, "_check_cdp", return_value=False):
            result = multi_project_router.resolve_target("fake-project")
        assert result["resolved"] is False
        assert "not found" in result.get("error", "").lower()


# ═══════════════════════════════════════════════════════════════════════
# 3. TestRouter10ProjectIsolation  (6 tests)
# ═══════════════════════════════════════════════════════════════════════


class TestRouter10ProjectIsolation:
    """Verify verify_isolation at 10-project scale (conversation-only)."""

    def _build_10_targets(self) -> list[dict]:
        """10 properly-isolated synthetic targets (shared CDP, unique conversations)."""
        names = [ACTIVE_PROJECT] + BOUND_PROJECTS + PENDING_PROJECTS
        return [
            _make_target(
                project_id=names[i],
                conv_id=f"conv-{names[i]}-{i}",
            )
            for i in range(EXPECTED_PROJECTS)
        ]

    def test_isolation_10_projects_pass(self):
        targets = self._build_10_targets()
        result = multi_project_router.verify_isolation(targets)
        assert result["isolated"] is True
        assert result["total_projects"] == EXPECTED_PROJECTS
        assert result["unique_conversations"] == EXPECTED_PROJECTS
        assert result["issues"] == []

    def test_shared_cdp_is_not_a_collision(self):
        """All targets share the same cdp_endpoint — this is expected, not a collision."""
        targets = self._build_10_targets()
        # Verify they all share the same endpoint
        endpoints = {t["cdp_endpoint"] for t in targets}
        assert len(endpoints) == 1, "All targets should share one CDP endpoint"
        result = multi_project_router.verify_isolation(targets)
        assert result["isolated"] is True  # shared CDP is fine

    def test_conversation_collision_in_10(self):
        targets = self._build_10_targets()
        # Force targets[7] to share a conversation_id with targets[3]
        targets[7]["conversation_id"] = targets[3]["conversation_id"]
        result = multi_project_router.verify_isolation(targets)
        assert result["isolated"] is False
        assert any("Conversation collision" in issue for issue in result["issues"])

    def test_mixed_active_pending_isolation(self):
        """Mix of active and pending targets should still be isolated."""
        active = _make_target("agent-acceptance", "conv-active")
        pending_targets = [
            _make_target(f"project-{name}", f"conv-pending-{i}")
            for i, name in enumerate(["alpha", "beta", "gamma"])
        ]
        targets = [active] + pending_targets
        result = multi_project_router.verify_isolation(targets)
        assert result["isolated"] is True
        assert result["total_projects"] == 4
        assert result["unique_conversations"] == 4

    def test_unresolved_not_counted(self):
        """Only resolved targets count toward total_projects."""
        resolved = [
            _make_target("proj-ok-1", "conv-1"),
            _make_target("proj-ok-2", "conv-2"),
        ]
        unresolved = [
            _make_target(f"proj-fail-{i}", "", resolved=False)
            for i in range(8)
        ]
        targets = resolved + unresolved
        result = multi_project_router.verify_isolation(targets)
        assert result["isolated"] is True
        assert result["total_projects"] == 2
        assert result["unique_conversations"] == 2


# ═══════════════════════════════════════════════════════════════════════
# 4. TestRouter10ProjectDispatch  (3 tests)
# ═══════════════════════════════════════════════════════════════════════


class TestRouter10ProjectDispatch:
    """build_dispatch_packet for every project status."""

    def test_dispatch_packet_fail_closed_when_cdp_down(self):
        """v2 FAIL-CLOSED: when CDP is down, dispatch is blocked."""
        with patch.object(multi_project_router, "_check_cdp", return_value=False):
            target = multi_project_router.resolve_target(ACTIVE_PROJECT)
        assert target["resolved"] is True
        task_spec = {"task_id": "STRESS-T001", "description": "active dispatch"}
        packet = multi_project_router.build_dispatch_packet(
            target, task_spec, "Execute stress task"
        )
        # v2 fail-closed: CDP down -> tab_match_status=cdp_unreachable -> blocked
        assert packet["dispatchable"] is False
        assert packet.get("blocked_reason") == "tab_match_status_not_exact"

    def test_dispatch_packet_for_active_with_cdp(self):
        """Active project with CDP up and exact match -> dispatchable."""
        target = _make_target(ACTIVE_PROJECT, "conv-active-stress")
        task_spec = {"task_id": "STRESS-T001", "description": "active dispatch"}
        packet = multi_project_router.build_dispatch_packet(
            target, task_spec, "Execute stress task"
        )
        assert packet["dispatchable"] is True
        assert packet["project_id"] == ACTIVE_PROJECT
        assert packet["cdp_endpoint"] == SHARED_CDP_ENDPOINT
        assert packet["conversation_id"] is not None
        assert packet["target_id"] is not None
        assert packet["tab_match_status"] == "exact_match"
        assert packet["task_spec"]["task_id"] == "STRESS-T001"
        assert packet["message_text"] == "Execute stress task"
        assert packet["message_length"] == len("Execute stress task")
        assert packet["cdp_mode"] == "shared_single_chrome"
        assert packet["isolation_model"] == "conversation_target_bound"
        assert "built_at" in packet

    def test_dispatch_packet_for_pending(self):
        """Pending projects do not resolve, dispatch correctly blocked."""
        pending_id = PENDING_PROJECTS[0]
        with patch.object(multi_project_router, "_check_cdp", return_value=False):
            target = multi_project_router.resolve_target(pending_id)
        assert target["resolved"] is False
        task_spec = {"task_id": "STRESS-T002", "description": "pending dispatch"}
        packet = multi_project_router.build_dispatch_packet(
            target, task_spec, "Execute pending task"
        )
        assert packet["dispatchable"] is False
        assert "error" in packet

    def test_dispatch_packet_for_unresolved(self):
        target = multi_project_router.resolve_target("fake-project")
        assert target["resolved"] is False
        task_spec = {"task_id": "STRESS-T003", "description": "unresolved dispatch"}
        packet = multi_project_router.build_dispatch_packet(
            target, task_spec, "Should not dispatch"
        )
        assert packet["dispatchable"] is False
        assert "not found" in packet.get("error", "").lower()


# ═══════════════════════════════════════════════════════════════════════
# 5. TestRouter10ProjectClassification  (3 tests)
# ═══════════════════════════════════════════════════════════════════════


class TestRouter10ProjectClassification:
    """Classify projects by binding_status from the registry."""

    def test_active_vs_pending_classification(self):
        reg = multi_project_router.load_registry()
        projects = reg["projects"]
        # agent-acceptance must be active
        assert projects[ACTIVE_PROJECT]["binding_status"] == "active"
        # project-alpha (bound) must be active
        for pid in BOUND_PROJECTS:
            assert projects[pid]["binding_status"] == "active", (
                f"{pid} should be active (bound to real conversation)"
            )
        # All scaffold projects must be pending_binding
        for pid in PENDING_PROJECTS:
            assert projects[pid]["binding_status"] == "pending_binding", (
                f"{pid} should be pending_binding"
            )

    def test_active_count(self):
        reg = multi_project_router.load_registry()
        active = [
            pid for pid, info in reg["projects"].items()
            if info["binding_status"] == "active"
        ]
        assert len(active) == 1, f"Expected 1 active project, got {len(active)}: {active}"
        assert ACTIVE_PROJECT in active

    def test_pending_count(self):
        reg = multi_project_router.load_registry()
        pending = [
            pid for pid, info in reg["projects"].items()
            if info["binding_status"] == "pending_binding"
        ]
        assert len(pending) == 9, f"Expected 9 pending projects, got {len(pending)}: {pending}"
        assert set(pending) == set(PENDING_PROJECTS)
