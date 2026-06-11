"""Tests for the WriteLab metadata-only paper handoff validator."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from scripts.validate_writelab_handoff import validate_writelab_handoff


def _copy_synthetic_case(tmp_path: Path) -> Path:
    source = ROOT / "examples" / "writelab_paper_handoff_synthetic_case"
    target = tmp_path / "writelab_handoff"
    shutil.copytree(source, target)
    return target


def _load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _write_yaml(path: Path, data: dict) -> None:
    path.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def test_synthetic_writelab_handoff_directory_passes(tmp_path):
    case_dir = _copy_synthetic_case(tmp_path)

    result = validate_writelab_handoff(case_dir)

    assert result["result"] == "pass"
    assert result["checks"]["required_files_present"] is True
    assert result["checks"]["privacy_boundaries_valid"] is True
    assert result["blocking_issues"] == []


def test_synthetic_writelab_handoff_zip_passes(tmp_path):
    case_dir = _copy_synthetic_case(tmp_path)
    zip_path = tmp_path / "writelab_handoff.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        for fp in case_dir.iterdir():
            zf.write(fp, arcname=fp.name)

    result = validate_writelab_handoff(zip_path)

    assert result["result"] == "pass"
    assert result["source_type"] == "zip"


def test_real_paper_classification_fails_closed(tmp_path):
    case_dir = _copy_synthetic_case(tmp_path)
    handoff_path = case_dir / "WRITELAB_HANDOFF.yaml"
    data = _load_yaml(handoff_path)
    data["content_classification"] = "real_paper_full_text"
    _write_yaml(handoff_path, data)

    result = validate_writelab_handoff(case_dir)

    assert result["result"] == "fail"
    assert any(i["code"] in {"schema_violation", "blocked_content_classification"} for i in result["blocking_issues"])


def test_diagnosis_text_span_fails_closed(tmp_path):
    case_dir = _copy_synthetic_case(tmp_path)
    diagnosis_path = case_dir / "DIAGNOSIS_RESULT.json"
    data = _load_json(diagnosis_path)
    data["diagnosis"]["problem_details"] = [{"text_span": "REAL_PAPER_TEXT"}]
    _write_json(diagnosis_path, data)

    result = validate_writelab_handoff(case_dir)

    assert result["result"] == "fail"
    assert any(i["code"] == "forbidden_payload_key" for i in result["blocking_issues"])


def test_original_paragraph_payload_fails_closed(tmp_path):
    case_dir = _copy_synthetic_case(tmp_path)
    diagnosis_path = case_dir / "DIAGNOSIS_RESULT.json"
    data = _load_json(diagnosis_path)
    data["paragraph"] = "REAL_PAPER_TEXT"
    _write_json(diagnosis_path, data)

    result = validate_writelab_handoff(case_dir)

    assert result["result"] == "fail"
    assert any(i["code"] == "forbidden_payload_key" for i in result["blocking_issues"])


def test_external_upload_attestation_fails_closed(tmp_path):
    case_dir = _copy_synthetic_case(tmp_path)
    privacy_path = case_dir / "PRIVACY_ATTESTATION.yaml"
    data = _load_yaml(privacy_path)
    data["contains_external_upload"] = True
    _write_yaml(privacy_path, data)

    result = validate_writelab_handoff(case_dir)

    assert result["result"] == "fail"
    assert any(i["code"] == "privacy_attestation_violation" for i in result["blocking_issues"])


def test_missing_required_target_contract_fails(tmp_path):
    case_dir = _copy_synthetic_case(tmp_path)
    handoff_path = case_dir / "WRITELAB_HANDOFF.yaml"
    data = _load_yaml(handoff_path)
    data["target_contracts"] = ["PAPER_TASK_OUTPUT_CONTRACT"]
    _write_yaml(handoff_path, data)

    result = validate_writelab_handoff(case_dir)

    assert result["result"] == "fail"
    assert any(i["code"] == "missing_required_target_contract" for i in result["blocking_issues"])


def test_handoff_id_mismatch_fails(tmp_path):
    case_dir = _copy_synthetic_case(tmp_path)
    diagnosis_path = case_dir / "DIAGNOSIS_RESULT.json"
    data = _load_json(diagnosis_path)
    data["handoff_id"] = "WRITELAB-HANDOFF-OTHER"
    _write_json(diagnosis_path, data)

    result = validate_writelab_handoff(case_dir)

    assert result["result"] == "fail"
    assert any(i["code"] == "handoff_id_mismatch" for i in result["blocking_issues"])


def test_cli_returns_nonzero_for_blocked_handoff(tmp_path):
    case_dir = _copy_synthetic_case(tmp_path)
    diagnosis_path = case_dir / "DIAGNOSIS_RESULT.json"
    data = _load_json(diagnosis_path)
    data["original_text"] = "REAL_PAPER_TEXT"
    _write_json(diagnosis_path, data)

    completed = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "validate_writelab_handoff.py"), str(case_dir)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert completed.returncode == 1
    assert "forbidden_payload_key" in completed.stdout

