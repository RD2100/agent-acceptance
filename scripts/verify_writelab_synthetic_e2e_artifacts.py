"""Verify retained artifacts from the WriteLab synthetic handoff E2E probe."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import zipfile
from pathlib import Path
from typing import Any

from validate_writelab_handoff import validate_writelab_handoff


EXPECTED_ZIP_FILES = [
    "DIAGNOSIS_RESULT.json",
    "PACK_MANIFEST.md",
    "PRIVACY_ATTESTATION.yaml",
    "WRITELAB_HANDOFF.yaml",
]
REQUIRED_FILES = [
    "PROBE_OUTPUT.txt",
    "API_PROBE_OUTPUT.json",
    "writelab-handoff.zip",
    "VALIDATION_OUTPUT.json",
    "MARKER_SCAN_OUTPUT.json",
    "TEMP_DB_CLEANUP_CHECK.txt",
    "HANDOFF_SAFETY_SCAN.json",
    "HASHES.txt",
]
FORBIDDEN_MARKERS = [
    "REAL_PAPER_TEXT",
    "USER_PRIVATE_TEXT",
    "RAW_TRANSCRIPT",
    "AUTHOR_IDENTITY",
]
RAW_SYNTHETIC_PAYLOAD_MARKERS = [
    "synthetic internal explanation",
    "synthetic raw span",
    "synthetic risk span",
]
TEMP_DB_PATTERNS = [
    "*.sqlite",
    "*.sqlite-wal",
    "*.sqlite-shm",
    "*.db",
]
HASH_EXCLUDES = {
    "HASHES.txt",
    "ARTIFACT_VERIFY_OUTPUT.json",
    "ARTIFACT_VERIFY_STDOUT.txt",
}


def _issue(code: str, message: str, path: str | None = None) -> dict[str, str]:
    item = {"code": code, "message": message}
    if path:
        item["path"] = path
    return item


def _read_text(path: Path) -> str:
    data = path.read_bytes()
    for encoding in ["utf-8-sig", "utf-16"]:
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="replace")


def _load_json_file(path: Path) -> tuple[dict[str, Any] | None, list[dict[str, str]]]:
    try:
        value = json.loads(_read_text(path))
    except Exception as exc:
        return None, [_issue("json_parse_error", f"{path.name}: {exc}", str(path))]
    if not isinstance(value, dict):
        return None, [_issue("json_not_object", f"{path.name} must contain an object", str(path))]
    return value, []


def _check_required_files(output_dir: Path) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    for filename in REQUIRED_FILES:
        path = output_dir / filename
        if not path.exists() or not path.is_file():
            issues.append(_issue("required_file_missing", f"missing required file: {filename}", filename))
    return issues


def _check_probe_output(output_dir: Path) -> list[dict[str, str]]:
    probe, issues = _load_json_file(output_dir / "PROBE_OUTPUT.txt")
    if probe is None:
        return issues
    summary = probe.get("summary")
    if probe.get("result") != "pass":
        issues.append(_issue("probe_result_not_pass", "PROBE_OUTPUT result must be pass", "PROBE_OUTPUT.txt"))
    expected_summary = {
        "project_status": 201,
        "report_status": 201,
        "download_status": 200,
        "validation_result": "pass",
        "marker_scan_pass": True,
    }
    if summary != expected_summary:
        issues.append(_issue("probe_summary_mismatch", f"unexpected probe summary: {summary}", "PROBE_OUTPUT.txt"))
    return issues


def _check_api_probe(output_dir: Path) -> list[dict[str, str]]:
    api_probe, issues = _load_json_file(output_dir / "API_PROBE_OUTPUT.json")
    if api_probe is None:
        return issues
    expected_statuses = {
        "project_status": 201,
        "report_status": 201,
        "download_status": 200,
    }
    for field, expected in expected_statuses.items():
        if api_probe.get(field) != expected:
            issues.append(_issue("api_status_mismatch", f"{field} must be {expected}", field))
    if api_probe.get("content_type") != "application/zip":
        issues.append(_issue("api_content_type_mismatch", "content_type must be application/zip", "content_type"))
    if sorted(api_probe.get("zip_namelist") or []) != EXPECTED_ZIP_FILES:
        issues.append(_issue("api_zip_namelist_mismatch", "API probe zip_namelist does not match expected files", "zip_namelist"))
    report_id = api_probe.get("report_id")
    expected_endpoint = f"/api/reports/diagnosis/{report_id}/writelab-handoff.zip"
    if not report_id or api_probe.get("endpoint") != expected_endpoint:
        issues.append(_issue("api_endpoint_report_id_mismatch", "endpoint must contain the recorded report_id", "endpoint"))
    return issues


def _zip_name_is_safe(name: str) -> bool:
    parts = Path(name).parts
    return (
        name in EXPECTED_ZIP_FILES
        and not Path(name).is_absolute()
        and ".." not in parts
        and "\\" not in name
    )


def _checks_all_true(validation: dict[str, Any]) -> bool:
    checks = validation.get("checks")
    return isinstance(checks, dict) and bool(checks) and all(value is True for value in checks.values())


def _check_zip(output_dir: Path) -> list[dict[str, str]]:
    zip_path = output_dir / "writelab-handoff.zip"
    issues: list[dict[str, str]] = []
    try:
        with zipfile.ZipFile(zip_path, "r") as zf:
            names = sorted(zf.namelist())
    except Exception as exc:
        return [_issue("zip_read_error", f"cannot read handoff ZIP: {exc}", str(zip_path))]
    if names != EXPECTED_ZIP_FILES:
        issues.append(_issue("zip_namelist_mismatch", f"unexpected ZIP files: {names}", str(zip_path)))
    for name in names:
        if not _zip_name_is_safe(name):
            issues.append(_issue("zip_unsafe_member_name", f"unsafe ZIP member name: {name}", str(zip_path)))

    current_validation = validate_writelab_handoff(zip_path)
    if current_validation.get("result") != "pass":
        issues.append(_issue("current_validator_failed", "current validator did not pass on handoff ZIP", str(zip_path)))
    if current_validation.get("blocking_issues"):
        issues.append(_issue("current_validator_blocking_issues", "current validator returned blocking issues", str(zip_path)))
    if not _checks_all_true(current_validation):
        issues.append(_issue("current_validator_checks_not_true", "current validator checks must all be true", str(zip_path)))
    return issues


def _check_saved_validation(output_dir: Path) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    filenames = ["VALIDATION_OUTPUT.json"]
    if (output_dir / "VALIDATION_CLI_OUTPUT.json").exists():
        filenames.append("VALIDATION_CLI_OUTPUT.json")
    for filename in filenames:
        validation, file_issues = _load_json_file(output_dir / filename)
        issues.extend(file_issues)
        if validation is None:
            continue
        if validation.get("result") != "pass":
            issues.append(_issue("saved_validation_not_pass", f"{filename} result must be pass", filename))
        if validation.get("blocking_issues") != []:
            issues.append(_issue("saved_validation_blocking_issues", f"{filename} blocking_issues must be empty", filename))
        if not _checks_all_true(validation):
            issues.append(_issue("saved_validation_checks_not_true", f"{filename} checks must all be true", filename))
    return issues


def _check_marker_scans(output_dir: Path) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    marker_scan, file_issues = _load_json_file(output_dir / "MARKER_SCAN_OUTPUT.json")
    issues.extend(file_issues)
    if marker_scan is not None:
        if marker_scan.get("pass") is not True:
            issues.append(_issue("zip_marker_scan_not_pass", "ZIP marker scan must pass", "MARKER_SCAN_OUTPUT.json"))
        if any((marker_scan.get("hits_by_label") or {}).values()):
            issues.append(_issue("zip_marker_hit", "ZIP marker scan reported hits", "MARKER_SCAN_OUTPUT.json"))

    directory_scan_path = output_dir / "DIRECTORY_MARKER_SCAN_OUTPUT.json"
    if directory_scan_path.exists():
        directory_scan, file_issues = _load_json_file(directory_scan_path)
        issues.extend(file_issues)
        if directory_scan is not None:
            if directory_scan.get("pass") is not True:
                issues.append(_issue("directory_marker_scan_not_pass", "directory marker scan must pass", "DIRECTORY_MARKER_SCAN_OUTPUT.json"))
            if directory_scan.get("hit_files"):
                issues.append(_issue("directory_marker_hit", "directory marker scan reported hit files", "DIRECTORY_MARKER_SCAN_OUTPUT.json"))

    for path in output_dir.rglob("*"):
        if not path.is_file() or path.suffix.lower() == ".zip":
            continue
        text = _read_text(path)
        if any(marker in text for marker in FORBIDDEN_MARKERS + RAW_SYNTHETIC_PAYLOAD_MARKERS):
            issues.append(_issue("retained_marker_hit", f"retained evidence contains a forbidden marker label: {path.name}", str(path)))
    return issues


def _check_temp_db_cleanup(output_dir: Path) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    for pattern in TEMP_DB_PATTERNS:
        for path in output_dir.glob(pattern):
            issues.append(_issue("temporary_database_retained", f"temporary database file retained: {path.name}", path.name))
    cleanup_text = _read_text(output_dir / "TEMP_DB_CLEANUP_CHECK.txt")
    if "exists=True" in cleanup_text:
        issues.append(_issue("temporary_database_cleanup_report_failed", "cleanup check reported retained database file", "TEMP_DB_CLEANUP_CHECK.txt"))
    return issues


def _check_test_outputs(output_dir: Path) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    for path in output_dir.glob("*TEST_OUTPUT.txt"):
        text = _read_text(path)
        if re.search(r"(?i)\bskipped\b", text):
            issues.append(_issue("test_output_contains_skip", f"test output contains skipped tests: {path.name}", path.name))
    return issues


def _check_handoff_safety(output_dir: Path) -> list[dict[str, str]]:
    handoff_safety, issues = _load_json_file(output_dir / "HANDOFF_SAFETY_SCAN.json")
    if handoff_safety is None:
        return issues
    if handoff_safety.get("pass") is not True:
        issues.append(_issue("handoff_safety_not_pass", "handoff safety scan must pass", "HANDOFF_SAFETY_SCAN.json"))
    if handoff_safety.get("issues") not in ([], None):
        issues.append(_issue("handoff_safety_issues", "handoff safety scan must not report issues", "HANDOFF_SAFETY_SCAN.json"))
    return issues


def _check_hashes(output_dir: Path) -> list[dict[str, str]]:
    hash_path = output_dir / "HASHES.txt"
    issues: list[dict[str, str]] = []
    recorded: dict[str, str] = {}
    for line in _read_text(hash_path).splitlines():
        line = line.strip()
        if not line:
            continue
        parts = line.split(None, 1)
        if len(parts) != 2:
            issues.append(_issue("hash_line_malformed", f"malformed HASHES line: {line}", "HASHES.txt"))
            continue
        digest, file_path = parts
        recorded[Path(file_path).name] = digest.upper()

    expected_files = {
        path.name
        for path in output_dir.iterdir()
        if path.is_file() and path.name not in HASH_EXCLUDES
    }
    missing = sorted(expected_files - set(recorded))
    for name in missing:
        issues.append(_issue("hash_missing_file", f"HASHES.txt missing file: {name}", "HASHES.txt"))

    for name, expected_hash in sorted(recorded.items()):
        if name in HASH_EXCLUDES:
            continue
        file_path = output_dir / name
        if not file_path.exists() or not file_path.is_file():
            issues.append(_issue("hash_file_missing_on_disk", f"hashed file is missing: {name}", "HASHES.txt"))
            continue
        actual_hash = hashlib.sha256(file_path.read_bytes()).hexdigest().upper()
        if actual_hash != expected_hash:
            issues.append(_issue("hash_mismatch", f"hash mismatch for {name}", "HASHES.txt"))
    return issues


def verify_artifacts(output_dir: str | Path) -> dict[str, Any]:
    path = Path(output_dir)
    result: dict[str, Any] = {
        "result": "pending",
        "output_dir": str(path),
        "checks": {
            "required_files_present": False,
            "probe_output_valid": False,
            "api_probe_valid": False,
            "zip_valid": False,
            "saved_validation_valid": False,
            "marker_scans_valid": False,
            "temporary_database_clean": False,
            "test_outputs_valid": False,
            "handoff_safety_valid": False,
            "hashes_valid": False,
        },
        "blocking_issues": [],
    }

    if not path.exists() or not path.is_dir():
        result["blocking_issues"].append(_issue("output_dir_missing", f"output directory missing: {path}", str(path)))
        result["result"] = "fail"
        return result

    sections = {
        "required_files_present": _check_required_files(path),
        "probe_output_valid": _check_probe_output(path),
        "api_probe_valid": _check_api_probe(path),
        "zip_valid": _check_zip(path),
        "saved_validation_valid": _check_saved_validation(path),
        "marker_scans_valid": _check_marker_scans(path),
        "temporary_database_clean": _check_temp_db_cleanup(path),
        "test_outputs_valid": _check_test_outputs(path),
        "handoff_safety_valid": _check_handoff_safety(path),
        "hashes_valid": _check_hashes(path),
    }

    for check_name, issues in sections.items():
        result["checks"][check_name] = not issues
        result["blocking_issues"].extend(issues)

    result["result"] = "pass" if not result["blocking_issues"] else "fail"
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Verify WriteLab synthetic E2E retained artifacts")
    parser.add_argument("output_dir", help="Probe output directory to verify")
    parser.add_argument("--json-output", help="Optional path to write verification JSON")
    args = parser.parse_args(argv)

    result = verify_artifacts(args.output_dir)
    output = json.dumps(result, ensure_ascii=False, indent=2)
    print(output)
    if args.json_output:
        Path(args.json_output).write_text(output + "\n", encoding="utf-8")
    return 0 if result["result"] == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())
