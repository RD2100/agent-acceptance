import json
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))

import validate_project_registry_bindings as validator  # noqa: E402


def _write_binding(root: Path, project_id: str, status: str, conversation_id: str) -> None:
    agent_dir = root / ".agent"
    agent_dir.mkdir(parents=True)
    data = {
        "schema_version": "1.0.0",
        "awsp_version": "1.3.0",
        "project_id": project_id,
        "project_root": str(root),
        "default_conversation_policy": "one_agent_one_conversation",
        "bindings": [
            {
                "agent_id": f"agent-{project_id}",
                "role": "executor",
                "binding_status": status,
                "conversation_id": conversation_id,
                "chat_url": f"https://chatgpt.com/c/{conversation_id}",
                "cdp_endpoint": "http://localhost:9222",
                "allowed_task_scope": ["*"],
                "capture_policy": {
                    "must_match_run_id": True,
                    "must_match_task_id": True,
                    "must_include_end_marker": True,
                    "forbid_last_message_only_capture": True,
                },
            }
        ],
    }
    (agent_dir / "CONVERSATION_BINDING.json").write_text(
        json.dumps(data, indent=2),
        encoding="utf-8",
    )


def _write_registry(registry_path: Path, projects: dict) -> None:
    registry_path.parent.mkdir(parents=True)
    registry = {
        "schema_version": "2.0.0",
        "total_projects": len(projects),
        "projects": projects,
    }
    registry_path.write_text(json.dumps(registry, indent=2), encoding="utf-8")


def _project(root: Path, project_id: str, status: str) -> dict:
    return {
        "project_id": project_id,
        "project_root": str(root),
        "binding_status": status,
    }


def test_suspended_project_duplicate_conversation_is_not_blocking(monkeypatch, tmp_path, capsys):
    active_root = tmp_path / "active"
    suspended_root = tmp_path / "suspended"
    _write_binding(active_root, "active-project", "active", "same-conversation")
    _write_binding(suspended_root, "suspended-project", "suspended", "same-conversation")

    registry_path = tmp_path / ".agent" / "PROJECT_REGISTRY.json"
    _write_registry(
        registry_path,
        {
            "active-project": _project(active_root, "active-project", "active"),
            "suspended-project": _project(suspended_root, "suspended-project", "suspended"),
        },
    )
    monkeypatch.setattr(validator, "REGISTRY", registry_path)

    assert validator.validate() is True
    output = capsys.readouterr().out
    assert "[PASS] Rule 8: no duplicate active conversation_id" in output
    assert "suspended -> NO AUTO-SUBMIT -> SAFE" in output


def test_non_active_binding_duplicate_conversation_is_not_blocking(monkeypatch, tmp_path):
    active_root = tmp_path / "active"
    paused_root = tmp_path / "paused-binding"
    _write_binding(active_root, "active-project", "active", "same-conversation")
    _write_binding(paused_root, "paused-binding-project", "paused", "same-conversation")

    registry_path = tmp_path / ".agent" / "PROJECT_REGISTRY.json"
    _write_registry(
        registry_path,
        {
            "active-project": _project(active_root, "active-project", "active"),
            "paused-binding-project": _project(paused_root, "paused-binding-project", "active"),
        },
    )
    monkeypatch.setattr(validator, "REGISTRY", registry_path)

    assert validator.validate() is True


def test_duplicate_active_conversation_still_blocks(monkeypatch, tmp_path, capsys):
    first_root = tmp_path / "first"
    second_root = tmp_path / "second"
    _write_binding(first_root, "first-project", "active", "same-conversation")
    _write_binding(second_root, "second-project", "active", "same-conversation")

    registry_path = tmp_path / ".agent" / "PROJECT_REGISTRY.json"
    _write_registry(
        registry_path,
        {
            "first-project": _project(first_root, "first-project", "active"),
            "second-project": _project(second_root, "second-project", "active"),
        },
    )
    monkeypatch.setattr(validator, "REGISTRY", registry_path)

    assert validator.validate() is False
    output = capsys.readouterr().out
    assert "[FAIL] Rule 8: no duplicate active conversation_id" in output
    assert "same-conversation" in output
