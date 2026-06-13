#!/usr/bin/env python3
"""Validate an ExecutionReport schema and independent reviewer identity."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

REPO = Path(__file__).resolve().parent.parent
SCHEMA_PATH = REPO / "schemas" / "agent-runtime" / "execution-report.schema.json"
GATE_RESULT_SCHEMA_PATH = REPO / "schemas" / "agent-runtime" / "gate-result.schema.json"


def _format_path(parts: list[Any]) -> str:
    return ".".join(str(part) for part in parts) or "<root>"


def validate_execution_report(path: Path) -> tuple[int, dict[str, Any]]:
    errors: list[str] = []
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except FileNotFoundError:
        data = None
        errors.append(f"file not found: {path}")
    except json.JSONDecodeError as exc:
        data = None
        errors.append(f"invalid JSON: {exc}")
    except OSError as exc:
        data = None
        errors.append(f"cannot read file: {path}: {exc}")

    if data is not None:
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8-sig"))
        gate_result_schema = json.loads(
            GATE_RESULT_SCHEMA_PATH.read_text(encoding="utf-8-sig")
        )
        schema["properties"]["gate_results"]["items"] = gate_result_schema
        validator = Draft202012Validator(schema)
        for error in sorted(
            validator.iter_errors(data), key=lambda item: list(item.absolute_path)
        ):
            errors.append(f"schema:{_format_path(list(error.absolute_path))}: {error.message}")

        if isinstance(data, dict) and data.get("status") == "pass":
            executor_id = data.get("executor_id")
            reviewer = data.get("reviewer_artifacts")
            reviewer_id = reviewer.get("reviewer_id") if isinstance(reviewer, dict) else None
            if executor_id and reviewer_id and executor_id == reviewer_id:
                errors.append("reviewer_id must differ from executor_id")

    report = {"valid": not errors, "path": str(path), "errors": errors}
    return (0 if not errors else 1), report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path)
    args = parser.parse_args()
    exit_code, report = validate_execution_report(args.report)
    print(json.dumps(report, indent=2, ensure_ascii=False))
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
