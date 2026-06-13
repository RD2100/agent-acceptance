"""Tests for the multi-agent dispatch plan validator CLI."""

import json
import subprocess
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))

from validate_multi_agent_dispatch_plan import validate_dispatch_plan

REPO = Path(__file__).resolve().parent.parent
VALID_PLAN = REPO / "_reports" / "multi-agent-dispatch-plan-a1" / "DISPATCH_PLAN.json"


def _load_valid_plan() -> dict:
    return json.loads(VALID_PLAN.read_text(encoding="utf-8"))


def _write_plan(tmp_path: Path, data: dict) -> Path:
    path = tmp_path / "DISPATCH_PLAN.json"
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return path


def _write_json(tmp_path: Path, data) -> Path:
    path = tmp_path / "DISPATCH_PLAN.json"
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return path


def test_validator_accepts_current_dispatch_plan():
    """Current dispatch plan is structurally and semantically valid."""
    exit_code, report = validate_dispatch_plan(VALID_PLAN)

    assert exit_code == 0
    assert report["valid"] is True
    assert report["dispatch_status"] == "HUMAN_REQUIRED"
    assert report["executed_external_runtime"] is False
    assert report["assignment_count"] >= 1
    assert report["errors"] == []


def test_validator_rejects_invalid_embedded_task_spec(tmp_path):
    """Consumers must catch invalid embedded TaskSpecs, not just top-level schema."""
    data = _load_valid_plan()
    data["assignments"][0]["task_spec"]["priority"] = "P9"
    path = _write_plan(tmp_path, data)

    exit_code, report = validate_dispatch_plan(path)

    assert exit_code == 1
    assert report["valid"] is False
    assert any(
        "schema:" in error and "task_spec.priority" in error and "P9" in error
        for error in report["errors"]
    )


def test_validator_rejects_parallel_write_conflict(tmp_path):
    """Consumers must catch write-set conflicts even when a stale summary says clean."""
    data = _load_valid_plan()
    ready = [
        item
        for item in data["assignments"]
        if item["parallel_safe"] and item["task_spec"]["status"] == "ready"
    ]
    assert len(ready) >= 2
    ready[0]["task_spec"]["conflict_registry"]["write_set"] = ["_reports/conflict"]
    ready[1]["task_spec"]["conflict_registry"]["write_set"] = [
        "_reports/conflict/report.md"
    ]
    data["conflict_summary"]["has_errors"] = False
    data["conflict_summary"]["has_write_conflicts"] = False
    path = _write_plan(tmp_path, data)

    exit_code, report = validate_dispatch_plan(path)

    assert exit_code == 1
    assert report["valid"] is False
    assert any("write conflict" in error for error in report["errors"])


def test_validator_rejects_external_runtime_execution_claim(tmp_path):
    """A dispatch plan cannot claim external runtime execution."""
    data = _load_valid_plan()
    data["executed_external_runtime"] = True
    path = _write_plan(tmp_path, data)

    exit_code, report = validate_dispatch_plan(path)

    assert exit_code == 1
    assert report["valid"] is False
    assert any("executed_external_runtime" in error for error in report["errors"])


def test_validator_rejects_non_object_top_level_without_crashing(tmp_path):
    """Malformed top-level JSON returns a structured schema error report."""
    path = _write_json(tmp_path, [])

    exit_code, report = validate_dispatch_plan(path)

    assert exit_code == 1
    assert report["valid"] is False
    assert report["dispatch_status"] is None
    assert report["assignment_count"] == 0
    assert any(
        "schema:" in error and "<root>" in error for error in report["errors"]
    )


def test_validator_rejects_null_top_level_as_schema_error(tmp_path):
    """JSON null is a parsed value, not a load failure sentinel."""
    path = _write_json(tmp_path, None)

    exit_code, report = validate_dispatch_plan(path)

    assert exit_code == 1
    assert report["valid"] is False
    assert report["dispatch_status"] is None
    assert report["assignment_count"] == 0
    assert any(
        "schema:" in error and "<root>" in error for error in report["errors"]
    )
    assert not any("failed to load dispatch plan" in error for error in report["errors"])


def test_validator_rejects_non_object_assignment_without_crashing(tmp_path):
    """Malformed assignment entries should not reach semantic .get() calls."""
    data = _load_valid_plan()
    data["assignments"] = [None]
    path = _write_plan(tmp_path, data)

    exit_code, report = validate_dispatch_plan(path)

    assert exit_code == 1
    assert report["valid"] is False
    assert report["assignment_count"] == 1
    assert any("schema:" in error and "assignments" in error for error in report["errors"])


def test_validator_cli_reports_malformed_shape_as_json(tmp_path):
    """CLI returns JSON for malformed shapes instead of crashing."""
    path = _write_json(tmp_path, None)
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPTS / "validate_multi_agent_dispatch_plan.py"),
            str(path),
        ],
        cwd=REPO,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    report = json.loads(result.stdout)
    assert report["valid"] is False
    assert report["dispatch_status"] is None
    assert any("schema:" in error for error in report["errors"])


def test_validator_cli_writes_json_report(tmp_path):
    """CLI returns JSON report and preserves success exit code for current plan."""
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPTS / "validate_multi_agent_dispatch_plan.py"),
            str(VALID_PLAN),
        ],
        cwd=REPO,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    report = json.loads(result.stdout)
    assert report["valid"] is True
    assert report["dispatch_status"] == "HUMAN_REQUIRED"
