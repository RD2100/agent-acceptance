"""Real validator-path tests for ExecutionReport identity separation."""

import json
import subprocess
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))

from validate_execution_report import validate_execution_report


def _write_report(tmp_path: Path, *, executor_id: str, reviewer_id: str) -> Path:
    path = tmp_path / "execution-report.json"
    path.write_text(
        json.dumps(
            {
                "report_id": "report-1",
                "batch_id": "batch-1",
                "generated_at": "2026-06-13T00:00:00Z",
                "status": "pass",
                "summary": "verified",
                "executor_id": executor_id,
                "reviewer_artifacts": {
                    "review_md": "review.md",
                    "review_yaml": "review.yaml",
                    "reviewer_role": "reviewer",
                    "reviewer_id": reviewer_id,
                    "verdict": "pass",
                },
            }
        ),
        encoding="utf-8",
    )
    return path


def test_distinct_executor_and_reviewer_pass(tmp_path):
    exit_code, report = validate_execution_report(
        _write_report(tmp_path, executor_id="executor-1", reviewer_id="reviewer-1")
    )

    assert exit_code == 0
    assert report["valid"] is True


def test_same_executor_and_reviewer_fail(tmp_path):
    exit_code, report = validate_execution_report(
        _write_report(tmp_path, executor_id="same-session", reviewer_id="same-session")
    )

    assert exit_code == 1
    assert report["valid"] is False
    assert "reviewer_id must differ from executor_id" in report["errors"]


def test_cli_missing_file_returns_structured_error(tmp_path):
    missing = tmp_path / "missing.json"
    result = subprocess.run(
        [sys.executable, str(SCRIPTS / "validate_execution_report.py"), str(missing)],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    report = json.loads(result.stdout)
    assert report["valid"] is False
    assert any("file not found" in error for error in report["errors"])


def test_gate_result_reference_is_resolved_locally(tmp_path):
    path = _write_report(tmp_path, executor_id="executor-1", reviewer_id="reviewer-1")
    data = json.loads(path.read_text(encoding="utf-8"))
    data["gate_results"] = [
        {
            "gate_id": "gate-1",
            "run_id": "run-1",
            "gate_level": "P0",
            "gate_name": "identity check",
            "result": "pass",
            "checked_at": "2026-06-13T00:00:00Z",
            "signer_role": "reviewer",
        }
    ]
    path.write_text(json.dumps(data), encoding="utf-8")

    exit_code, report = validate_execution_report(path)

    assert exit_code == 0
    assert report["valid"] is True
