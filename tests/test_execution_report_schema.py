"""Schema checks for independent ExecutionReport reviewer evidence."""

import json
from pathlib import Path

from jsonschema import Draft202012Validator

REPO = Path(__file__).resolve().parent.parent
SCHEMA = json.loads(
    (REPO / "schemas" / "agent-runtime" / "execution-report.schema.json").read_text(
        encoding="utf-8-sig"
    )
)


def _report() -> dict:
    return {
        "report_id": "report-1",
        "batch_id": "batch-1",
        "generated_at": "2026-06-13T00:00:00Z",
        "status": "pass",
        "summary": "verified",
        "executor_id": "executor-session",
        "reviewer_artifacts": {
            "review_md": "review.md",
            "review_yaml": "review.yaml",
            "reviewer_role": "reviewer",
            "reviewer_id": "reviewer-session",
            "verdict": "pass",
        },
    }


def test_pass_report_requires_executor_and_reviewer_ids():
    report = _report()
    del report["executor_id"]
    del report["reviewer_artifacts"]["reviewer_id"]

    messages = [
        error.message for error in Draft202012Validator(SCHEMA).iter_errors(report)
    ]

    assert any("executor_id" in message for message in messages)
    assert any("reviewer_id" in message for message in messages)


def test_pass_report_with_identity_fields_is_schema_valid():
    errors = list(Draft202012Validator(SCHEMA).iter_errors(_report()))

    assert errors == []
