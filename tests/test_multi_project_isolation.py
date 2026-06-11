"""Tests for Multi-Project Isolation Architecture (v2 — Single Chrome).

Covers:
- multi_cdp_launcher.py: registry management, Chrome launch, port check, instance verify
- multi_project_router.py: resolve_target, resolve_all, build_dispatch_packet, verify_isolation
- Architecture: single Chrome + multi-conversation isolation
"""

import json
import sys
import types
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

REPO = Path(__file__).resolve().parent.parent
SCRIPTS = REPO / "scripts"
sys.path.insert(0, str(SCRIPTS))


# ── Helpers ─────────────────────────────────────────────────────────────

def _make_registry(projects: dict | None = None) -> dict:
    """Build a synthetic PROJECT_REGISTRY.json (v2 shared-CDP)."""
    return {
        "schema_version": "2.0.0",
        "awsp_version": "1.3.0",
        "architecture": "single_chrome_shared_cdp",
        "generated_at": "2026-06-10T00:00:00Z",
        "shared_cdp_port": 9222,
        "shared_cdp_endpoint": "http://localhost:9222",
        "shared_profile_dir": "/tmp/shared_profile",
        "projects": projects or {},
    }


def _make_binding(agents: list[dict] | None = None) -> dict:
    """Build a synthetic CONVERSATION_BINDING.json (v2 shared-CDP)."""
    return {
        "schema_version": "2.0.0",
        "awsp_version": "1.3.0",
        "project_id": "test-project",
        "project_root": "/tmp/test",
        "architecture": "single_chrome_shared_cdp",
        "bindings": agents or [],
    }


def _sample_agent(agent_id: str, role: str, conv_id: str) -> dict:
    """Build a sample agent binding (no browser_profile_id — shared Chrome)."""
    return {
        "agent_id": agent_id,
        "role": role,
        "binding_status": "active",
        "conversation_id": conv_id,
        "chat_url": f"https://chatgpt.com/c/{conv_id}",
        "cdp_endpoint": "http://localhost:9222",
        "allowed_task_scope": ["*"],
        "capture_policy": {
            "must_match_run_id": True,
            "must_match_task_id": True,
            "must_include_end_marker": True,
            "forbid_last_message_only_capture": True,
        },
    }


# ── TestMultiCdpLauncherModule ──────────────────────────────────────────


class TestMultiCdpLauncherModule:
    """Verify multi_cdp_launcher.py is importable and has key functions."""

    def test_import_module(self):
        import multi_cdp_launcher
        assert hasattr(multi_cdp_launcher, "load_registry")
        assert hasattr(multi_cdp_launcher, "save_registry")
        assert hasattr(multi_cdp_launcher, "launch_chrome")
        assert hasattr(multi_cdp_launcher, "verify_instance")

    def test_chrome_paths_list(self):
        import multi_cdp_launcher
        assert isinstance(multi_cdp_launcher.CHROME_PATHS, list)
        assert len(multi_cdp_launcher.CHROME_PATHS) >= 3

    def test_default_cdp_port(self):
        import multi_cdp_launcher
        assert multi_cdp_launcher.DEFAULT_CDP_PORT == 9222

    def test_default_profile_dir_is_shared(self):
        import multi_cdp_launcher
        assert "shared" in str(multi_cdp_launcher.DEFAULT_PROFILE_DIR)

    def test_has_list_chatgpt_tabs(self):
        import multi_cdp_launcher
        assert hasattr(multi_cdp_launcher, "list_chatgpt_tabs")


# ── TestRegistryManagement ──────────────────────────────────────────────


class TestRegistryManagement:
    """Test load/save of PROJECT_REGISTRY.json with isolated filesystem."""

    def test_load_registry_returns_default_when_missing(self, tmp_path, monkeypatch):
        import multi_cdp_launcher
        fake_path = tmp_path / ".agent" / "PROJECT_REGISTRY.json"
        monkeypatch.setattr(multi_cdp_launcher, "REGISTRY_PATH", fake_path)
        reg = multi_cdp_launcher.load_registry()
        assert reg["schema_version"] == "2.0.0"
        assert reg["awsp_version"] == "1.3.0"
        assert reg["architecture"] == "single_chrome_shared_cdp"
        assert reg["projects"] == {}

    def test_load_registry_reads_existing(self, tmp_path, monkeypatch):
        import multi_cdp_launcher
        agent_dir = tmp_path / ".agent"
        agent_dir.mkdir()
        reg_path = agent_dir / "PROJECT_REGISTRY.json"
        data = _make_registry({"proj-a": {"project_root": "/tmp/a"}})
        reg_path.write_text(json.dumps(data), encoding="utf-8")
        monkeypatch.setattr(multi_cdp_launcher, "REGISTRY_PATH", reg_path)
        reg = multi_cdp_launcher.load_registry()
        assert "proj-a" in reg["projects"]

    def test_save_registry_creates_file(self, tmp_path, monkeypatch):
        import multi_cdp_launcher
        reg_path = tmp_path / ".agent" / "PROJECT_REGISTRY.json"
        monkeypatch.setattr(multi_cdp_launcher, "REGISTRY_PATH", reg_path)
        reg = _make_registry({"proj-x": {"project_root": "/tmp/x"}})
        multi_cdp_launcher.save_registry(reg)
        assert reg_path.exists()
        loaded = json.loads(reg_path.read_text(encoding="utf-8"))
        assert "proj-x" in loaded["projects"]
        assert "updated_at" in loaded

    def test_save_registry_round_trip(self, tmp_path, monkeypatch):
        import multi_cdp_launcher
        reg_path = tmp_path / ".agent" / "PROJECT_REGISTRY.json"
        monkeypatch.setattr(multi_cdp_launcher, "REGISTRY_PATH", reg_path)
        reg = _make_registry({"p1": {"project_root": "/a"}, "p2": {"project_root": "/b"}})
        multi_cdp_launcher.save_registry(reg)
        loaded = multi_cdp_launcher.load_registry()
        assert len(loaded["projects"]) == 2

    def test_registry_has_shared_architecture(self, tmp_path, monkeypatch):
        import multi_cdp_launcher
        reg_path = tmp_path / ".agent" / "PROJECT_REGISTRY.json"
        monkeypatch.setattr(multi_cdp_launcher, "REGISTRY_PATH", reg_path)
        # load_registry returns defaults for missing file
        reg = multi_cdp_launcher.load_registry()
        assert reg["architecture"] == "single_chrome_shared_cdp"
        # After save + reload, shared fields are present
        multi_cdp_launcher.save_registry(reg)
        loaded = multi_cdp_launcher.load_registry()
        assert loaded["shared_cdp_endpoint"] == "http://localhost:9222"


# ── TestPortAndInstanceChecks ──────────────────────────────────────────


class TestPortAndInstanceChecks:
    """Test _check_port and verify_instance with mocked network calls."""

    def test_check_port_returns_false_when_unreachable(self):
        import multi_cdp_launcher
        assert multi_cdp_launcher._check_port(19999) is False

    def test_check_port_returns_true_on_success(self):
        import multi_cdp_launcher
        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        with patch("urllib.request.urlopen", return_value=mock_resp):
            assert multi_cdp_launcher._check_port(9222) is True

    def test_verify_instance_inactive_when_unreachable(self):
        import multi_cdp_launcher
        result = multi_cdp_launcher.verify_instance(19999)
        assert result["port"] == 19999
        assert result["active"] is False

    def test_verify_instance_active_with_mock(self):
        import multi_cdp_launcher
        version_data = {"Browser": "Chrome/125.0", "Protocol-Version": "1.3"}
        pages_data = [
            {"url": "https://chatgpt.com/c/abc"},
            {"url": "https://example.com"},
        ]

        def mock_urlopen(url, timeout=3):
            resp = MagicMock()
            resp.status = 200
            resp.__enter__ = lambda s: s
            resp.__exit__ = MagicMock(return_value=False)
            if "/json/version" in url:
                resp.read = lambda: json.dumps(version_data).encode()
            elif url.endswith("/json"):
                resp.read = lambda: json.dumps(pages_data).encode()
            return resp

        with patch("urllib.request.urlopen", side_effect=mock_urlopen):
            result = multi_cdp_launcher.verify_instance(9222)
            assert result["active"] is True
            assert result["browser"] == "Chrome/125.0"
            assert result["total_pages"] == 2
            assert result["chatgpt_pages"] == 1

    def test_list_chatgpt_tabs_extracts_conv_id(self):
        import multi_cdp_launcher
        pages = [
            {"url": "https://chatgpt.com/c/conv-123", "title": "Test Chat"},
            {"url": "https://example.com", "title": "Other"},
            {"url": "https://chatgpt.com/c/conv-456?foo=bar", "title": "Chat 2"},
        ]
        with patch.object(multi_cdp_launcher, "_get_pages", return_value=pages):
            tabs = multi_cdp_launcher.list_chatgpt_tabs(9222)
        assert len(tabs) == 2
        assert tabs[0]["conversation_id"] == "conv-123"
        assert tabs[1]["conversation_id"] == "conv-456"


# ── TestLaunchChrome ────────────────────────────────────────────────────


class TestLaunchChrome:
    """Test launch_chrome with single-Chrome architecture."""

    def test_launch_chrome_no_chrome_found(self, tmp_path):
        import multi_cdp_launcher
        result = multi_cdp_launcher.launch_chrome(
            port=9222, profile_dir=tmp_path / "shared", chrome_path=None
        )
        assert "launched" in result or "error" in result
        assert result.get("launched") is not None

    def test_launch_chrome_already_active(self, tmp_path):
        import multi_cdp_launcher
        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        version_data = {"Browser": "Chrome/125.0"}
        mock_resp.read = lambda: json.dumps(version_data).encode()
        with patch("urllib.request.urlopen", return_value=mock_resp):
            result = multi_cdp_launcher.launch_chrome(
                port=9222, profile_dir=tmp_path / "shared",
                chrome_path="C:\\fake\\chrome.exe",
            )
            assert result["launched"] is False
            assert result["already_active"] is True
            assert result["cdp_endpoint"] == "http://localhost:9222"

    def test_launch_chrome_creates_shared_profile(self, tmp_path):
        import multi_cdp_launcher
        mock_proc = MagicMock()
        mock_proc.pid = 12345
        profile = tmp_path / "shared"
        with patch.object(multi_cdp_launcher, "_check_port", return_value=False):
            with patch("subprocess.Popen", return_value=mock_proc):
                result = multi_cdp_launcher.launch_chrome(
                    port=9222, profile_dir=profile,
                    chrome_path="C:\\fake\\chrome.exe",
                )
                assert result["launched"] is True
                assert result["pid"] == 12345
                assert result["cdp_endpoint"] == "http://localhost:9222"
                assert result["profile_dir"] == str(profile)
                assert profile.exists()

    def test_launch_uses_single_port(self, tmp_path):
        """All projects share port 9222 — only one Chrome is launched."""
        import multi_cdp_launcher
        mock_proc = MagicMock()
        mock_proc.pid = 99999
        with patch("subprocess.Popen", return_value=mock_proc):
            result = multi_cdp_launcher.launch_chrome(
                port=multi_cdp_launcher.DEFAULT_CDP_PORT,
                profile_dir=tmp_path / "shared",
                chrome_path="C:\\fake\\chrome.exe",
            )
            assert result["cdp_endpoint"] == "http://localhost:9222"


# ── TestMultiProjectRouterModule ────────────────────────────────────────


class TestMultiProjectRouterModule:
    """Verify multi_project_router.py is importable and has key functions."""

    def test_import_module(self):
        import multi_project_router
        assert hasattr(multi_project_router, "resolve_target")
        assert hasattr(multi_project_router, "resolve_all")
        assert hasattr(multi_project_router, "build_dispatch_packet")
        assert hasattr(multi_project_router, "verify_isolation")
        assert hasattr(multi_project_router, "load_registry")
        assert hasattr(multi_project_router, "load_binding")


# ── TestResolveTarget ───────────────────────────────────────────────────


class TestResolveTarget:
    """Test router resolve_target with synthetic registry and binding."""

    def _setup_project(self, tmp_path, project_id, conv_id):
        """Create a synthetic project with registry + binding."""
        agent_dir = tmp_path / project_id / ".agent"
        agent_dir.mkdir(parents=True)

        binding = _make_binding([
            _sample_agent(f"agent-{project_id}", "executor", conv_id)
        ])
        (agent_dir / "CONVERSATION_BINDING.json").write_text(
            json.dumps(binding), encoding="utf-8"
        )
        return {
            "project_id": project_id,
            "project_root": str(tmp_path / project_id),
            "registered_at": "2026-06-10T00:00:00Z",
        }

    def test_resolve_unknown_project(self, tmp_path, monkeypatch):
        import multi_project_router
        reg_path = tmp_path / "PROJECT_REGISTRY.json"
        reg_path.write_text(json.dumps(_make_registry({})), encoding="utf-8")
        monkeypatch.setattr(multi_project_router, "REGISTRY_PATH", reg_path)
        result = multi_project_router.resolve_target("nonexistent")
        assert result["resolved"] is False
        assert "not found" in result["error"]

    def test_resolve_no_binding(self, tmp_path, monkeypatch):
        import multi_project_router
        project_root = tmp_path / "proj-empty"
        project_root.mkdir()
        reg = _make_registry({
            "proj-empty": {
                "project_root": str(project_root),
            }
        })
        reg_path = tmp_path / "PROJECT_REGISTRY.json"
        reg_path.write_text(json.dumps(reg), encoding="utf-8")
        monkeypatch.setattr(multi_project_router, "REGISTRY_PATH", reg_path)
        result = multi_project_router.resolve_target("proj-empty", str(project_root))
        assert result["resolved"] is False
        assert "not found" in result["error"].lower() or "binding" in result["error"].lower()

    def test_resolve_no_active_agent(self, tmp_path, monkeypatch):
        import multi_project_router
        project_root = tmp_path / "proj-inactive"
        agent_dir = project_root / ".agent"
        agent_dir.mkdir(parents=True)
        binding = _make_binding([
            {**_sample_agent("agent-x", "executor", "conv-1"),
             "binding_status": "pending"}
        ])
        (agent_dir / "CONVERSATION_BINDING.json").write_text(
            json.dumps(binding), encoding="utf-8"
        )
        reg = _make_registry({
            "proj-inactive": {
                "project_root": str(project_root),
            }
        })
        reg_path = tmp_path / "PROJECT_REGISTRY.json"
        reg_path.write_text(json.dumps(reg), encoding="utf-8")
        monkeypatch.setattr(multi_project_router, "REGISTRY_PATH", reg_path)
        result = multi_project_router.resolve_target("proj-inactive", str(project_root))
        assert result["resolved"] is False
        assert "no active" in result["error"].lower()

    def test_resolve_success(self, tmp_path, monkeypatch):
        import multi_project_router
        proj = self._setup_project(tmp_path, "proj-ok", "conv-abc")
        reg = _make_registry({"proj-ok": proj})
        reg_path = tmp_path / "PROJECT_REGISTRY.json"
        reg_path.write_text(json.dumps(reg), encoding="utf-8")
        monkeypatch.setattr(multi_project_router, "REGISTRY_PATH", reg_path)
        with patch.object(multi_project_router, "_check_cdp", return_value=False):
            result = multi_project_router.resolve_target("proj-ok", proj["project_root"])
        assert result["resolved"] is True
        assert result["cdp_endpoint"] == "http://localhost:9222"  # shared
        assert result["conversation_id"] == "conv-abc"
        assert result["agent_id"] == "agent-proj-ok"
        assert result["agent_role"] == "executor"
        assert result["binding_status"] == "active"
        assert result["chat_url"] == "https://chatgpt.com/c/conv-abc"

    def test_resolve_uses_shared_cdp_endpoint(self, tmp_path, monkeypatch):
        """All projects must resolve to the same shared CDP endpoint."""
        import multi_project_router
        projects = {}
        for pid, conv in [("proj-a", "conv-a"), ("proj-b", "conv-b")]:
            p = self._setup_project(tmp_path, pid, conv)
            projects[pid] = p
        reg = _make_registry(projects)
        reg_path = tmp_path / "PROJECT_REGISTRY.json"
        reg_path.write_text(json.dumps(reg), encoding="utf-8")
        monkeypatch.setattr(multi_project_router, "REGISTRY_PATH", reg_path)
        with patch.object(multi_project_router, "_check_cdp", return_value=False):
            r1 = multi_project_router.resolve_target("proj-a", projects["proj-a"]["project_root"])
            r2 = multi_project_router.resolve_target("proj-b", projects["proj-b"]["project_root"])
        # Same CDP endpoint for both — shared Chrome
        assert r1["cdp_endpoint"] == r2["cdp_endpoint"]
        # Different conversations — isolation
        assert r1["conversation_id"] != r2["conversation_id"]


# ── TestResolveAll ──────────────────────────────────────────────────────


class TestResolveAll:
    """Test resolve_all returns targets for every registered project."""

    def test_resolve_all_empty_registry(self, tmp_path, monkeypatch):
        import multi_project_router
        reg_path = tmp_path / "PROJECT_REGISTRY.json"
        reg_path.write_text(json.dumps(_make_registry({})), encoding="utf-8")
        monkeypatch.setattr(multi_project_router, "REGISTRY_PATH", reg_path)
        results = multi_project_router.resolve_all()
        assert results == []

    def test_resolve_all_multiple_projects(self, tmp_path, monkeypatch):
        import multi_project_router
        projects = {}
        for pid, conv in [("alpha", "conv-a"), ("beta", "conv-b")]:
            proj_dir = tmp_path / pid
            agent_dir = proj_dir / ".agent"
            agent_dir.mkdir(parents=True)
            binding = _make_binding([
                _sample_agent(f"agent-{pid}", "executor", conv)
            ])
            (agent_dir / "CONVERSATION_BINDING.json").write_text(
                json.dumps(binding), encoding="utf-8"
            )
            projects[pid] = {
                "project_id": pid,
                "project_root": str(proj_dir),
                "registered_at": "2026-06-10T00:00:00Z",
            }

        reg = _make_registry(projects)
        reg_path = tmp_path / "PROJECT_REGISTRY.json"
        reg_path.write_text(json.dumps(reg), encoding="utf-8")
        monkeypatch.setattr(multi_project_router, "REGISTRY_PATH", reg_path)

        with patch.object(multi_project_router, "_check_cdp", return_value=False):
            results = multi_project_router.resolve_all()
        assert len(results) == 2
        resolved = [r for r in results if r.get("resolved")]
        assert len(resolved) == 2
        # All share same CDP endpoint
        endpoints = {r["cdp_endpoint"] for r in resolved}
        assert len(endpoints) == 1


# ── TestBuildDispatchPacket ─────────────────────────────────────────────


class TestBuildDispatchPacket:
    """Test dispatch packet construction."""

    def test_packet_unresolved_target(self):
        import multi_project_router
        target = {"resolved": False, "error": "not found"}
        packet = multi_project_router.build_dispatch_packet(target, {}, "hello")
        assert packet["dispatchable"] is False
        assert packet["error"] == "not found"

    def test_packet_resolved_target(self):
        import multi_project_router
        target = {
            "resolved": True,
            "project_id": "proj-a",
            "cdp_endpoint": "http://localhost:9222",
            "cdp_active": True,
            "conversation_id": "conv-123",
            "chat_url": "https://chatgpt.com/c/conv-123",
            "target_id": "cdp-target-proj-a",
            "target_url": "https://chatgpt.com/c/conv-123",
            "tab_match_status": "exact_match",
            "agent_id": "agent-1",
            "agent_role": "executor",
        }
        task_spec = {"task_id": "T-001", "description": "test task"}
        msg = "Please execute this task."
        packet = multi_project_router.build_dispatch_packet(target, task_spec, msg)
        assert packet["dispatchable"] is True
        assert packet["project_id"] == "proj-a"
        assert packet["cdp_endpoint"] == "http://localhost:9222"
        assert packet["conversation_id"] == "conv-123"
        assert packet["agent_id"] == "agent-1"
        assert packet["task_spec"]["task_id"] == "T-001"
        assert packet["message_text"] == msg
        assert packet["message_length"] == len(msg)
        assert "built_at" in packet


# ── TestVerifyIsolation ────────────────────────────────────────────────


class TestVerifyIsolation:
    """Test multi-project isolation — conversation_id is the only check."""

    def test_empty_targets_isolated(self):
        import multi_project_router
        result = multi_project_router.verify_isolation([])
        assert result["isolated"] is True
        assert result["total_projects"] == 0

    def test_single_target_isolated(self):
        import multi_project_router
        targets = [{
            "resolved": True,
            "project_id": "proj-a",
            "cdp_endpoint": "http://localhost:9222",
            "conversation_id": "conv-a",
        }]
        result = multi_project_router.verify_isolation(targets)
        assert result["isolated"] is True
        assert result["total_projects"] == 1
        assert result["unique_conversations"] == 1
        assert result["issues"] == []

    def test_two_projects_same_cdp_different_conv_isolated(self):
        """Two projects on the same Chrome — different conversations — is isolated."""
        import multi_project_router
        targets = [
            {
                "resolved": True,
                "project_id": "proj-a",
                "cdp_endpoint": "http://localhost:9222",
                "conversation_id": "conv-a",
            },
            {
                "resolved": True,
                "project_id": "proj-b",
                "cdp_endpoint": "http://localhost:9222",  # same CDP — expected!
                "conversation_id": "conv-b",  # different conv — isolated
            },
        ]
        result = multi_project_router.verify_isolation(targets)
        assert result["isolated"] is True
        assert result["total_projects"] == 2
        assert result["unique_conversations"] == 2
        assert result["issues"] == []

    def test_conversation_collision_detected(self):
        import multi_project_router
        targets = [
            {
                "resolved": True,
                "project_id": "proj-a",
                "cdp_endpoint": "http://localhost:9222",
                "conversation_id": "same-conv",
            },
            {
                "resolved": True,
                "project_id": "proj-b",
                "cdp_endpoint": "http://localhost:9222",
                "conversation_id": "same-conv",  # collision!
            },
        ]
        result = multi_project_router.verify_isolation(targets)
        assert result["isolated"] is False
        assert len(result["issues"]) >= 1
        assert any("Conversation collision" in i for i in result["issues"])

    def test_unresolved_targets_skipped(self):
        import multi_project_router
        targets = [
            {"resolved": False, "project_id": "broken", "error": "not found"},
            {
                "resolved": True,
                "project_id": "proj-a",
                "cdp_endpoint": "http://localhost:9222",
                "conversation_id": "conv-a",
            },
        ]
        result = multi_project_router.verify_isolation(targets)
        assert result["isolated"] is True
        assert result["total_projects"] == 1  # Only resolved counted

    def test_three_projects_all_isolated(self):
        import multi_project_router
        targets = [
            {
                "resolved": True, "project_id": f"proj-{i}",
                "cdp_endpoint": "http://localhost:9222",  # all same Chrome
                "conversation_id": f"conv-{i}",  # different conversations
            }
            for i in range(3)
        ]
        result = multi_project_router.verify_isolation(targets)
        assert result["isolated"] is True
        assert result["total_projects"] == 3
        assert result["unique_conversations"] == 3

    def test_ten_projects_all_isolated(self):
        """Stress test: 10 projects on shared Chrome, each with unique conversation."""
        import multi_project_router
        targets = [
            {
                "resolved": True,
                "project_id": f"proj-{i:03d}",
                "cdp_endpoint": "http://localhost:9222",
                "conversation_id": f"conv-{i:03d}",
            }
            for i in range(10)
        ]
        result = multi_project_router.verify_isolation(targets)
        assert result["isolated"] is True
        assert result["total_projects"] == 10
        assert result["unique_conversations"] == 10

    def test_has_timestamp(self):
        import multi_project_router
        result = multi_project_router.verify_isolation([])
        assert "checked_at" in result


# ── TestExistingProjectRegistry ─────────────────────────────────────────


class TestExistingProjectInfrastructure:
    """Verify the existing project (agent-acceptance) infrastructure is intact."""

    def test_conversation_binding_exists(self):
        binding_path = REPO / ".agent" / "CONVERSATION_BINDING.json"
        assert binding_path.exists()

    def test_conversation_binding_has_two_agents(self):
        binding_path = REPO / ".agent" / "CONVERSATION_BINDING.json"
        data = json.loads(binding_path.read_text(encoding="utf-8"))
        active = [b for b in data["bindings"] if b["binding_status"] == "active"]
        assert len(active) == 2

    def test_agents_have_distinct_conversations(self):
        binding_path = REPO / ".agent" / "CONVERSATION_BINDING.json"
        data = json.loads(binding_path.read_text(encoding="utf-8"))
        conv_ids = [b["conversation_id"] for b in data["bindings"]]
        assert len(conv_ids) == len(set(conv_ids)), "Agents must have unique conversation IDs"

    def test_scripts_exist(self):
        assert (SCRIPTS / "multi_cdp_launcher.py").exists()
        assert (SCRIPTS / "multi_project_router.py").exists()

    def test_scripts_importable(self):
        import multi_cdp_launcher
        import multi_project_router
        # Both should import without error

    def test_registry_v2_architecture(self):
        """Registry must declare single_chrome_shared_cdp architecture."""
        import multi_cdp_launcher
        reg = multi_cdp_launcher.load_registry()
        assert reg.get("architecture") == "single_chrome_shared_cdp"
        assert reg.get("shared_cdp_endpoint") == "http://localhost:9222"


# ── TestMultiProjectArchitecture ────────────────────────────────────────


class TestMultiProjectArchitecture:
    """Verify the architectural guarantees of the v2 shared-Chrome model."""

    def test_registry_schema_has_required_fields(self):
        import multi_cdp_launcher
        reg = multi_cdp_launcher.load_registry()
        assert "schema_version" in reg
        assert "awsp_version" in reg
        assert "projects" in reg
        assert isinstance(reg["projects"], dict)

    def test_binding_load_returns_empty_for_missing(self, tmp_path):
        import multi_project_router
        result = multi_project_router.load_binding(tmp_path / "nonexistent")
        assert result == {}

    def test_binding_load_returns_data(self, tmp_path):
        import multi_project_router
        agent_dir = tmp_path / ".agent"
        agent_dir.mkdir()
        binding = _make_binding([_sample_agent("a1", "executor", "c1")])
        (agent_dir / "CONVERSATION_BINDING.json").write_text(
            json.dumps(binding), encoding="utf-8"
        )
        result = multi_project_router.load_binding(tmp_path)
        assert len(result["bindings"]) == 1
        assert result["bindings"][0]["agent_id"] == "a1"

    def test_dispatch_packet_includes_all_routing_info(self):
        import multi_project_router
        target = {
            "resolved": True,
            "project_id": "p1",
            "cdp_endpoint": "http://localhost:9222",
            "cdp_active": True,
            "conversation_id": "c1",
            "chat_url": "https://chatgpt.com/c/c1",
            "target_id": "cdp-target-p1",
            "target_url": "https://chatgpt.com/c/c1",
            "tab_match_status": "exact_match",
            "agent_id": "a1",
            "agent_role": "executor",
        }
        packet = multi_project_router.build_dispatch_packet(
            target, {"task_id": "T1"}, "do it"
        )
        required_keys = [
            "dispatchable", "project_id", "cdp_endpoint", "cdp_active",
            "conversation_id", "chat_url", "agent_id", "agent_role",
            "task_spec", "message_text", "message_length", "built_at",
        ]
        for key in required_keys:
            assert key in packet, f"Missing key: {key}"

    def test_shared_cdp_does_not_break_isolation(self):
        """Core guarantee: shared CDP endpoint + unique conversations = isolated."""
        import multi_project_router
        targets = [
            {
                "resolved": True,
                "project_id": f"proj-{i}",
                "cdp_endpoint": "http://localhost:9222",  # ALL share
                "conversation_id": f"unique-conv-{i}",  # ALL different
            }
            for i in range(10)
        ]
        result = multi_project_router.verify_isolation(targets)
        assert result["isolated"] is True
        assert result["total_projects"] == 10
        assert result["unique_conversations"] == 10
        assert result["issues"] == []
