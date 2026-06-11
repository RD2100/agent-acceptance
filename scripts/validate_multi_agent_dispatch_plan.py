#!/usr/bin/env python3
"""Validate a multi-agent dispatch plan packet.

This is a consumer-side validator: it checks the top-level dispatch plan
schema, every embedded TaskSpec, and the semantic write-conflict rules.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from multi_agent_dispatch_plan import validate_plan

REPO = Path(__file__).resolve().parent.parent
PLAN_SCHEMA = REPO / "schemas" / "agent-runtime" / "multi-agent-dispatch-plan.schema.json"
JSON_LOAD_FAILED = object()


def _load_json(path: Path) -> tuple[Any, str | None]:
    try:
        return json.loads(path.read_text(encoding="utf-8-sig")), None
    except FileNotFoundError:
        return JSON_LOAD_FAILED, f"file not found: {path}"
    except json.JSONDecodeError as exc:
        return JSON_LOAD_FAILED, f"invalid JSON: {exc}"


def _format_schema_error(error: Any) -> str:
    path = ".".join(str(part) for part in error.absolute_path)
    location = path or "<root>"
    return f"{location}: {error.message}"


def _validate_schema(data: Any) -> list[str]:
    schema, load_error = _load_json(PLAN_SCHEMA)
    if load_error or schema is JSON_LOAD_FAILED:
        return [load_error or f"failed to load schema: {PLAN_SCHEMA}"]
    if not isinstance(schema, dict):
        return [f"schema root must be an object: {PLAN_SCHEMA}"]

    validator = Draft202012Validator(schema)
    errors = sorted(
        validator.iter_errors(data),
        key=lambda err: list(err.absolute_path),
    )
    return [_format_schema_error(error) for error in errors]


def validate_dispatch_plan(path: Path) -> tuple[int, dict[str, Any]]:
    """Validate a dispatch plan file and return an exit code plus report."""
    plan, load_error = _load_json(path)
    if load_error or plan is JSON_LOAD_FAILED:
        return 1, {
            "valid": False,
            "path": str(path),
            "errors": [load_error or "failed to load dispatch plan"],
        }

    schema_errors = _validate_schema(plan)
    semantic_valid = False
    semantic_errors: list[str] = []
    if not schema_errors:
        semantic_valid, semantic_errors = validate_plan(plan)
    errors = [f"schema: {error}" for error in schema_errors]
    errors.extend(f"semantic: {error}" for error in semantic_errors)

    assignments = plan.get("assignments", []) if isinstance(plan, dict) else []
    report = {
        "valid": not errors and semantic_valid,
        "path": str(path),
        "dispatch_status": plan.get("status") if isinstance(plan, dict) else None,
        "executed_external_runtime": (
            plan.get("executed_external_runtime") if isinstance(plan, dict) else None
        ),
        "assignment_count": len(assignments) if isinstance(assignments, list) else 0,
        "errors": errors,
    }
    return 0 if report["valid"] else 1, report


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate a multi-agent dispatch plan packet."
    )
    parser.add_argument("plan", help="Path to DISPATCH_PLAN.json")
    args = parser.parse_args()

    exit_code, report = validate_dispatch_plan(Path(args.plan))
    print(json.dumps(report, indent=2, ensure_ascii=False))
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
