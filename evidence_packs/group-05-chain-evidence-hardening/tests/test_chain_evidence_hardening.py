from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import yaml

ROOT = Path(__file__).resolve().parent.parent

from tools.ai_guard import validate_evidence_dir
from tools.go_evidence import (
    _determine_reviewer_verdict,
    synthesize_final_status,
    cmd_finalize,
)


POLICY = {
    "required_evidence_files": [
        "diff.patch",
        "test-output.md",
        "safety-report.json",
        "chain-evidence.json",
        "review.yaml",
    ],
    "reviewer_forbidden_roles": ["executor", "fixer", "coder"],
    "blocking_finding_severities": ["P0", "P1"],
}


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _write_json(path: Path, payload: dict) -> None:
    _write_text(path, json.dumps(payload, ensure_ascii=False, indent=2))


def _write_yaml(path: Path, payload: dict) -> None:
    _write_text(path, yaml.safe_dump(payload, sort_keys=False))


def _make_valid_evidence_dir(tmp_path: Path) -> Path:
    run_dir = tmp_path / "run"
    _write_text(run_dir / "diff.patch", "diff")
    _write_text(run_dir / "test-output.md", "tests")
    _write_json(
        run_dir / "safety-report.json",
        {
            "exit_code": 0,
            "stdout": "pass",
            "stderr": "",
        },
    )
    _write_json(
        run_dir / "chain-evidence.json",
        {
            "run_id": "run",
            "task_file": ".ai/tasks/group-05-chain-evidence-hardening.yaml",
            "executor_id": "exec-1",
            "reviewer_id": "reviewer-1",
            "reviewer_role": "reviewer",
            "reviewed_at": "2026-06-07T10:00:00+00:00",
            "created_at": "2026-06-07T09:00:00+00:00",
            "producer": "test",
        },
    )
    _write_yaml(
        run_dir / "review.yaml",
        {
            "reviewer_role": "reviewer",
            "reviewer_id": "reviewer-1",
            "executor_id": "exec-1",
            "verdict": "pass",
            "reviewed_inputs": [
                "diff.patch",
                "test-output.md",
                "safety-report.json",
                "chain-evidence.json",
            ],
            "findings": [],
        },
    )
    return run_dir


def test_chain_schema_declares_reviewer_and_rerun_fields():
    schema = json.loads((ROOT / "schemas" / "agent-runtime" / "chain-evidence.schema.json").read_text(encoding="utf-8"))
    props = schema["properties"]
    for field in ("reviewer_role", "reviewed_at", "rerun_verified_at", "rerun_summary"):
        assert field in props


def test_ai_guard_rejects_unexpected_chain_field(tmp_path):
    run_dir = _make_valid_evidence_dir(tmp_path)
    chain = json.loads((run_dir / "chain-evidence.json").read_text(encoding="utf-8"))
    chain["unexpected"] = True
    _write_json(run_dir / "chain-evidence.json", chain)
    errors, _warnings = validate_evidence_dir(run_dir, POLICY, repo_root=ROOT)
    assert any("unexpected field" in error for error in errors)


def test_ai_guard_rejects_invalid_reviewed_at(tmp_path):
    run_dir = _make_valid_evidence_dir(tmp_path)
    chain = json.loads((run_dir / "chain-evidence.json").read_text(encoding="utf-8"))
    chain["reviewed_at"] = "not-a-date"
    _write_json(run_dir / "chain-evidence.json", chain)
    errors, _warnings = validate_evidence_dir(run_dir, POLICY, repo_root=ROOT)
    assert any("reviewed_at" in error for error in errors)


def test_ai_guard_rejects_missing_reviewer_role_after_review(tmp_path):
    run_dir = _make_valid_evidence_dir(tmp_path)
    chain = json.loads((run_dir / "chain-evidence.json").read_text(encoding="utf-8"))
    chain.pop("reviewer_role")
    _write_json(run_dir / "chain-evidence.json", chain)
    errors, _warnings = validate_evidence_dir(run_dir, POLICY, repo_root=ROOT)
    assert any("reviewer_role is required" in error for error in errors)


def test_ai_guard_rejects_reviewer_id_mismatch(tmp_path):
    run_dir = _make_valid_evidence_dir(tmp_path)
    chain = json.loads((run_dir / "chain-evidence.json").read_text(encoding="utf-8"))
    chain["reviewer_id"] = "someone-else"
    _write_json(run_dir / "chain-evidence.json", chain)
    errors, _warnings = validate_evidence_dir(run_dir, POLICY, repo_root=ROOT)
    assert any("reviewer_id must match" in error for error in errors)


def test_ai_guard_rejects_rerun_without_summary(tmp_path):
    run_dir = _make_valid_evidence_dir(tmp_path)
    chain = json.loads((run_dir / "chain-evidence.json").read_text(encoding="utf-8"))
    chain["rerun_verified_at"] = "2026-06-07T11:00:00+00:00"
    _write_json(run_dir / "chain-evidence.json", chain)
    errors, _warnings = validate_evidence_dir(run_dir, POLICY, repo_root=ROOT)
    assert any("rerun_summary is required" in error for error in errors)


def test_ai_guard_rejects_rerun_before_reviewed_at(tmp_path):
    run_dir = _make_valid_evidence_dir(tmp_path)
    chain = json.loads((run_dir / "chain-evidence.json").read_text(encoding="utf-8"))
    chain["rerun_verified_at"] = "2026-06-07T08:59:00+00:00"
    chain["rerun_summary"] = "stale rerun"
    _write_json(run_dir / "chain-evidence.json", chain)
    errors, _warnings = validate_evidence_dir(run_dir, POLICY, repo_root=ROOT)
    assert any("rerun_verified_at must be on or after reviewed_at" in error for error in errors)


def test_determine_reviewer_verdict_invalid_when_missing(tmp_path):
    verdict, blocked_by = _determine_reviewer_verdict(tmp_path / "missing-review.yaml")
    assert verdict == "missing"
    assert blocked_by[0]["code"] == "review_artifact_missing"


def test_synthesize_final_status_human_required_precedence():
    final = synthesize_final_status(
        "pass",
        "pass",
        "accepted",
        [{"origin": "policy", "code": "human_required", "detail": "manual gate"}],
    )
    assert final == "human_required"


def test_finalize_writes_rerun_metadata(tmp_path, monkeypatch):
    run_dir = _make_valid_evidence_dir(tmp_path)
    _write_json(run_dir / "evidence-report.json", {"evidence_status": "pass"})

    import tools.go_evidence as go_evidence

    monkeypatch.setattr(
        go_evidence,
        "run_command",
        lambda command, cwd: SimpleNamespace(returncode=0, stdout="AI Guard Evidence: PASS", stderr=""),
    )

    exit_code = cmd_finalize(SimpleNamespace(run_dir=str(run_dir)), ROOT)
    chain = json.loads((run_dir / "chain-evidence.json").read_text(encoding="utf-8"))
    assert exit_code == 0
    assert "rerun_verified_at" in chain
    assert "rerun_summary" in chain
    assert "final=pass" in chain["rerun_summary"]
