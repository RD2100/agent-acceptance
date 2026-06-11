"""Tests for the PAPER-A3 paper task validator."""

from __future__ import annotations

import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from scripts.validate_paper_task import validate_paper_task


def _copy_synthetic_case(tmp_path: Path) -> Path:
    source = ROOT / "examples" / "paper_a2_synthetic_case"
    target = tmp_path / "paper_case"
    shutil.copytree(source, target)
    return target


def _load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _write_yaml(path: Path, data: dict) -> None:
    path.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")


def test_synthetic_paper_task_directory_passes(tmp_path):
    case_dir = _copy_synthetic_case(tmp_path)

    result = validate_paper_task(case_dir)

    assert result["result"] == "pass"
    assert result["checks"]["required_files_present"] is True
    assert result["checks"]["privacy_boundaries_valid"] is True
    assert result["blocking_issues"] == []


def test_synthetic_paper_task_zip_passes(tmp_path):
    case_dir = _copy_synthetic_case(tmp_path)
    zip_path = tmp_path / "paper_case.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        for fp in case_dir.iterdir():
            zf.write(fp, arcname=fp.name)

    result = validate_paper_task(zip_path)

    assert result["result"] == "pass"
    assert result["source_type"] == "zip"


def test_real_paper_full_text_input_fails_closed(tmp_path):
    case_dir = _copy_synthetic_case(tmp_path)
    input_path = case_dir / "PAPER_TASK_INPUT.yaml"
    data = _load_yaml(input_path)
    data["paper_data_classification"] = "real_paper_full_text"
    _write_yaml(input_path, data)

    result = validate_paper_task(case_dir)

    assert result["result"] == "fail"
    assert any(i["code"] == "real_paper_full_text_input" for i in result["blocking_issues"])


def test_user_authorized_excerpt_without_explicit_auth_fails(tmp_path):
    case_dir = _copy_synthetic_case(tmp_path)
    input_path = case_dir / "PAPER_TASK_INPUT.yaml"
    data = _load_yaml(input_path)
    data["paper_data_classification"] = "user_authorized_excerpt"
    data["user_authorization"] = "none"
    _write_yaml(input_path, data)

    result = validate_paper_task(case_dir)

    assert result["result"] == "fail"
    assert any(i["code"] == "missing_user_authorization_for_excerpt" for i in result["blocking_issues"])


def test_output_privacy_leak_fails(tmp_path):
    case_dir = _copy_synthetic_case(tmp_path)
    output_path = case_dir / "PAPER_TASK_OUTPUT.yaml"
    data = _load_yaml(output_path)
    data["contains_unredacted_excerpt"] = True
    _write_yaml(output_path, data)

    result = validate_paper_task(case_dir)

    assert result["result"] == "fail"
    assert any(i["code"] == "output_privacy_violation" for i in result["blocking_issues"])


def test_forbidden_payload_key_fails(tmp_path):
    case_dir = _copy_synthetic_case(tmp_path)
    output_path = case_dir / "PAPER_TASK_OUTPUT.yaml"
    data = _load_yaml(output_path)
    data["raw_paper_text"] = "blocked"
    _write_yaml(output_path, data)

    result = validate_paper_task(case_dir)

    assert result["result"] == "fail"
    assert any(i["code"] == "real_paper_text_in_output" for i in result["blocking_issues"])


def test_missing_privacy_attestation_fails(tmp_path):
    case_dir = _copy_synthetic_case(tmp_path)
    (case_dir / "PRIVACY_ATTESTATION.yaml").unlink()

    result = validate_paper_task(case_dir)

    assert result["result"] == "fail"
    assert any(i["code"] == "required_file_missing" for i in result["blocking_issues"])


def test_missing_redaction_report_fails(tmp_path):
    case_dir = _copy_synthetic_case(tmp_path)
    (case_dir / "REDACTION_REPORT.yaml").unlink()

    result = validate_paper_task(case_dir)

    assert result["result"] == "fail"
    assert any(i["code"] == "required_file_missing" for i in result["blocking_issues"])


def test_output_missing_evidence_basis_fails_schema(tmp_path):
    case_dir = _copy_synthetic_case(tmp_path)
    output_path = case_dir / "PAPER_TASK_OUTPUT.yaml"
    data = _load_yaml(output_path)
    data.pop("evidence_basis")
    _write_yaml(output_path, data)

    result = validate_paper_task(case_dir)

    assert result["result"] == "fail"
    assert any(i["code"] == "schema_violation" for i in result["blocking_issues"])


def test_output_claims_accepted_or_closed_fails(tmp_path):
    case_dir = _copy_synthetic_case(tmp_path)
    output_path = case_dir / "PAPER_TASK_OUTPUT.yaml"
    data = _load_yaml(output_path)
    data["output_summary"] = "This synthetic paper task is accepted and closed."
    _write_yaml(output_path, data)

    result = validate_paper_task(case_dir)

    assert result["result"] == "fail"
    assert any(i["code"] == "output_claims_accepted_or_closed" for i in result["blocking_issues"])


def test_memory_paper_content_payload_fails(tmp_path):
    case_dir = _copy_synthetic_case(tmp_path)
    attestation_path = case_dir / "PRIVACY_ATTESTATION.yaml"
    data = _load_yaml(attestation_path)
    data["memory_write"] = {"paper_content": "blocked"}
    _write_yaml(attestation_path, data)

    result = validate_paper_task(case_dir)

    assert result["result"] == "fail"
    assert any(i["code"] == "privacy_attestation_forbidden_payload" for i in result["blocking_issues"])


def test_memory_paper_excerpt_payload_fails(tmp_path):
    case_dir = _copy_synthetic_case(tmp_path)
    attestation_path = case_dir / "PRIVACY_ATTESTATION.yaml"
    data = _load_yaml(attestation_path)
    data["memory_write"] = {"paper_excerpt": "blocked"}
    _write_yaml(attestation_path, data)

    result = validate_paper_task(case_dir)

    assert result["result"] == "fail"
    assert any(i["code"] == "privacy_attestation_forbidden_payload" for i in result["blocking_issues"])


def test_memory_citation_original_text_payload_fails(tmp_path):
    case_dir = _copy_synthetic_case(tmp_path)
    attestation_path = case_dir / "PRIVACY_ATTESTATION.yaml"
    data = _load_yaml(attestation_path)
    data["memory_write"] = {"citation_original_text": "blocked"}
    _write_yaml(attestation_path, data)

    result = validate_paper_task(case_dir)

    assert result["result"] == "fail"
    assert any(i["code"] == "privacy_attestation_forbidden_payload" for i in result["blocking_issues"])


def test_external_upload_enabled_fails(tmp_path):
    case_dir = _copy_synthetic_case(tmp_path)
    attestation_path = case_dir / "PRIVACY_ATTESTATION.yaml"
    data = _load_yaml(attestation_path)
    data["contains_external_upload"] = True
    _write_yaml(attestation_path, data)

    result = validate_paper_task(case_dir)

    assert result["result"] == "fail"
    assert any(i["code"] == "privacy_attestation_violation" for i in result["blocking_issues"])


def test_cli_returns_nonzero_for_blocked_bundle(tmp_path):
    case_dir = _copy_synthetic_case(tmp_path)
    input_path = case_dir / "PAPER_TASK_INPUT.yaml"
    data = _load_yaml(input_path)
    data["paper_data_classification"] = "real_paper_full_text"
    _write_yaml(input_path, data)

    completed = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "validate_paper_task.py"), str(case_dir)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert completed.returncode == 1
    assert "real_paper_full_text_input" in completed.stdout
