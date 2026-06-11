"""Tests for the multi-agent Gate 0 preflight."""

import json
import subprocess
import sys
from pathlib import Path

from jsonschema import Draft202012Validator

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))

from awsp_scaffold import create_scaffold
from multi_agent_gate0_preflight import evaluate_preflight

REPO = Path(__file__).resolve().parent.parent
SCHEMA_PATH = REPO / "schemas" / "agent-runtime" / "multi-agent-gate0-preflight.schema.json"


def _schema_validator() -> Draft202012Validator:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


def _assert_schema_valid(report: dict) -> None:
    errors = sorted(
        _schema_validator().iter_errors(report),
        key=lambda err: list(err.absolute_path),
    )
    assert errors == []


def _write_runtime_docs(root: Path, *, executable: bool = True) -> None:
    docs = root / "docs" / "agent-runtime"
    docs.mkdir(parents=True)
    status = "approved" if executable else "proposed"
    usable_execution = "true" if executable else "false"
    (docs / "capability-inventory.md").write_text(
        f"""# Capability Inventory

## 29. dev-frame-opencode Dispatch
- **Status**: {status}
- **Passport usable_for_gate0**: true
- **Passport usable_for_execution**: {usable_execution}
""",
        encoding="utf-8",
    )
    (docs / "tool-policy.md").write_text(
        """# Tool Policy

| `opencode run` / dev-frame-opencode dispatch | proposed capability, human-gated |
| Cross-repo pytest/smoke scripts | human-gated |
| Paper workflow | pilot-only unless authorized |

legacy `authorized=true` JSON file is not sufficient
""",
        encoding="utf-8",
    )


def _activate_binding(binding_path: Path, agent_id: str, conversation_id: str) -> None:
    data = json.loads(binding_path.read_text(encoding="utf-8"))
    data["bindings"][0]["agent_id"] = agent_id
    data["bindings"][0]["binding_status"] = "active"
    data["bindings"][0]["conversation_id"] = conversation_id
    data["bindings"][0]["chat_url"] = None
    binding_path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def test_current_repo_preflight_passes_pilot_ready():
    """Current workspace pilot is fully activated, gate0 should PASS."""
    exit_code, report = evaluate_preflight(REPO)

    _assert_schema_valid(report)
    assert exit_code == 0
    assert report["overall"] == "PASS"
    assert report["executed_external_runtime"] is False


def test_cli_output_writes_same_schema_valid_report(tmp_path):
    """CLI --output writes the same report JSON while preserving current exit semantics."""
    output_path = tmp_path / "nested" / "gate0" / "preflight.json"

    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPTS / "multi_agent_gate0_preflight.py"),
            "--output",
            str(output_path),
        ],
        cwd=REPO,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    stdout_report = json.loads(result.stdout)
    file_report = json.loads(output_path.read_text(encoding="utf-8"))
    assert file_report == stdout_report
    _assert_schema_valid(file_report)
    assert file_report["overall"] == "PASS"
    assert file_report["executed_external_runtime"] is False


def test_two_active_bindings_with_approved_capability_pass(tmp_path):
    """A complete synthetic two-agent setup passes Gate 0."""
    _write_runtime_docs(tmp_path, executable=True)
    project_a = tmp_path / "project-a"
    project_b = tmp_path / "project-b"
    project_a.mkdir()
    project_b.mkdir()
    create_scaffold(str(project_a))
    create_scaffold(str(project_b))
    binding_a = project_a / ".agent" / "CONVERSATION_BINDING.json"
    binding_b = project_b / ".agent" / "CONVERSATION_BINDING.json"
    _activate_binding(binding_a, "agent-alpha", "conv-alpha")
    _activate_binding(binding_b, "agent-beta", "conv-beta")

    exit_code, report = evaluate_preflight(
        repo_root=tmp_path,
        binding_paths=[binding_a, binding_b],
        project_roots=[str(project_a), str(project_b)],
    )

    _assert_schema_valid(report)
    assert exit_code == 0
    assert report["overall"] == "PASS"
    assert report["agent_count"] == 2
    assert all(check["status"] == "passed" for check in report["checks"])


def test_proposed_opencode_capability_requires_human_gate(tmp_path):
    """CAP-029 proposed/false execution state keeps pilot in HUMAN_REQUIRED."""
    _write_runtime_docs(tmp_path, executable=False)
    project_a = tmp_path / "project-a"
    project_b = tmp_path / "project-b"
    project_a.mkdir()
    project_b.mkdir()
    create_scaffold(str(project_a))
    create_scaffold(str(project_b))
    binding_a = project_a / ".agent" / "CONVERSATION_BINDING.json"
    binding_b = project_b / ".agent" / "CONVERSATION_BINDING.json"
    _activate_binding(binding_a, "agent-alpha", "conv-alpha")
    _activate_binding(binding_b, "agent-beta", "conv-beta")

    exit_code, report = evaluate_preflight(
        repo_root=tmp_path,
        binding_paths=[binding_a, binding_b],
        project_roots=[str(project_a), str(project_b)],
    )

    _assert_schema_valid(report)
    assert exit_code == 2
    assert report["overall"] == "HUMAN_REQUIRED"
    assert any(check["name"] == "cap_029_execution" for check in report["checks"])


def test_duplicate_agent_ids_block(tmp_path):
    """Two bindings cannot claim the same agent_id."""
    _write_runtime_docs(tmp_path, executable=True)
    project_a = tmp_path / "project-a"
    project_b = tmp_path / "project-b"
    project_a.mkdir()
    project_b.mkdir()
    create_scaffold(str(project_a))
    create_scaffold(str(project_b))
    binding_a = project_a / ".agent" / "CONVERSATION_BINDING.json"
    binding_b = project_b / ".agent" / "CONVERSATION_BINDING.json"
    _activate_binding(binding_a, "agent-duplicate", "conv-alpha")
    _activate_binding(binding_b, "agent-duplicate", "conv-beta")

    exit_code, report = evaluate_preflight(
        repo_root=tmp_path,
        binding_paths=[binding_a, binding_b],
        project_roots=[str(project_a), str(project_b)],
    )

    _assert_schema_valid(report)
    assert exit_code == 1
    assert report["overall"] == "BLOCKED"
    assert any(check["name"] == "unique_agent_ids" for check in report["checks"])


def test_missing_binding_blocks(tmp_path):
    """Missing binding evidence is a blocked preflight, not human-required."""
    _write_runtime_docs(tmp_path, executable=True)

    exit_code, report = evaluate_preflight(
        repo_root=tmp_path,
        binding_paths=[tmp_path / "missing" / "CONVERSATION_BINDING.json"],
        project_roots=[str(tmp_path / "missing")],
    )

    _assert_schema_valid(report)
    assert exit_code == 1
    assert report["overall"] == "BLOCKED"
    assert any("not found" in check["detail"] for check in report["checks"])


def test_schema_rejects_external_runtime_execution_flag():
    """Preflight reports cannot claim external runtime execution."""
    report = {
        "overall": "PASS",
        "executed_external_runtime": True,
        "human_gate_required": False,
        "agent_count": 2,
        "checks": [
            {
                "name": "sample",
                "status": "passed",
                "detail": "sample check",
                "evidence": None,
            }
        ],
    }

    errors = list(_schema_validator().iter_errors(report))

    assert errors
    assert any("False was expected" in error.message for error in errors)


def test_schema_rejects_human_required_without_gate_flag():
    """HUMAN_REQUIRED reports must set human_gate_required=true."""
    report = {
        "overall": "HUMAN_REQUIRED",
        "executed_external_runtime": False,
        "human_gate_required": False,
        "agent_count": 1,
        "checks": [
            {
                "name": "manual_binding",
                "status": "human_required",
                "detail": "binding pending",
                "evidence": None,
            }
        ],
    }

    errors = list(_schema_validator().iter_errors(report))

    assert errors
    assert any("True was expected" in error.message for error in errors)
