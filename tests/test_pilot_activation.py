"""Tests for MULTI-AGENT-MULTI-GPT-PILOT-A1 activation mechanism."""

import json
import sys
import tempfile
import shutil
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))

REPO = Path(__file__).resolve().parent.parent
BINDING_PATH = REPO / ".agent" / "CONVERSATION_BINDING.json"
SCHEMA_PATH = REPO / ".agent" / "CONVERSATION_REGISTRY.schema.json"

from validate_conversation_registry import validate_binding
from awsp_scaffold import create_scaffold


# ── Fixtures ──────────────────────────────────────────────────────────


def _load_binding():
    return json.loads(BINDING_PATH.read_text(encoding="utf-8"))


def _make_scaffold(tmp: Path):
    """Create a fresh AWSP scaffold in a temp directory."""
    create_scaffold(str(tmp))
    return tmp / ".agent"


# ── TestPilotBindingActivation ────────────────────────────────────────


class TestPilotBindingActivation:
    """Verify the real CONVERSATION_BINDING.json reflects pilot activation."""

    def test_binding_has_two_agents(self):
        data = _load_binding()
        assert len(data["bindings"]) == 2

    def test_agent_local_001_is_active(self):
        data = _load_binding()
        agent = next(b for b in data["bindings"] if b["agent_id"] == "agent-local-001")
        assert agent["binding_status"] == "active"

    def test_agent_local_001_has_real_chat_url(self):
        data = _load_binding()
        agent = next(b for b in data["bindings"] if b["agent_id"] == "agent-local-001")
        assert agent["chat_url"] is not None
        assert agent["chat_url"].startswith("https://chatgpt.com/c/")
        assert "<" not in agent["chat_url"]  # not a placeholder

    def test_agent_local_001_has_real_conversation_id(self):
        data = _load_binding()
        agent = next(b for b in data["bindings"] if b["agent_id"] == "agent-local-001")
        assert agent["conversation_id"] is not None
        assert len(agent["conversation_id"]) > 10  # real UUID-like

    def test_agent_local_001_has_cdp_endpoint(self):
        data = _load_binding()
        agent = next(b for b in data["bindings"] if b["agent_id"] == "agent-local-001")
        assert agent["cdp_endpoint"] is not None
        assert agent["cdp_endpoint"].startswith("http://")

    def test_agent_pilot_beta_is_active(self):
        data = _load_binding()
        agent = next(b for b in data["bindings"] if b["agent_id"] == "agent-pilot-beta")
        assert agent["binding_status"] == "active"
        assert agent["chat_url"] is not None
        assert agent["chat_url"].startswith("https://chatgpt.com/c/")
        assert agent["conversation_id"] is not None
        assert len(agent["conversation_id"]) > 10

    def test_agent_pilot_beta_has_executor_role(self):
        data = _load_binding()
        agent = next(b for b in data["bindings"] if b["agent_id"] == "agent-pilot-beta")
        assert agent["role"] == "executor"

    def test_agent_ids_are_unique(self):
        data = _load_binding()
        ids = [b["agent_id"] for b in data["bindings"]]
        assert len(ids) == len(set(ids))

    def test_binding_validates_successfully(self):
        result = validate_binding(str(BINDING_PATH), project_root=str(REPO))
        assert result["valid"] is True
        assert result["schema_validated"] is True
        assert result["errors"] == []

    def test_binding_summary_counts(self):
        result = validate_binding(str(BINDING_PATH), project_root=str(REPO))
        summary = result["summary"]
        assert summary["binding_count"] == 2
        assert summary["active_count"] == 2
        assert summary["pending_count"] == 0

    def test_binding_passes_schema_validation(self):
        result = validate_binding(str(BINDING_PATH), project_root=str(REPO))
        assert result["details"]["schema_validation"] == "passed"
        assert result["details"]["schema_validation_errors"] == 0

    def test_capture_policy_preserved_for_active_agent(self):
        data = _load_binding()
        agent = next(b for b in data["bindings"] if b["agent_id"] == "agent-local-001")
        cp = agent["capture_policy"]
        assert cp["must_match_run_id"] is True
        assert cp["must_match_task_id"] is True
        assert cp["must_include_end_marker"] is True
        assert cp["forbid_last_message_only_capture"] is True


# ── TestPilotActivationSafetyGuards ────────────────────────────────────


class TestPilotActivationSafetyGuards:
    """Verify that activation safety guards still work after binding update."""

    def test_one_agent_one_conversation_policy(self):
        data = _load_binding()
        assert data["default_conversation_policy"] == "one_agent_one_conversation"

    def test_active_agents_have_distinct_conversations(self):
        data = _load_binding()
        active = [b for b in data["bindings"] if b["binding_status"] == "active"]
        conv_ids = [b.get("conversation_id") for b in active if b.get("conversation_id")]
        assert len(conv_ids) == len(set(conv_ids)), "Active agents share conversation IDs"

    def test_governance_scope_preserved(self):
        data = _load_binding()
        gs = data["governance_scope"]
        assert gs["default_execution_policy"] == "human_gated_for_external_runtime_execution"
        assert gs["forbid_ad_hoc_gpt_submission"] is True
        assert gs["forbid_cross_repo_smoke_without_human_gate"] is True

    def test_external_runtimes_preserved(self):
        data = _load_binding()
        runtimes = data["governance_scope"]["external_runtimes"]
        runtime_ids = {r["runtime_id"] for r in runtimes}
        assert runtime_ids == {
            "devframe-control-plane",
            "dev-frame-opencode",
            "paper-workflow",
        }

    def test_no_fabricated_pending_as_active(self):
        """Pending agents must not be reported as active."""
        data = _load_binding()
        for b in data["bindings"]:
            if b.get("chat_url") is None and b.get("conversation_id") is None:
                assert b["binding_status"] == "pending_manual_binding", (
                    f"{b['agent_id']} has no chat_url/conversation_id but is not pending"
                )


# ── TestPilotScaffoldActivationPath ───────────────────────────────────


class TestPilotScaffoldActivationPath:
    """Verify that a fresh scaffold can be activated through the same mechanism."""

    def test_fresh_scaffold_can_be_activated(self, tmp_path):
        agent_dir = _make_scaffold(tmp_path)
        binding_path = agent_dir / "CONVERSATION_BINDING.json"
        data = json.loads(binding_path.read_text(encoding="utf-8"))

        # Activate the first agent
        data["bindings"][0]["binding_status"] = "active"
        data["bindings"][0]["chat_url"] = "https://chatgpt.com/c/test-conv-id-12345"
        data["bindings"][0]["conversation_id"] = "test-conv-id-12345"
        binding_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

        resolved = str(tmp_path.resolve()).replace("\\", "/")
        result = validate_binding(str(binding_path), project_root=resolved)
        assert result["valid"] is True
        assert result["summary"]["active_count"] == 1

    def test_scaffold_rejects_active_without_real_url(self, tmp_path):
        agent_dir = _make_scaffold(tmp_path)
        binding_path = agent_dir / "CONVERSATION_BINDING.json"
        data = json.loads(binding_path.read_text(encoding="utf-8"))

        # Try to activate without real URL
        data["bindings"][0]["binding_status"] = "active"
        data["bindings"][0]["chat_url"] = "<placeholder>"
        binding_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

        resolved = str(tmp_path.resolve()).replace("\\", "/")
        result = validate_binding(str(binding_path), project_root=resolved)
        assert result["valid"] is False

    def test_scaffold_adds_second_agent(self, tmp_path):
        agent_dir = _make_scaffold(tmp_path)
        binding_path = agent_dir / "CONVERSATION_BINDING.json"
        data = json.loads(binding_path.read_text(encoding="utf-8"))

        # Add second agent
        second_agent = {
            "agent_id": "agent-pilot-beta",
            "role": "executor",
            "binding_status": "pending_manual_binding",
            "conversation_id": None,
            "chat_url": None,
            "browser_profile_id": None,
            "cdp_endpoint": None,
            "allowed_task_scope": ["*"],
            "capture_policy": {
                "must_match_run_id": True,
                "must_match_task_id": True,
                "must_include_end_marker": True,
                "forbid_last_message_only_capture": True,
            },
        }
        data["bindings"].append(second_agent)
        binding_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

        resolved = str(tmp_path.resolve()).replace("\\", "/")
        result = validate_binding(str(binding_path), project_root=resolved)
        assert result["valid"] is True
        assert result["summary"]["binding_count"] == 2

    def test_scaffold_rejects_duplicate_agent_on_activation(self, tmp_path):
        agent_dir = _make_scaffold(tmp_path)
        binding_path = agent_dir / "CONVERSATION_BINDING.json"
        data = json.loads(binding_path.read_text(encoding="utf-8"))

        # Add duplicate agent
        data["bindings"].append(dict(data["bindings"][0]))
        binding_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

        resolved = str(tmp_path.resolve()).replace("\\", "/")
        result = validate_binding(str(binding_path), project_root=resolved)
        assert result["valid"] is False
        assert any("duplicate" in e.lower() for e in result["errors"])


# ── TestPilotActivationRecord ─────────────────────────────────────────


class TestPilotActivationRecord:
    """Test the pilot_activation_record module."""

    def test_build_activation_record_structure(self):
        from pilot_activation_record import build_activation_record, verify_cdp_session

        binding_data = json.loads(BINDING_PATH.read_text(encoding="utf-8"))
        cdp_evidence = {
            "cdp_active": True,
            "browser": "Chrome/Test",
            "protocol_version": "1.3",
            "chat_pages": [{"type": "page", "url": binding_data["bindings"][0].get("chat_url", ""), "title": "Test"}],
            "chat_page_count": 1,
        }
        validation_result = validate_binding(str(BINDING_PATH), project_root=str(REPO))

        record = build_activation_record(BINDING_PATH, cdp_evidence, validation_result)

        assert record["pilot_id"] == "multi-agent-multi-gpt-pilot-a1"
        assert record["binding_valid"] is True
        assert record["schema_validated"] is True
        assert record["agent_summary"]["total"] == 2
        assert record["agent_summary"]["active"] == 2
        assert record["agent_summary"]["pending"] == 0
        assert len(record["active_agents"]) == 2
        assert len(record["pending_agents"]) == 0
        assert record["pilot_readiness"]["at_least_one_active"] is True
        assert record["pilot_readiness"]["at_least_two_agents"] is True
        assert record["pilot_readiness"]["all_agents_active"] is True

    def test_activation_record_cdp_verification(self):
        from pilot_activation_record import build_activation_record

        binding_data = json.loads(BINDING_PATH.read_text(encoding="utf-8"))
        active_agent = next(b for b in binding_data["bindings"] if b["binding_status"] == "active")
        conv_id = active_agent.get("conversation_id", "")

        # CDP with matching conversation
        cdp_evidence = {
            "cdp_active": True,
            "browser": "Chrome/Test",
            "chat_pages": [{"type": "page", "url": f"https://chatgpt.com/c/{conv_id}", "title": "Test"}],
            "chat_page_count": 1,
        }
        validation_result = validate_binding(str(BINDING_PATH), project_root=str(REPO))
        record = build_activation_record(BINDING_PATH, cdp_evidence, validation_result)

        assert record["active_agents"][0]["cdp_session_verified"] is True

    def test_activation_record_cdp_not_verified_when_no_match(self):
        from pilot_activation_record import build_activation_record

        cdp_evidence = {
            "cdp_active": True,
            "browser": "Chrome/Test",
            "chat_pages": [{"type": "page", "url": "https://chatgpt.com/c/wrong-id", "title": "Test"}],
            "chat_page_count": 1,
        }
        validation_result = validate_binding(str(BINDING_PATH), project_root=str(REPO))
        record = build_activation_record(BINDING_PATH, cdp_evidence, validation_result)

        assert record["active_agents"][0]["cdp_session_verified"] is False
