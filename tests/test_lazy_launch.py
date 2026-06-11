"""Tests for lazy_launch_manager — Phase 2 MULTI-CDP-LAZY-LAUNCH-A1.

Covers:
- Module import
- get_project_status for each lifecycle state
- lazy_launch (already active, resource limit, success)
- health_check_all classification
- count_warm_instances
- load_resource_policy
- mark_stale
- Stale detection on /json/version failure
"""
from __future__ import annotations

import json
import sys
from io import BytesIO
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Ensure scripts/ is importable
SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import lazy_launch_manager as llm


# ── Fixtures ──────────────────────────────────────────────────────────


@pytest.fixture
def isolated_env(tmp_path, monkeypatch):
    """Create isolated registry + policy in tmp_path and patch module paths."""
    agent_dir = tmp_path / ".agent"
    agent_dir.mkdir()

    registry_path = agent_dir / "PROJECT_REGISTRY.json"
    policy_path = agent_dir / "MULTI_PROJECT_RESOURCE_POLICY.json"

    # v2 registry: shared Chrome, conversation-based isolation
    registry = {
        "schema_version": "2.0.0",
        "awsp_version": "1.3.0",
        "architecture": "single_chrome_shared_cdp",
        "generated_at": "2026-06-10T00:00:00Z",
        "shared_cdp_port": 9222,
        "shared_cdp_endpoint": "http://localhost:9222",
        "projects": {
            "proj-a": {
                "project_id": "proj-a",
                "binding_status": "pending_binding",
                "registered_at": "2026-06-10T00:00:00Z",
            },
            "proj-b": {
                "project_id": "proj-b",
                "binding_status": "pending_binding",
                "registered_at": "2026-06-10T00:00:00Z",
            },
            "proj-c": {
                "project_id": "proj-c",
                "binding_status": "active",
                "registered_at": "2026-06-10T00:00:00Z",
            },
        },
    }

    policy = {
        "schema_version": "1.0.0",
        "max_warm_cdp_instances": 2,
        "max_active_gpt_reviews": 1,
        "lazy_launch": True,
    }

    registry_path.write_text(json.dumps(registry, indent=2), encoding="utf-8")
    policy_path.write_text(json.dumps(policy, indent=2), encoding="utf-8")

    # Patch module-level paths
    monkeypatch.setattr(llm, "REGISTRY_PATH", registry_path)
    monkeypatch.setattr(llm, "POLICY_PATH", policy_path)

    return {
        "registry_path": registry_path,
        "policy_path": policy_path,
        "registry": registry,
        "policy": policy,
    }


def _make_cdp_response(version_text="Chrome/120.0", protocol="1.3"):
    """Build a mock urllib response for /json/version."""
    body = json.dumps({
        "Browser": version_text,
        "Protocol-Version": protocol,
        "webSocketDebuggerUrl": "ws://localhost:9222/devtools/browser/abc",
    }).encode("utf-8")
    return BytesIO(body)


def _make_pages_response(pages):
    """Build a mock urllib response for /json (page list)."""
    body = json.dumps(pages).encode("utf-8")
    return BytesIO(body)


# ── 1. Module Import ──────────────────────────────────────────────────


class TestModuleImport:
    def test_module_imports(self):
        """LLM-001: Module imports without error."""
        assert llm is not None
        assert hasattr(llm, "get_project_status")
        assert hasattr(llm, "lazy_launch")
        assert hasattr(llm, "health_check_all")
        assert hasattr(llm, "count_warm_instances")
        assert hasattr(llm, "load_resource_policy")
        assert hasattr(llm, "mark_stale")


# ── 2. get_project_status ─────────────────────────────────────────────


class TestGetProjectStatus:
    def test_unknown_project(self, isolated_env):
        """LLM-002: Unknown project returns registered status."""
        result = llm.get_project_status("nonexistent")
        assert result["project_id"] == "nonexistent"
        assert result["status"] == llm.STATUS_REGISTERED
        assert result["port"] == 0

    def test_registered_not_started(self, isolated_env):
        """LLM-003: Project in registry but CDP not responding -> registered."""
        # All urllib calls fail (no Chrome running)
        with patch.object(llm.urllib.request, "urlopen", side_effect=Exception("no connection")):
            result = llm.get_project_status("proj-a")
        assert result["status"] == llm.STATUS_REGISTERED
        assert result["cdp_responsive"] is False

    def test_warm_status(self, isolated_env):
        """LLM-004: CDP responds but no GPT pages -> warm."""
        call_count = {"n": 0}

        def fake_urlopen(url, timeout=3):
            call_count["n"] += 1
            if "/json/version" in url:
                return _make_cdp_response()
            elif url.endswith("/json"):
                # No GPT pages
                return _make_pages_response([
                    {"url": "https://example.com", "title": "Example"}
                ])
            raise Exception("unknown url")

        with patch.object(llm.urllib.request, "urlopen", side_effect=fake_urlopen):
            result = llm.get_project_status("proj-a")
        assert result["status"] == llm.STATUS_WARM
        assert result["cdp_responsive"] is True
        assert result["gpt_review_active"] is False

    def test_active_status(self, isolated_env):
        """LLM-005: CDP responds with GPT page -> active."""
        def fake_urlopen(url, timeout=3):
            if "/json/version" in url:
                return _make_cdp_response()
            elif url.endswith("/json"):
                return _make_pages_response([
                    {"url": "https://chatgpt.com/c/abc123", "title": "ChatGPT"},
                    {"url": "https://example.com", "title": "Other"},
                ])
            raise Exception("unknown url")

        with patch.object(llm.urllib.request, "urlopen", side_effect=fake_urlopen):
            result = llm.get_project_status("proj-a")
        assert result["status"] == llm.STATUS_ACTIVE
        assert result["gpt_review_active"] is True
        assert result["total_pages"] == 2

    def test_stale_from_binding_status(self, isolated_env):
        """LLM-006: binding_status=stale in registry -> stale."""
        # Set proj-a to stale in registry
        reg = json.loads(isolated_env["registry_path"].read_text(encoding="utf-8"))
        reg["projects"]["proj-a"]["binding_status"] = "stale"
        isolated_env["registry_path"].write_text(json.dumps(reg), encoding="utf-8")

        result = llm.get_project_status("proj-a")
        assert result["status"] == llm.STATUS_STALE

    def test_stale_detection_cdp_down(self, isolated_env):
        """LLM-007: binding_status=active but CDP not responding -> stale."""
        # proj-c has binding_status=active
        with patch.object(llm.urllib.request, "urlopen", side_effect=Exception("connection refused")):
            result = llm.get_project_status("proj-c")
        assert result["status"] == llm.STATUS_STALE
        assert result["cdp_responsive"] is False


# ── 3. lazy_launch ────────────────────────────────────────────────────


class TestLazyLaunch:
    def test_already_warm_returns_noop(self, isolated_env):
        """LLM-008: If project is already warm, lazy_launch returns noop."""
        def fake_urlopen(url, timeout=3):
            if "/json/version" in url:
                return _make_cdp_response()
            elif url.endswith("/json"):
                return _make_pages_response([])
            raise Exception("unknown url")

        with patch.object(llm.urllib.request, "urlopen", side_effect=fake_urlopen):
            result = llm.lazy_launch("proj-a")
        assert result["action"] == "noop"
        assert "Already" in result["reason"]

    def test_already_active_returns_noop(self, isolated_env):
        """LLM-009: If project is already active, lazy_launch returns noop."""
        def fake_urlopen(url, timeout=3):
            if "/json/version" in url:
                return _make_cdp_response()
            elif url.endswith("/json"):
                return _make_pages_response([
                    {"url": "https://chatgpt.com/c/xyz", "title": "GPT"}
                ])
            raise Exception("unknown url")

        with patch.object(llm.urllib.request, "urlopen", side_effect=fake_urlopen):
            result = llm.lazy_launch("proj-a")
        assert result["action"] == "noop"
        assert "active" in result["reason"]

    def test_resource_limit_reached(self, isolated_env):
        """LLM-010: Fails when shared Chrome is already running and max_warm=0."""
        # Override policy to max_warm=0 so that even one running Chrome triggers limit
        policy = {
            "schema_version": "1.0.0",
            "max_warm_cdp_instances": 0,
            "max_active_gpt_reviews": 1,
            "lazy_launch": True,
        }
        isolated_env["policy_path"].write_text(
            json.dumps(policy), encoding="utf-8"
        )

        def fake_urlopen(url, timeout=3):
            if "/json/version" in url:
                # Simulate shared Chrome NOT running (so target is "registered")
                raise Exception("no connection")
            raise Exception("unknown url")

        # But count_warm_instances sees the Chrome as running (mock returns 1)
        with patch.object(llm.urllib.request, "urlopen", side_effect=fake_urlopen):
            with patch.object(llm, "count_warm_instances", return_value=1):
                result = llm.lazy_launch("proj-a")

        assert result["action"] == "error"
        assert "Resource limit" in result["error"]
        assert result["warm_count"] >= result["max_warm"]

    def test_unknown_project(self, isolated_env):
        """LLM-011: Launching unknown project returns error."""
        # get_project_status will return registered for unknown project,
        # then lazy_launch checks registry and finds it missing
        with patch.object(llm.urllib.request, "urlopen", side_effect=Exception("no conn")):
            result = llm.lazy_launch("nonexistent-project")
        assert result["action"] == "error"
        assert "not found" in result["error"]

    def test_success_path(self, isolated_env):
        """LLM-012: Successful launch returns action=launched."""
        # proj-a is registered (not running), no warm instances
        def fake_urlopen(url, timeout=3):
            raise Exception("no connection — nothing running")

        mock_launch_result = {
            "project_id": "proj-a",
            "port": 9222,
            "launched": True,
            "pid": 12345,
            "cdp_endpoint": "http://localhost:9222",
            "profile_dir": "/tmp/proj-a",
            "launched_at": "2026-06-10T00:00:00Z",
        }

        with patch.object(llm.urllib.request, "urlopen", side_effect=fake_urlopen):
            with patch("multi_cdp_launcher.launch_chrome", return_value=mock_launch_result):
                result = llm.lazy_launch("proj-a")

        assert result["action"] == "launched"
        assert result["port"] == 9222
        assert result["pid"] == 12345
        assert result["status"] == "warm"

    def test_launch_failure_returns_error(self, isolated_env):
        """LLM-013: If launch_chrome fails, returns error."""
        def fake_urlopen(url, timeout=3):
            raise Exception("no connection")

        mock_launch_result = {
            "project_id": "proj-a",
            "port": 9222,
            "launched": False,
            "error": "Chrome executable not found",
        }

        with patch.object(llm.urllib.request, "urlopen", side_effect=fake_urlopen):
            with patch("multi_cdp_launcher.launch_chrome", return_value=mock_launch_result):
                result = llm.lazy_launch("proj-a")

        assert result["action"] == "error"
        assert "Chrome executable not found" in result["error"]


# ── 4. health_check_all ──────────────────────────────────────────────


class TestHealthCheckAll:
    def test_classification(self, isolated_env):
        """LLM-014: All projects share Chrome — classify by binding_status + CDP."""
        # In v2, all projects share port 9222. If Chrome is down:
        #   proj-a (pending_binding) -> registered (never started)
        #   proj-b (pending_binding) -> registered (never started)
        #   proj-c (active) -> stale (was running, now down)
        def fake_urlopen(url, timeout=3):
            raise Exception("no connection")

        with patch.object(llm.urllib.request, "urlopen", side_effect=fake_urlopen):
            result = llm.health_check_all()

        assert result["total"] == 3
        assert "proj-a" in result["not_started"]
        assert "proj-b" in result["not_started"]
        assert "proj-c" in result["stale"]

    def test_empty_registry(self, isolated_env, tmp_path):
        """LLM-015: Empty registry returns zeroed summary."""
        empty_registry = {
            "schema_version": "1.0.0",
            "projects": {},
        }
        isolated_env["registry_path"].write_text(
            json.dumps(empty_registry), encoding="utf-8"
        )

        result = llm.health_check_all()
        assert result["total"] == 0
        assert result["active"] == []
        assert result["warm"] == []
        assert result["stale"] == []
        assert result["not_started"] == []

    def test_details_per_project(self, isolated_env):
        """LLM-016: Health check includes per-project detail dicts."""
        with patch.object(llm.urllib.request, "urlopen", side_effect=Exception("down")):
            result = llm.health_check_all()

        assert "details" in result
        assert "proj-a" in result["details"]
        assert isinstance(result["details"]["proj-a"], dict)


# ── 5. count_warm_instances ──────────────────────────────────────────


class TestCountWarmInstances:
    def test_zero_when_none_running(self, isolated_env):
        """LLM-017: Returns 0 when no CDP instances respond."""
        with patch.object(llm.urllib.request, "urlopen", side_effect=Exception("down")):
            count = llm.count_warm_instances()
        assert count == 0

    def test_counts_shared_chrome(self, isolated_env):
        """LLM-018: Shared Chrome — returns 1 when running, 0 when not."""
        # Chrome running on shared port 9222
        def fake_urlopen(url, timeout=3):
            if "/json/version" in url and "9222" in url:
                return _make_cdp_response()
            raise Exception("no connection")

        with patch.object(llm.urllib.request, "urlopen", side_effect=fake_urlopen):
            count = llm.count_warm_instances()
        assert count == 1  # One shared Chrome


# ── 6. load_resource_policy ──────────────────────────────────────────


class TestLoadResourcePolicy:
    def test_loads_policy(self, isolated_env):
        """LLM-019: Loads policy from file correctly."""
        policy = llm.load_resource_policy()
        assert policy["max_warm_cdp_instances"] == 2
        assert policy["max_active_gpt_reviews"] == 1
        assert policy["lazy_launch"] is True

    def test_fallback_when_missing(self, isolated_env, tmp_path):
        """LLM-020: Returns defaults when policy file is missing."""
        missing_path = tmp_path / "nonexistent" / "policy.json"
        # Point to a non-existent path
        import lazy_launch_manager as mod
        original = mod.POLICY_PATH
        mod.POLICY_PATH = missing_path
        try:
            policy = llm.load_resource_policy()
            assert policy["max_warm_cdp_instances"] == 4
            assert policy["max_active_gpt_reviews"] == 2
        finally:
            mod.POLICY_PATH = original


# ── 7. mark_stale ─────────────────────────────────────────────────────


class TestMarkStale:
    def test_mark_stale_success(self, isolated_env):
        """LLM-021: Successfully marks a project as stale."""
        result = llm.mark_stale("proj-a")
        assert result["action"] == "marked_stale"
        assert result["binding_status"] == llm.STATUS_STALE
        assert "stale_at" in result

        # Verify it persisted
        reg = json.loads(isolated_env["registry_path"].read_text(encoding="utf-8"))
        assert reg["projects"]["proj-a"]["binding_status"] == "stale"

    def test_mark_stale_unknown_project(self, isolated_env):
        """LLM-022: Marking unknown project returns error."""
        result = llm.mark_stale("does-not-exist")
        assert result["action"] == "error"
        assert "not found" in result["error"]


# ── 8. Stale detection ────────────────────────────────────────────────


class TestStaleDetection:
    def test_version_timeout_means_stale(self, isolated_env):
        """LLM-023: /json/version timeout on active project -> stale."""
        # proj-c has binding_status=active, simulate timeout
        with patch.object(
            llm.urllib.request, "urlopen",
            side_effect=TimeoutError("connection timed out")
        ):
            result = llm.get_project_status("proj-c")
        assert result["status"] == llm.STATUS_STALE

    def test_version_error_on_warm_project(self, isolated_env):
        """LLM-024: Connection error on a warm project -> stale."""
        # Set proj-a to warm first
        reg = json.loads(isolated_env["registry_path"].read_text(encoding="utf-8"))
        reg["projects"]["proj-a"]["binding_status"] = "warm"
        isolated_env["registry_path"].write_text(json.dumps(reg), encoding="utf-8")

        with patch.object(
            llm.urllib.request, "urlopen",
            side_effect=ConnectionRefusedError("refused")
        ):
            result = llm.get_project_status("proj-a")
        assert result["status"] == llm.STATUS_STALE
