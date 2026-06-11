#!/usr/bin/env python3
"""Shared fail-closed authorization checks for cross-repo execution scripts."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REQUIRED_AUDIT_FIELDS = (
    "schema_version",
    "authorized",
    "scope",
    "allowed_repos",
    "decision_maker",
    "decision_reason",
    "approved_at",
    "expires_at",
    "risk_acknowledged",
)


def _parse_timestamp(value: Any, field: str, errors: list[str]) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        errors.append(f"authorization {field} must be a non-empty ISO timestamp")
        return None

    raw = value.strip()
    if raw.endswith("Z"):
        raw = raw[:-1] + "+00:00"

    try:
        parsed = datetime.fromisoformat(raw)
    except ValueError:
        errors.append(f"authorization {field} must be a valid ISO timestamp")
        return None

    if parsed.tzinfo is None:
        errors.append(f"authorization {field} must include a timezone")
        return None

    return parsed.astimezone(timezone.utc)


def validate_cross_repo_authorization(
    record_path: str | None,
    *,
    required_scope: str,
    required_repos: list[str],
    now: datetime | None = None,
) -> tuple[bool, list[str], dict | None]:
    """Validate an auditable human authorization record.

    The record intentionally remains small, but it must be reviewable: who
    approved, why, for which exact repos, when, and until when.
    """
    if not record_path:
        return False, ["missing --authorization-record for cross-repo execution"], None

    path = Path(record_path)
    if not path.exists():
        return False, [f"authorization record not found: {path}"], None

    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as exc:
        return False, [f"authorization record invalid JSON: {exc}"], None

    errors: list[str] = []
    for field in REQUIRED_AUDIT_FIELDS:
        if field not in data:
            errors.append(f"authorization record missing required field: {field}")

    if data.get("authorized") is not True:
        errors.append("authorization record must set authorized=true")
    if data.get("scope") != required_scope:
        errors.append(f"authorization scope must be {required_scope}")
    if "risk_acknowledged" in data and data.get("risk_acknowledged") is not True:
        errors.append("authorization record must set risk_acknowledged=true")

    for field in ("decision_maker", "decision_reason"):
        if field in data and (
            not isinstance(data.get(field), str) or not data.get(field, "").strip()
        ):
            errors.append(f"authorization {field} must be non-empty")

    allowed_repos = data.get("allowed_repos")
    if not isinstance(allowed_repos, list) or not all(
        isinstance(repo, str) and repo.strip() for repo in allowed_repos
    ):
        errors.append("authorization allowed_repos must be a non-empty list of repo names")
    else:
        required_set = set(required_repos)
        allowed_set = set(allowed_repos)
        missing = sorted(required_set - allowed_set)
        unknown = sorted(allowed_set - required_set)
        if missing:
            errors.append(
                "authorization allowed_repos missing repo(s): " + ", ".join(missing)
            )
        if unknown:
            errors.append(
                "authorization allowed_repos contains unknown repo(s): "
                + ", ".join(unknown)
            )

    approved_at = (
        _parse_timestamp(data.get("approved_at"), "approved_at", errors)
        if "approved_at" in data
        else None
    )
    expires_at = (
        _parse_timestamp(data.get("expires_at"), "expires_at", errors)
        if "expires_at" in data
        else None
    )
    if approved_at and expires_at and expires_at <= approved_at:
        errors.append("authorization expires_at must be after approved_at")

    effective_now = now or datetime.now(timezone.utc)
    if effective_now.tzinfo is None:
        effective_now = effective_now.replace(tzinfo=timezone.utc)
    effective_now = effective_now.astimezone(timezone.utc)
    if expires_at and expires_at <= effective_now:
        errors.append("authorization record is expired")

    return len(errors) == 0, errors, data
