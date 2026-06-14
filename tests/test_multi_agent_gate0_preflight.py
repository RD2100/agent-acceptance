"""Tests for the multi-agent Gate 0 preflight."""

import json
import subprocess
import sys
from datetime import datetime, timedelta, timezone
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


def _write_activation_record(
    path: Path,
    agent_ids: list[str],
    *,
    live_sessions: bool = True,
    authorized: bool = True,
    stale_sessions: bool = False,
) -> Path:
    now = datetime.now(timezone.utc)
    verified_at = now - timedelta(hours=2) if stale_sessions else now
    evidence_dir = path.parent / "_evidence" / "synthetic"
    evidence_dir.mkdir(parents=True, exist_ok=True)
    authorization_evidence = evidence_dir / "authorization.json"
    authorization_evidence.write_text(
        json.dumps({"run_id": "run-synthetic-001", "authorized": authorized}),
        encoding="utf-8",
    )
    for index, agent_id in enumerate(agent_ids, start=1):
        (evidence_dir / f"session-{index}.json").write_text(
            json.dumps(
                {
                    "agent_id": agent_id,
                    "session_id": f"session-{index}",
                    "live": live_sessions,
                    "verified_at": verified_at.isoformat(),
                }
            ),
            encoding="utf-8",
        )
    data = {
        "pilot_id": "synthetic-pilot",
        "run_id": "run-synthetic-001",
        "authorization": {
            "authorized": authorized,
            "authorizing_task": "task-synthetic-authorization",
            "exact_command": "opencode run --task run-synthetic-001",
            "expected_write_set": ["_reports/synthetic/**"],
            "evidence_file": str(authorization_evidence.relative_to(path.parent)),
            "decision_maker": "human-reviewer",
            "decision_reason": "bounded synthetic test",
            "approved_at": now.isoformat(),
            "expires_at": (now + timedelta(hours=1)).isoformat(),
            "risk_acknowledged": True,
        },
        "active_agents": [
            {
                "agent_id": agent_id,
                "binding_status": "active",
                "session_id": f"session-{index}",
                "cdp_session_verified": live_sessions,
                "verified_at": verified_at.isoformat(),
                "evidence_file": str(
                    (evidence_dir / f"session-{index}.json").relative_to(path.parent)
                ),
            }
            for index, agent_id in enumerate(agent_ids, start=1)
        ],
        "cdp_session": {"active": live_sessions},
    }
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return path


def test_current_repo_preflight_requires_fresh_authorization_and_live_sessions():
    """Current repo preflight reports current readiness without executing runtimes."""
    exit_code, report = evaluate_preflight(REPO)

    _assert_schema_valid(report)
    assert report["overall"] in {"PASS", "HUMAN_REQUIRED"}
    assert exit_code == (0 if report["overall"] == "PASS" else 2)
    assert report["human_gate_required"] is (report["overall"] == "HUMAN_REQUIRED")
    assert report["executed_external_runtime"] is False
    assert any(check["name"] == "live_agent_sessions" for check in report["checks"])
    generated_at = datetime.fromisoformat(report["generated_at"].replace("Z", "+00:00"))
    assert generated_at.tzinfo is not None


def test_cli_output_writes_same_schema_valid_report(tmp_path):
    """CLI --output writes the same schema report with current exit semantics."""
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

    stdout_report = json.loads(result.stdout)
    file_report = json.loads(output_path.read_text(encoding="utf-8"))
    assert file_report == stdout_report
    _assert_schema_valid(file_report)
    assert file_report["overall"] in {"PASS", "HUMAN_REQUIRED"}
    assert result.returncode == (0 if file_report["overall"] == "PASS" else 2)
    assert file_report["human_gate_required"] is (
        file_report["overall"] == "HUMAN_REQUIRED"
    )
    assert file_report["executed_external_runtime"] is False
    assert isinstance(file_report["generated_at"], str)


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
    activation_record = _write_activation_record(
        tmp_path / "ACTIVATION_RECORD.json",
        ["agent-alpha", "agent-beta"],
    )

    exit_code, report = evaluate_preflight(
        repo_root=tmp_path,
        binding_paths=[binding_a, binding_b],
        project_roots=[str(project_a), str(project_b)],
        activation_record_path=activation_record,
    )

    _assert_schema_valid(report)
    assert exit_code == 0
    assert report["overall"] == "PASS"
    assert report["agent_count"] == 2
    assert all(check["status"] == "passed" for check in report["checks"])


def test_active_bindings_without_run_bound_authorization_require_human_gate(tmp_path):
    """Static active bindings alone must never authorize external dispatch."""
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
        activation_record_path=tmp_path / "missing-activation.json",
    )

    _assert_schema_valid(report)
    assert exit_code == 2
    assert report["overall"] == "HUMAN_REQUIRED"
    assert any(check["name"] == "run_authorization" for check in report["checks"])


def test_unverified_live_sessions_require_human_gate(tmp_path):
    """An authorization record cannot substitute for live independent sessions."""
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
    activation_record = _write_activation_record(
        tmp_path / "ACTIVATION_RECORD.json",
        ["agent-alpha", "agent-beta"],
        live_sessions=False,
    )

    exit_code, report = evaluate_preflight(
        repo_root=tmp_path,
        binding_paths=[binding_a, binding_b],
        project_roots=[str(project_a), str(project_b)],
        activation_record_path=activation_record,
    )

    _assert_schema_valid(report)
    assert exit_code == 2
    assert report["overall"] == "HUMAN_REQUIRED"
    assert any(check["name"] == "live_agent_sessions" for check in report["checks"])


def test_stale_session_evidence_requires_human_gate(tmp_path):
    """Previously live sessions must be re-verified for the current run."""
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
    activation_record = _write_activation_record(
        tmp_path / "ACTIVATION_RECORD.json",
        ["agent-alpha", "agent-beta"],
        stale_sessions=True,
    )

    exit_code, report = evaluate_preflight(
        repo_root=tmp_path,
        binding_paths=[binding_a, binding_b],
        project_roots=[str(project_a), str(project_b)],
        activation_record_path=activation_record,
    )

    assert exit_code == 2
    assert report["overall"] == "HUMAN_REQUIRED"
    assert any("stale" in check["detail"] for check in report["checks"])


def test_future_authorization_approval_requires_human_gate(tmp_path):
    """An approval timestamp from the future cannot authorize this run."""
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
    activation_record = _write_activation_record(
        tmp_path / "ACTIVATION_RECORD.json", ["agent-alpha", "agent-beta"]
    )
    data = json.loads(activation_record.read_text(encoding="utf-8"))
    future_approval = datetime.now(timezone.utc) + timedelta(days=1)
    data["authorization"]["approved_at"] = future_approval.isoformat()
    data["authorization"]["expires_at"] = (future_approval + timedelta(hours=1)).isoformat()
    activation_record.write_text(json.dumps(data), encoding="utf-8")

    exit_code, report = evaluate_preflight(
        repo_root=tmp_path,
        binding_paths=[binding_a, binding_b],
        project_roots=[str(project_a), str(project_b)],
        activation_record_path=activation_record,
    )

    _assert_schema_valid(report)
    assert exit_code == 2
    assert report["overall"] == "HUMAN_REQUIRED"
    assert any(
        check["name"] == "run_authorization"
        and "approved_at is in the future" in check["detail"]
        for check in report["checks"]
    )


def test_activation_evidence_cannot_escape_repository_root(tmp_path):
    """Authorization evidence paths are repository-bound and fail closed."""
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
    activation_record = _write_activation_record(
        tmp_path / "ACTIVATION_RECORD.json", ["agent-alpha", "agent-beta"]
    )
    outside = tmp_path.parent / "outside-authorization.json"
    outside.write_text(
        json.dumps({"run_id": "run-synthetic-001", "authorized": True}),
        encoding="utf-8",
    )
    data = json.loads(activation_record.read_text(encoding="utf-8"))
    data["authorization"]["evidence_file"] = str(outside)
    activation_record.write_text(json.dumps(data), encoding="utf-8")

    exit_code, report = evaluate_preflight(
        repo_root=tmp_path,
        binding_paths=[binding_a, binding_b],
        project_roots=[str(project_a), str(project_b)],
        activation_record_path=activation_record,
    )

    assert exit_code == 2
    assert report["overall"] == "HUMAN_REQUIRED"
    assert any("within repository root" in check["detail"] for check in report["checks"])


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
    activation_record = _write_activation_record(
        tmp_path / "ACTIVATION_RECORD.json",
        ["agent-alpha", "agent-beta"],
    )

    exit_code, report = evaluate_preflight(
        repo_root=tmp_path,
        binding_paths=[binding_a, binding_b],
        project_roots=[str(project_a), str(project_b)],
        activation_record_path=activation_record,
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
