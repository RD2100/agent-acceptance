"""Validate PAPER-A2 paper task bundles before workflow closure.

The validator accepts either a directory or a ZIP file containing the
PAPER-A2 redacted paper task files. It is intentionally fail-closed:
privacy boundary violations return exit code 1 and are reported as
blocking issues.
"""

from __future__ import annotations

import argparse
import json
import sys
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parent.parent

REQUIRED_FILES = [
    "PAPER_TASK_INPUT.yaml",
    "PAPER_TASK_OUTPUT.yaml",
    "PRIVACY_ATTESTATION.yaml",
    "REDACTION_REPORT.yaml",
]

ALLOWED_TASK_TYPES = {
    "cssci_review",
    "thesis_midterm_review",
    "academic_revision",
    "citation_verification",
    "paper_structure_diagnosis",
}

PRIVACY_FALSE_FIELDS = [
    "contains_real_paper_full_text",
    "contains_user_private_text",
    "contains_raw_transcript",
    "contains_external_upload",
]

FORBIDDEN_PAYLOAD_KEYS = {
    "raw_paper_text",
    "paper_content",
    "paper_excerpt",
    "citation_original_text",
    "user_identity",
    "unpublished_argument",
    "doctoral_dissertation_draft",
    "raw_transcript",
    "private_paper_text",
}


@dataclass
class Bundle:
    source: Path
    source_type: str
    files: dict[str, bytes]


def _issue(code: str, message: str, path: str | None = None) -> dict[str, str]:
    item = {"code": code, "message": message}
    if path:
        item["path"] = path
    return item


def _load_schema(name: str) -> dict[str, Any]:
    return json.loads((ROOT / "schemas" / name).read_text(encoding="utf-8"))


def _find_required_file(names: list[str], filename: str) -> str | None:
    matches = [n for n in names if n == filename or n.endswith("/" + filename)]
    if len(matches) == 1:
        return matches[0]
    return None


def _load_bundle(source: str | Path) -> tuple[Bundle | None, list[dict[str, str]]]:
    path = Path(source)
    issues: list[dict[str, str]] = []

    if not path.exists():
        return None, [_issue("source_missing", f"source does not exist: {path}")]

    files: dict[str, bytes] = {}
    if path.is_dir():
        for filename in REQUIRED_FILES:
            fp = path / filename
            if fp.exists() and fp.is_file():
                files[filename] = fp.read_bytes()
        return Bundle(path, "directory", files), issues

    if path.is_file() and path.suffix.lower() == ".zip":
        try:
            with zipfile.ZipFile(path, "r") as zf:
                names = zf.namelist()
                for filename in REQUIRED_FILES:
                    member = _find_required_file(names, filename)
                    if member:
                        files[filename] = zf.read(member)
        except zipfile.BadZipFile:
            issues.append(_issue("bad_zip", f"invalid ZIP file: {path}"))
        return Bundle(path, "zip", files), issues

    return None, [_issue("unsupported_source", "source must be a directory or .zip file")]


def _load_yaml_file(bundle: Bundle, filename: str) -> tuple[dict[str, Any] | None, list[dict[str, str]]]:
    if filename not in bundle.files:
        return None, [_issue("required_file_missing", f"missing required file: {filename}", filename)]

    try:
        value = yaml.safe_load(bundle.files[filename].decode("utf-8"))
    except Exception as exc:
        return None, [_issue("yaml_parse_error", f"{filename}: {exc}", filename)]

    if not isinstance(value, dict):
        return None, [_issue("yaml_not_mapping", f"{filename} must contain a mapping", filename)]

    return value, []


def _schema_errors(instance: dict[str, Any], schema_name: str, label: str) -> list[dict[str, str]]:
    schema = _load_schema(schema_name)
    validator = Draft202012Validator(schema)
    issues: list[dict[str, str]] = []
    for error in sorted(validator.iter_errors(instance), key=lambda e: list(e.path)):
        path = ".".join(str(part) for part in error.path) or label
        issues.append(_issue("schema_violation", f"{label}: {error.message}", path))
    return issues


def _walk_forbidden_keys(value: Any, prefix: str = "") -> list[str]:
    found: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            key_text = str(key)
            current = f"{prefix}.{key_text}" if prefix else key_text
            if key_text in FORBIDDEN_PAYLOAD_KEYS:
                found.append(current)
            found.extend(_walk_forbidden_keys(child, current))
    elif isinstance(value, list):
        for idx, child in enumerate(value):
            found.extend(_walk_forbidden_keys(child, f"{prefix}[{idx}]"))
    return found


def _check_consistency(documents: dict[str, dict[str, Any]]) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    task_ids = {name: doc.get("task_id") for name, doc in documents.items()}
    present_task_ids = {value for value in task_ids.values() if value}
    if len(present_task_ids) != 1:
        issues.append(_issue("task_id_mismatch", f"inconsistent task_id values: {task_ids}"))

    task_types = {
        "PAPER_TASK_INPUT.yaml": documents["PAPER_TASK_INPUT.yaml"].get("task_type"),
        "PAPER_TASK_OUTPUT.yaml": documents["PAPER_TASK_OUTPUT.yaml"].get("task_type"),
    }
    present_task_types = {value for value in task_types.values() if value}
    if len(present_task_types) != 1:
        issues.append(_issue("task_type_mismatch", f"inconsistent task_type values: {task_types}"))
    for filename, task_type in task_types.items():
        if task_type and task_type not in ALLOWED_TASK_TYPES:
            issues.append(_issue("task_type_not_allowed", f"{filename}: unsupported task_type {task_type}", filename))

    return issues


def _check_input(document: dict[str, Any]) -> list[dict[str, str]]:
    issues = _schema_errors(document, "paper_task_input.schema.json", "PAPER_TASK_INPUT.yaml")

    classification = document.get("paper_data_classification")
    authorization = document.get("user_authorization")
    if classification == "real_paper_full_text":
        issues.append(_issue("real_paper_full_text_input", "real_paper_full_text input is blocked"))
    if classification == "user_authorized_excerpt" and authorization != "explicit":
        issues.append(_issue("missing_user_authorization_for_excerpt", "user_authorized_excerpt requires explicit authorization"))

    for key_path in _walk_forbidden_keys(document):
        issues.append(_issue("raw_paper_text_in_input", f"forbidden paper payload key in input: {key_path}", key_path))

    return issues


def _check_output(document: dict[str, Any]) -> list[dict[str, str]]:
    issues = _schema_errors(document, "paper_task_output.schema.json", "PAPER_TASK_OUTPUT.yaml")

    for field in ["contains_real_paper_full_text", "contains_unredacted_excerpt", "contains_user_identity"]:
        if document.get(field) is True:
            issues.append(_issue("output_privacy_violation", f"{field} must be false", field))

    summary = str(document.get("output_summary", "")).lower()
    if "accepted" in summary or "closed" in summary:
        issues.append(_issue("output_claims_accepted_or_closed", "paper task output must not claim accepted or closed"))

    for key_path in _walk_forbidden_keys(document):
        issues.append(_issue("real_paper_text_in_output", f"forbidden paper payload key in output: {key_path}", key_path))

    return issues


def _check_privacy_attestation(document: dict[str, Any]) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    required = [
        "task_id",
        "contains_real_paper_full_text",
        "contains_user_private_text",
        "contains_raw_transcript",
        "contains_memory_write",
        "contains_external_upload",
        "redaction_applied",
        "manual_review_required",
        "memory_write_policy",
    ]
    for field in required:
        if field not in document:
            issues.append(_issue("privacy_attestation_missing_field", f"missing privacy field: {field}", field))

    for field in PRIVACY_FALSE_FIELDS:
        if document.get(field) is not False:
            issues.append(_issue("privacy_attestation_violation", f"{field} must be false", field))

    if document.get("redaction_applied") is not True:
        issues.append(_issue("redaction_not_applied", "redaction_applied must be true", "redaction_applied"))

    if document.get("memory_write_policy") not in {"none", "redacted_workflow_lesson_only"}:
        issues.append(_issue("memory_write_policy_blocked", "memory_write_policy is not allowed", "memory_write_policy"))

    for key_path in _walk_forbidden_keys(document):
        issues.append(_issue("privacy_attestation_forbidden_payload", f"forbidden payload key: {key_path}", key_path))

    return issues


def _check_redaction_report(document: dict[str, Any]) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    required = [
        "task_id",
        "redaction_applied",
        "contains_real_paper_full_text",
        "contains_user_private_text",
        "contains_raw_transcript",
        "manual_review_required",
    ]
    for field in required:
        if field not in document:
            issues.append(_issue("redaction_report_missing_field", f"missing redaction field: {field}", field))

    if document.get("redaction_applied") is not True:
        issues.append(_issue("redaction_report_not_applied", "redaction_applied must be true", "redaction_applied"))

    for field in ["contains_real_paper_full_text", "contains_user_private_text", "contains_raw_transcript"]:
        if document.get(field) is not False:
            issues.append(_issue("redaction_report_privacy_violation", f"{field} must be false", field))

    for key_path in _walk_forbidden_keys(document):
        issues.append(_issue("redaction_report_forbidden_payload", f"forbidden payload key: {key_path}", key_path))

    return issues


def validate_paper_task(source: str | Path) -> dict[str, Any]:
    """Validate a paper task directory or ZIP evidence bundle."""
    result: dict[str, Any] = {
        "result": "pending",
        "source": str(source),
        "source_type": None,
        "validated_files": [],
        "checks": {
            "required_files_present": False,
            "schemas_valid": False,
            "privacy_boundaries_valid": False,
            "task_consistency_valid": False,
        },
        "blocking_issues": [],
    }

    bundle, issues = _load_bundle(source)
    result["blocking_issues"].extend(issues)
    if bundle is None:
        result["result"] = "fail"
        return result

    result["source_type"] = bundle.source_type
    missing = [filename for filename in REQUIRED_FILES if filename not in bundle.files]
    if missing:
        for filename in missing:
            result["blocking_issues"].append(_issue("required_file_missing", f"missing required file: {filename}", filename))
        result["result"] = "fail"
        return result

    result["checks"]["required_files_present"] = True
    result["validated_files"] = REQUIRED_FILES[:]

    documents: dict[str, dict[str, Any]] = {}
    for filename in REQUIRED_FILES:
        document, file_issues = _load_yaml_file(bundle, filename)
        result["blocking_issues"].extend(file_issues)
        if document is not None:
            documents[filename] = document

    if len(documents) != len(REQUIRED_FILES):
        result["result"] = "fail"
        return result

    result["blocking_issues"].extend(_check_input(documents["PAPER_TASK_INPUT.yaml"]))
    result["blocking_issues"].extend(_check_output(documents["PAPER_TASK_OUTPUT.yaml"]))
    result["blocking_issues"].extend(_check_privacy_attestation(documents["PRIVACY_ATTESTATION.yaml"]))
    result["blocking_issues"].extend(_check_redaction_report(documents["REDACTION_REPORT.yaml"]))
    result["blocking_issues"].extend(_check_consistency(documents))

    issue_codes = {issue["code"] for issue in result["blocking_issues"]}
    result["checks"]["schemas_valid"] = "schema_violation" not in issue_codes
    result["checks"]["privacy_boundaries_valid"] = not any(
        code
        in {
            "real_paper_full_text_input",
            "raw_paper_text_in_input",
            "real_paper_text_in_output",
            "output_privacy_violation",
            "privacy_attestation_violation",
            "redaction_report_privacy_violation",
            "privacy_attestation_forbidden_payload",
            "redaction_report_forbidden_payload",
            "memory_write_policy_blocked",
            "missing_user_authorization_for_excerpt",
        }
        for code in issue_codes
    )
    result["checks"]["task_consistency_valid"] = not {"task_id_mismatch", "task_type_mismatch", "task_type_not_allowed"} & issue_codes

    result["result"] = "pass" if not result["blocking_issues"] else "fail"
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate a PAPER-A2 paper task bundle")
    parser.add_argument("source", help="Directory or ZIP containing PAPER_TASK_INPUT/OUTPUT and privacy files")
    parser.add_argument("--json-output", help="Optional path to write validation JSON")
    args = parser.parse_args(argv)

    result = validate_paper_task(args.source)
    output = json.dumps(result, ensure_ascii=False, indent=2)
    print(output)

    if args.json_output:
        Path(args.json_output).write_text(output + "\n", encoding="utf-8")

    return 0 if result["result"] == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())
