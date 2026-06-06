"""Tests for PAPER-C2 synthetic authorization/redaction gate."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
FIXTURE_DIR = ROOT / "examples" / "paper_c2_authorization_redaction_gate"
CONTRACT = ROOT / "contracts" / "paper_c2_authorization_redaction_gate_contract.yaml"
AUTH_SCHEMA = ROOT / "schemas" / "paper_c2_authorization_gate.schema.json"
REDACTION_SCHEMA = ROOT / "schemas" / "paper_c2_redaction_gate.schema.json"
VALIDATOR = ROOT / "scripts" / "validate_paper_c2_gate.py"


def _load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _run_validator(path: Path) -> tuple[int, dict]:
    completed = subprocess.run(
        [sys.executable, str(VALIDATOR), str(path)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    return completed.returncode, json.loads(completed.stdout)


def test_contract_keeps_real_paper_execution_disabled():
    contract = _load_yaml(CONTRACT)

    assert contract["scope"] == "synthetic_only_gate_implementation"
    assert contract["real_paper_execution_allowed"] is False
    assert contract["real_paper_full_text_allowed"] is False
    assert contract["external_upload_allowed"] is False
    assert contract["live_cdp_allowed"] is False


def test_gate_schemas_exist_and_require_fail_closed_fields():
    auth_schema = json.loads(AUTH_SCHEMA.read_text(encoding="utf-8"))
    redaction_schema = json.loads(REDACTION_SCHEMA.read_text(encoding="utf-8"))

    assert "authorization_id" in auth_schema["required"]
    assert auth_schema["properties"]["allowed_input_classification"]["const"] == "user_authorized_excerpt"
    assert auth_schema["properties"]["revocation_supported"]["const"] is True
    assert redaction_schema["properties"]["contains_real_paper_full_text"]["const"] is False
    assert redaction_schema["properties"]["contains_external_upload"]["const"] is False


def test_positive_authorized_redacted_fixture_passes():
    code, result = _run_validator(FIXTURE_DIR / "positive_authorized_redacted.yaml")

    assert code == 0
    assert result["result"] == "pass"
    assert result["blocking_issues"] == []


def test_negative_fixtures_fail_closed_with_expected_issue():
    for path in sorted(FIXTURE_DIR.glob("*_blocked.yaml")):
        data = _load_yaml(path)
        code, result = _run_validator(path)

        assert code == 1, path.name
        assert result["result"] == "fail"
        for issue in data["expected_blocking_issues"]:
            assert issue in result["blocking_issues"], path.name


def test_all_fixtures_are_synthetic_placeholders_only():
    forbidden = {"REAL_PAPER_TEXT", "USER_PRIVATE_TEXT", "RAW_TRANSCRIPT", "AUTHOR_IDENTITY"}
    for path in FIXTURE_DIR.glob("*.yaml"):
        text = path.read_text(encoding="utf-8")
        data = yaml.safe_load(text)

        assert data["synthetic_only"] is True
        assert data["task"]["content_placeholder"].startswith("SYNTHETIC_")
        for marker in forbidden:
            assert marker not in text


def test_negative_fixture_set_covers_required_authorization_failures():
    expected = {
        "missing_authorization",
        "stale_authorization",
        "ambiguous_authorization",
        "overbroad_authorization",
        "missing_redaction_report",
    }
    observed = set()
    for path in FIXTURE_DIR.glob("*_blocked.yaml"):
        observed.update(_load_yaml(path)["expected_blocking_issues"])

    assert expected.issubset(observed)


def test_malformed_fixture_fails_closed_without_traceback(tmp_path):
    malformed = _load_yaml(FIXTURE_DIR / "positive_authorized_redacted.yaml")
    malformed.pop("evaluation_time_utc")
    path = tmp_path / "malformed.yaml"
    path.write_text(yaml.safe_dump(malformed, sort_keys=False), encoding="utf-8")

    code, result = _run_validator(path)

    assert code == 1
    assert result["result"] == "fail"
    assert "invalid_evaluation_time" in result["blocking_issues"]
