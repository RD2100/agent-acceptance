"""Validate metadata-only WriteLab paper handoff packets.

The validator accepts a directory or ZIP packet and fails closed if the packet
contains original paper text, paragraph text spans, rewrite text, author
identity, external upload markers, or missing privacy evidence.
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
    "WRITELAB_HANDOFF.yaml",
    "DIAGNOSIS_RESULT.json",
    "PRIVACY_ATTESTATION.yaml",
    "PACK_MANIFEST.md",
]

REQUIRED_TARGET_CONTRACTS = {
    "PAPER_TASK_OUTPUT_CONTRACT",
    "PAPER_REDACTED_EVIDENCE_PACK_CONTRACT",
}

PRIVACY_FALSE_FIELDS = [
    "contains_real_paper_full_text",
    "contains_user_private_text",
    "contains_raw_transcript",
    "contains_external_upload",
    "contains_memory_write",
    "contains_original_paragraph",
    "contains_rewrite_text",
]

FORBIDDEN_PAYLOAD_KEYS = {
    "raw_paper_text",
    "paper_content",
    "paper_excerpt",
    "citation_original_text",
    "user_identity",
    "author_identity",
    "author_name",
    "advisor_comment",
    "raw_transcript",
    "private_paper_text",
    "paragraph",
    "paragraph_text",
    "content",
    "text_span",
    "original_text",
    "revised_text",
    "rewrite_text",
    "full_text",
}

FORBIDDEN_CONTENT_MARKERS = {
    "REAL_PAPER_TEXT",
    "USER_PRIVATE_TEXT",
    "RAW_TRANSCRIPT",
    "AUTHOR_IDENTITY",
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


def _load_json_file(bundle: Bundle, filename: str) -> tuple[dict[str, Any] | None, list[dict[str, str]]]:
    if filename not in bundle.files:
        return None, [_issue("required_file_missing", f"missing required file: {filename}", filename)]

    try:
        value = json.loads(bundle.files[filename].decode("utf-8"))
    except Exception as exc:
        return None, [_issue("json_parse_error", f"{filename}: {exc}", filename)]

    if not isinstance(value, dict):
        return None, [_issue("json_not_mapping", f"{filename} must contain an object", filename)]

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


def _walk_forbidden_markers(value: Any, prefix: str = "") -> list[str]:
    found: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            current = f"{prefix}.{key}" if prefix else str(key)
            found.extend(_walk_forbidden_markers(child, current))
    elif isinstance(value, list):
        for idx, child in enumerate(value):
            found.extend(_walk_forbidden_markers(child, f"{prefix}[{idx}]"))
    elif isinstance(value, str):
        for marker in FORBIDDEN_CONTENT_MARKERS:
            if marker in value:
                found.append(prefix or marker)
    return found


def _check_common_payload_safety(documents: dict[str, dict[str, Any]]) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    for filename, document in documents.items():
        for key_path in _walk_forbidden_keys(document):
            issues.append(_issue("forbidden_payload_key", f"{filename}: forbidden payload key: {key_path}", key_path))
        for marker_path in _walk_forbidden_markers(document):
            issues.append(_issue("forbidden_content_marker", f"{filename}: forbidden content marker at {marker_path}", marker_path))
    return issues


def _check_consistency(documents: dict[str, dict[str, Any]]) -> list[dict[str, str]]:
    handoff = documents["WRITELAB_HANDOFF.yaml"]
    diagnosis = documents["DIAGNOSIS_RESULT.json"]
    privacy = documents["PRIVACY_ATTESTATION.yaml"]
    handoff_ids = {
        "WRITELAB_HANDOFF.yaml": handoff.get("handoff_id"),
        "DIAGNOSIS_RESULT.json": diagnosis.get("handoff_id"),
        "PRIVACY_ATTESTATION.yaml": privacy.get("handoff_id"),
    }
    present_ids = {value for value in handoff_ids.values() if value}
    if len(present_ids) != 1:
        return [_issue("handoff_id_mismatch", f"inconsistent handoff_id values: {handoff_ids}")]
    return []


def _check_handoff(document: dict[str, Any]) -> list[dict[str, str]]:
    issues = _schema_errors(document, "writelab_paper_handoff.schema.json", "WRITELAB_HANDOFF.yaml")

    if document.get("content_classification") not in {"synthetic", "redacted_metadata"}:
        issues.append(_issue("blocked_content_classification", "content_classification must be synthetic or redacted_metadata", "content_classification"))

    target_contracts = set(document.get("target_contracts") or [])
    missing = sorted(REQUIRED_TARGET_CONTRACTS - target_contracts)
    for contract_id in missing:
        issues.append(_issue("missing_required_target_contract", f"missing target contract: {contract_id}", "target_contracts"))

    return issues


def _check_diagnosis(document: dict[str, Any]) -> list[dict[str, str]]:
    issues = _schema_errors(document, "writelab_diagnosis_result.schema.json", "DIAGNOSIS_RESULT.json")
    for field in ["contains_text_spans", "contains_original_paragraph", "contains_rewrite_text"]:
        if document.get(field) is not False:
            issues.append(_issue("diagnosis_privacy_violation", f"{field} must be false", field))
    return issues


def _check_privacy_attestation(document: dict[str, Any]) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    required = [
        "handoff_id",
        "contains_real_paper_full_text",
        "contains_user_private_text",
        "contains_raw_transcript",
        "contains_external_upload",
        "contains_memory_write",
        "contains_original_paragraph",
        "contains_rewrite_text",
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

    return issues


def validate_writelab_handoff(source: str | Path) -> dict[str, Any]:
    """Validate a WriteLab diagnosis handoff directory or ZIP packet."""
    result: dict[str, Any] = {
        "result": "pending",
        "source": str(source),
        "source_type": None,
        "validated_files": [],
        "checks": {
            "required_files_present": False,
            "schemas_valid": False,
            "privacy_boundaries_valid": False,
            "handoff_consistency_valid": False,
            "target_contracts_valid": False,
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
    handoff, file_issues = _load_yaml_file(bundle, "WRITELAB_HANDOFF.yaml")
    result["blocking_issues"].extend(file_issues)
    if handoff is not None:
        documents["WRITELAB_HANDOFF.yaml"] = handoff

    diagnosis, file_issues = _load_json_file(bundle, "DIAGNOSIS_RESULT.json")
    result["blocking_issues"].extend(file_issues)
    if diagnosis is not None:
        documents["DIAGNOSIS_RESULT.json"] = diagnosis

    privacy, file_issues = _load_yaml_file(bundle, "PRIVACY_ATTESTATION.yaml")
    result["blocking_issues"].extend(file_issues)
    if privacy is not None:
        documents["PRIVACY_ATTESTATION.yaml"] = privacy

    if len(documents) != 3:
        result["result"] = "fail"
        return result

    result["blocking_issues"].extend(_check_handoff(documents["WRITELAB_HANDOFF.yaml"]))
    result["blocking_issues"].extend(_check_diagnosis(documents["DIAGNOSIS_RESULT.json"]))
    result["blocking_issues"].extend(_check_privacy_attestation(documents["PRIVACY_ATTESTATION.yaml"]))
    result["blocking_issues"].extend(_check_consistency(documents))
    result["blocking_issues"].extend(_check_common_payload_safety(documents))

    issue_codes = {issue["code"] for issue in result["blocking_issues"]}
    result["checks"]["schemas_valid"] = "schema_violation" not in issue_codes
    result["checks"]["privacy_boundaries_valid"] = not any(
        code
        in {
            "blocked_content_classification",
            "privacy_attestation_violation",
            "diagnosis_privacy_violation",
            "forbidden_payload_key",
            "forbidden_content_marker",
            "memory_write_policy_blocked",
        }
        for code in issue_codes
    )
    result["checks"]["handoff_consistency_valid"] = "handoff_id_mismatch" not in issue_codes
    result["checks"]["target_contracts_valid"] = "missing_required_target_contract" not in issue_codes

    result["result"] = "pass" if not result["blocking_issues"] else "fail"
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate a metadata-only WriteLab paper handoff packet")
    parser.add_argument("source", help="Directory or ZIP containing WriteLab handoff files")
    parser.add_argument("--json-output", help="Optional path to write validation JSON")
    args = parser.parse_args(argv)

    result = validate_writelab_handoff(args.source)
    output = json.dumps(result, ensure_ascii=False, indent=2)
    print(output)

    if args.json_output:
        Path(args.json_output).write_text(output + "\n", encoding="utf-8")

    return 0 if result["result"] == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())

