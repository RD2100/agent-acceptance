"""PAPER-C1 protocol-only safety tests for future real-paper pilots."""

from __future__ import annotations

from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parent.parent
PROTOCOL = ROOT / "docs" / "paper-c1-real-paper-pilot-safety-protocol.md"
CONTRACT = ROOT / "contracts" / "paper_c1_real_paper_pilot_safety_contract.yaml"
FIXTURE_DIR = ROOT / "examples" / "paper_c1_negative_privacy_fixtures"


def _load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def test_protocol_is_design_only_and_blocks_real_paper_execution():
    text = PROTOCOL.read_text(encoding="utf-8")

    assert "Scope: protocol_only" in text
    assert "real_paper_execution_allowed: false" in text
    assert "real_paper_full_text_allowed: false" in text
    assert "external_upload_allowed: false" in text
    assert "live_cdp_allowed: false" in text


def test_contract_is_machine_readable_and_fail_closed():
    contract = _load_yaml(CONTRACT)

    assert contract["contract_id"] == "PAPER_C1_REAL_PAPER_PILOT_SAFETY_CONTRACT"
    assert contract["scope"] == "protocol_only"
    assert contract["real_paper_execution_allowed"] is False
    assert contract["real_paper_full_text_allowed"] is False
    assert contract["external_upload_allowed"] is False
    assert contract["live_cdp_allowed"] is False

    expected_failures = {
        "real_paper_full_text_input",
        "user_private_text_detected",
        "missing_or_ambiguous_authorization",
        "missing_privacy_attestation",
        "missing_redaction_report",
        "memory_write_contains_paper_content",
        "external_upload_attempted",
        "live_cdp_attempted",
        "historical_evidence_cleanup_attempted",
        "classifier_uncertainty",
    }
    assert expected_failures.issubset(set(contract["fail_closed_on"]))


def test_user_authorized_excerpt_requires_task_scoped_authorization():
    contract = _load_yaml(CONTRACT)
    rule = contract["input_classification_rules"]["user_authorized_excerpt"]

    assert rule["handling"] == "block_without_explicit_task_scoped_authorization"
    assert {
        "authorization_id",
        "authorized_by",
        "authorized_at_utc",
        "task_id",
        "allowed_input_classification",
        "allowed_operations",
        "expires_at_utc",
        "revocation_supported",
    }.issubset(set(rule["required_authorization_fields"]))


def test_negative_fixtures_are_synthetic_only():
    fixture_paths = sorted(FIXTURE_DIR.glob("*.yaml"))
    assert {p.name for p in fixture_paths} == {
        "external_upload_blocked.yaml",
        "memory_write_blocked.yaml",
        "real_full_text_blocked.yaml",
    }

    forbidden_values = {
        "REAL_PAPER_TEXT",
        "USER_PRIVATE_TEXT",
        "RAW_TRANSCRIPT",
        "AUTHOR_IDENTITY",
    }
    for path in fixture_paths:
        text = path.read_text(encoding="utf-8")
        data = yaml.safe_load(text)

        assert data["synthetic_only"] is True
        assert data["expected_result"] == "blocked"
        assert data["expected_blocking_issue"]
        assert data["payload"]["contains_real_paper_content"] is False
        assert data["payload"]["contains_user_private_text"] is False
        for marker in forbidden_values:
            assert marker not in text


def test_fixture_scenarios_match_contract_fail_closed_rules():
    contract = _load_yaml(CONTRACT)
    fail_closed = set(contract["fail_closed_on"])

    for path in FIXTURE_DIR.glob("*.yaml"):
        data = _load_yaml(path)
        assert data["expected_blocking_issue"] in fail_closed
