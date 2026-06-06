"""Validate PAPER-C2 synthetic authorization/redaction gate fixtures."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

ALLOWED_OPERATIONS = {"classify", "redact", "summarize_metadata"}
PROHIBITED_MARKERS = {
    "REAL_PAPER_TEXT",
    "USER_PRIVATE_TEXT",
    "RAW_TRANSCRIPT",
    "AUTHOR_IDENTITY",
}


def _parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def _try_parse_time(value: Any) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        return _parse_time(value)
    except ValueError:
        return None


def _contains_forbidden_marker(value: Any) -> bool:
    if isinstance(value, str):
        return any(marker in value for marker in PROHIBITED_MARKERS)
    if isinstance(value, dict):
        return any(_contains_forbidden_marker(v) for v in value.values())
    if isinstance(value, list):
        return any(_contains_forbidden_marker(v) for v in value)
    return False


def validate_fixture(path: Path) -> dict:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    issues: list[str] = []

    if data.get("synthetic_only") is not True:
        issues.append("fixture_not_synthetic_only")
    if _contains_forbidden_marker(data):
        issues.append("forbidden_fixture_marker_detected")

    task = data.get("task") or {}
    auth = data.get("authorization")
    redaction = data.get("redaction") or {}
    evaluation_time = _try_parse_time(data.get("evaluation_time_utc"))
    if evaluation_time is None:
        issues.append("invalid_evaluation_time")

    if not auth:
        issues.append("missing_authorization")
    else:
        required_auth = [
            "authorization_id",
            "authorized_by",
            "authorized_at_utc",
            "expires_at_utc",
            "task_id",
            "allowed_input_classification",
            "allowed_operations",
            "revocation_supported",
            "status",
        ]
        missing = [field for field in required_auth if field not in auth]
        if missing:
            issues.append("missing_authorization_field")
        else:
            if auth["authorized_by"] != "human_user":
                issues.append("ambiguous_authorization")
            if auth["allowed_input_classification"] != "user_authorized_excerpt":
                issues.append("ambiguous_authorization")
            if auth["status"] != "active":
                issues.append("stale_authorization")
            if auth["revocation_supported"] is not True:
                issues.append("missing_revocation_support")
            if auth["task_id"] != task.get("task_id"):
                issues.append("authorization_task_mismatch")
            if len(auth.get("applies_to_task_ids", [auth["task_id"]])) != 1:
                issues.append("ambiguous_authorization")
            expires_at = _try_parse_time(auth["expires_at_utc"])
            if expires_at is None:
                issues.append("invalid_authorization_expiry")
            elif evaluation_time is not None and expires_at <= evaluation_time:
                issues.append("stale_authorization")
            operations = set(auth["allowed_operations"])
            if not operations or not operations.issubset(ALLOWED_OPERATIONS):
                issues.append("overbroad_authorization")

    if redaction.get("redaction_report_present") is not True:
        issues.append("missing_redaction_report")
    if redaction.get("privacy_attestation_present") is not True:
        issues.append("missing_privacy_attestation")
    if redaction.get("redaction_applied") is not True:
        issues.append("redaction_not_applied")
    if redaction.get("redacted_material_classification") not in {
        "redacted_metadata",
        "user_authorized_excerpt_metadata",
    }:
        issues.append("redaction_not_applied")
    if redaction.get("contains_real_paper_full_text") is not False:
        issues.append("real_paper_text_detected")
    if redaction.get("contains_user_private_text") is not False:
        issues.append("user_private_text_detected")
    if redaction.get("contains_raw_transcript") is not False:
        issues.append("raw_transcript_detected")
    if redaction.get("contains_memory_write_with_paper_content") is not False:
        issues.append("paper_content_memory_write_detected")
    if redaction.get("contains_external_upload") is not False:
        issues.append("external_upload_attempted")

    deduped = list(dict.fromkeys(issues))
    return {
        "fixture_id": data.get("fixture_id"),
        "result": "fail" if deduped else "pass",
        "blocking_issues": deduped,
    }


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("Usage: python scripts/validate_paper_c2_gate.py <fixture.yaml>")
        return 2
    result = validate_fixture(Path(argv[1]))
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["result"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
