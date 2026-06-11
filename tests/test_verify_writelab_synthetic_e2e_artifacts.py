"""Tests for the WriteLab synthetic E2E artifact verifier."""

from __future__ import annotations

import json
import hashlib
import subprocess
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parent.parent
WRITELAB_BACKEND = Path("D:/writelab/backend")
HASH_EXCLUDES = {
    "HASHES.txt",
    "ARTIFACT_VERIFY_OUTPUT.json",
    "ARTIFACT_VERIFY_STDOUT.txt",
}


def _run_probe(output_dir: Path) -> None:
    result = subprocess.run(
        [
            sys.executable,
            "scripts/probe_writelab_handoff_e2e.py",
            "--writelab-backend",
            str(WRITELAB_BACKEND),
            "--output-dir",
            str(output_dir),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def _write_supporting_artifacts(output_dir: Path) -> None:
    (output_dir / "HANDOFF_SAFETY_SCAN.json").write_text(
        json.dumps({"pass": True, "issues": []}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    lines = []
    for path in sorted(p for p in output_dir.iterdir() if p.is_file() and p.name not in HASH_EXCLUDES):
        digest = hashlib.sha256(path.read_bytes()).hexdigest().upper()
        lines.append(f"{digest}  {path}")
    (output_dir / "HASHES.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")


def _run_verifier(output_dir: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            "scripts/verify_writelab_synthetic_e2e_artifacts.py",
            str(output_dir),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def test_verify_writelab_synthetic_e2e_artifacts_passes_for_probe_output(tmp_path):
    if not WRITELAB_BACKEND.exists():
        pytest.skip("WriteLab backend checkout is not available")

    output_dir = tmp_path / "probe"
    _run_probe(output_dir)
    _write_supporting_artifacts(output_dir)

    result = _run_verifier(output_dir)

    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    assert payload["result"] == "pass"
    assert all(payload["checks"].values())
    assert payload["blocking_issues"] == []


def test_verify_writelab_synthetic_e2e_artifacts_fails_on_retained_temp_db(tmp_path):
    if not WRITELAB_BACKEND.exists():
        pytest.skip("WriteLab backend checkout is not available")

    output_dir = tmp_path / "probe"
    _run_probe(output_dir)
    (output_dir / "writelab_synthetic_e2e.sqlite").write_text("raw temporary db should not remain", encoding="utf-8")
    _write_supporting_artifacts(output_dir)

    result = _run_verifier(output_dir)

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert payload["result"] == "fail"
    assert payload["checks"]["temporary_database_clean"] is False
    assert any(
        issue["code"] == "temporary_database_retained"
        for issue in payload["blocking_issues"]
    )


def test_verify_writelab_synthetic_e2e_artifacts_fails_on_skipped_test_output(tmp_path):
    if not WRITELAB_BACKEND.exists():
        pytest.skip("WriteLab backend checkout is not available")

    output_dir = tmp_path / "probe"
    _run_probe(output_dir)
    (output_dir / "PROBE_TEST_OUTPUT.txt").write_text("1 skipped\n", encoding="utf-8")
    _write_supporting_artifacts(output_dir)

    result = _run_verifier(output_dir)

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert payload["checks"]["test_outputs_valid"] is False
    assert any(
        issue["code"] == "test_output_contains_skip"
        for issue in payload["blocking_issues"]
    )


def test_verify_writelab_synthetic_e2e_artifacts_fails_on_hash_mismatch(tmp_path):
    if not WRITELAB_BACKEND.exists():
        pytest.skip("WriteLab backend checkout is not available")

    output_dir = tmp_path / "probe"
    _run_probe(output_dir)
    _write_supporting_artifacts(output_dir)
    with (output_dir / "API_PROBE_OUTPUT.json").open("a", encoding="utf-8") as handle:
        handle.write("\n")

    result = _run_verifier(output_dir)

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert payload["checks"]["hashes_valid"] is False
    assert any(
        issue["code"] == "hash_mismatch"
        for issue in payload["blocking_issues"]
    )
