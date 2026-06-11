"""Regression tests for the synthetic WriteLab handoff E2E probe."""

from __future__ import annotations

import json
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parent.parent
WRITELAB_BACKEND = Path("D:/writelab/backend")


def test_probe_writelab_handoff_e2e_generates_valid_metadata_only_zip(tmp_path):
    if not WRITELAB_BACKEND.exists():
        pytest.skip("WriteLab backend checkout is not available")

    output_dir = tmp_path / "probe"
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
    summary = json.loads(result.stdout)
    assert summary["result"] == "pass"
    assert summary["summary"] == {
        "project_status": 201,
        "report_status": 201,
        "download_status": 200,
        "validation_result": "pass",
        "marker_scan_pass": True,
    }

    zip_path = output_dir / "writelab-handoff.zip"
    assert zip_path.exists()
    with zipfile.ZipFile(zip_path, "r") as zf:
        assert sorted(zf.namelist()) == [
            "DIAGNOSIS_RESULT.json",
            "PACK_MANIFEST.md",
            "PRIVACY_ATTESTATION.yaml",
            "WRITELAB_HANDOFF.yaml",
        ]

    validation = json.loads((output_dir / "VALIDATION_OUTPUT.json").read_text(encoding="utf-8"))
    assert validation["result"] == "pass"
    assert validation["blocking_issues"] == []

    marker_scan = json.loads((output_dir / "MARKER_SCAN_OUTPUT.json").read_text(encoding="utf-8"))
    assert marker_scan["pass"] is True
    assert not any(marker_scan["hits_by_label"].values())

    assert not (output_dir / "writelab_synthetic_e2e.sqlite").exists()
    assert not (output_dir / "writelab_synthetic_e2e.sqlite-wal").exists()
    assert not (output_dir / "writelab_synthetic_e2e.sqlite-shm").exists()
