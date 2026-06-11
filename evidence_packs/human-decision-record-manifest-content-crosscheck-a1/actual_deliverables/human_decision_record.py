#!/usr/bin/env python3
"""
human_decision_record.py — Human-required decision record management.

Creates and validates decision records for the `human_required` state
in the process state machine. When GPT review returns `human_required`,
a human decision must be recorded before transitioning to `gate_passing`.

Per PROCESS_STATE_MACHINE.json T10:
  human_required → gate_passing guard:
    human_decision_recorded AND decision_evidence_attached

Usage:
    # Create a new decision record
    python scripts/human_decision_record.py create \
        --task-id "TASK-ID" \
        --decision-type "override|approve|reject|defer" \
        --decision-reason "Why this decision was made" \
        --decision-maker "human_operator_id" \
        [--evidence-files "file1,file2"]

    # Validate an existing decision record
    python scripts/human_decision_record.py validate \
        --record-path "./human_decisions/task_id.json"
"""

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path, PurePosixPath, PureWindowsPath

TZ_CST = timezone(timedelta(hours=8))
REPO = Path(__file__).resolve().parent.parent

VALID_DECISION_TYPES = {"override", "approve", "reject", "defer"}
REQUIRED_FIELDS = [
    "task_id", "decision_type", "decision_reason",
    "decision_maker", "decision_timestamp",
]


def compute_evidence_hashes(evidence_files: list, repo_root: str = None) -> dict:
    """Compute SHA-256 hashes for evidence files.

    Args:
        evidence_files: List of evidence file paths.
        repo_root: Optional repo root for resolving relative paths.

    Returns:
        dict mapping file path → sha256 hex digest (or "MISSING" / "ERROR").
    """
    hashes = {}
    root = Path(repo_root) if repo_root else None
    for ef in evidence_files:
        ef_path = Path(ef)
        if not ef_path.is_absolute() and root:
            ef_path = root / ef
        try:
            if ef_path.exists():
                hashes[ef] = hashlib.sha256(ef_path.read_bytes()).hexdigest()
            else:
                hashes[ef] = "MISSING"
        except (OSError, PermissionError) as e:
            hashes[ef] = f"ERROR:{e}"
    return hashes


def verify_evidence_hashes(
    evidence_files: list,
    stored_hashes: dict,
    repo_root: str = None,
) -> dict:
    """Verify evidence file hashes against stored values.

    Returns:
        dict with match, mismatch, missing, errors lists.
    """
    result = {"match": [], "mismatch": [], "missing": [], "errors": []}
    root = Path(repo_root) if repo_root else None
    for ef in evidence_files:
        ef_path = Path(ef)
        if not ef_path.is_absolute() and root:
            ef_path = root / ef
        stored = stored_hashes.get(ef)
        if not stored or stored == "MISSING":
            result["missing"].append(ef)
            continue
        if stored.startswith("ERROR:"):
            result["errors"].append(ef)
            continue
        try:
            if ef_path.exists():
                actual = hashlib.sha256(ef_path.read_bytes()).hexdigest()
                if actual == stored:
                    result["match"].append(ef)
                else:
                    result["mismatch"].append(ef)
            else:
                result["missing"].append(ef)
        except (OSError, PermissionError) as e:
            result["errors"].append(ef)
    return result


def _normalize_path(p: str) -> str:
    """Normalize a file path for cross-platform comparison."""
    return PurePosixPath(PureWindowsPath(p)).as_posix().lower()


def parse_manifest_paths(manifest_content: str) -> list:
    """Extract file paths from PACK_MANIFEST.md table rows.

    Parses backtick-wrapped paths in markdown table rows like:
        | 1 | `scripts/human_decision_record.py` | deliverable | ...

    Returns:
        List of normalized path strings.
    """
    paths = []
    for line in manifest_content.splitlines():
        line = line.strip()
        if line.startswith("|") and "`" in line:
            # Skip header/separator rows
            if "---" in line or "Path" in line and "Role" in line:
                continue
            # Extract backtick-wrapped path (first backtick pair in the row)
            parts = line.split("`")
            if len(parts) >= 3:
                raw_path = parts[1]  # content between first pair of backticks
                if raw_path and "/" in raw_path or "\\" in raw_path or "." in raw_path:
                    paths.append(_normalize_path(raw_path))
    return paths


def crosscheck_manifest_content(
    evidence_files: list,
    manifest_entry_path: str,
    repo_root: str,
) -> dict:
    """Parse PACK_MANIFEST.md and verify all evidence_files are listed.

    Args:
        evidence_files: List of evidence file paths from the record.
        manifest_entry_path: The path to PACK_MANIFEST.md as stored in evidence_files.
        repo_root: Repo root directory for resolving paths.

    Returns:
        dict with checked, all_listed, not_in_manifest, manifest_paths_count.
    """
    result = {
        "checked": False,
        "all_listed": False,
        "not_in_manifest": [],
        "manifest_paths_count": 0,
    }

    # Resolve manifest file on disk
    m_path = Path(manifest_entry_path)
    if not m_path.is_absolute():
        m_path = Path(repo_root) / manifest_entry_path

    if not m_path.exists():
        return result  # Can't parse if file doesn't exist

    try:
        content = m_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return result

    manifest_paths = parse_manifest_paths(content)
    result["checked"] = True
    result["manifest_paths_count"] = len(manifest_paths)

    manifest_set = set(manifest_paths)
    for ef in evidence_files:
        normalized = _normalize_path(ef)
        if normalized not in manifest_set:
            result["not_in_manifest"].append(ef)

    result["all_listed"] = len(result["not_in_manifest"]) == 0
    return result


def create_record(
    task_id: str,
    decision_type: str,
    decision_reason: str,
    decision_maker: str,
    evidence_files: list = None,
    gpt_verdict_context: str = None,
    repo_root: str = None,
    compute_hashes: bool = False,
) -> dict:
    """Create a human decision record.

    Args:
        task_id: The task ID this decision relates to.
        decision_type: One of override, approve, reject, defer.
        decision_reason: Why this decision was made.
        decision_maker: Human operator identifier.
        evidence_files: Optional list of supporting evidence file paths.
        gpt_verdict_context: Optional context from the GPT review.
        repo_root: Optional repo root for resolving evidence paths.
        compute_hashes: If True, compute SHA-256 hashes for evidence files.

    Returns:
        dict — the decision record.
    """
    if decision_type not in VALID_DECISION_TYPES:
        raise ValueError(
            f"Invalid decision_type '{decision_type}'. "
            f"Must be one of: {', '.join(sorted(VALID_DECISION_TYPES))}"
        )

    if not task_id or not str(task_id).strip():
        raise ValueError("task_id must not be empty")

    if not decision_reason or not decision_reason.strip():
        raise ValueError("decision_reason must not be empty")

    if not decision_maker or not decision_maker.strip():
        raise ValueError("decision_maker must not be empty")

    now = datetime.now(tz=TZ_CST)
    record = {
        "schema_version": "1.2.0",
        "task_id": task_id,
        "decision_type": decision_type,
        "decision_reason": decision_reason.strip(),
        "decision_maker": decision_maker.strip(),
        "decision_timestamp": now.isoformat(),
        "evidence_files": evidence_files or [],
        "evidence_hashes": {},
        "gpt_verdict_context": gpt_verdict_context or "",
        "exit_conditions_met": {
            "human_decision_recorded": True,
            "decision_evidence_attached": len(evidence_files or []) > 0,
        },
    }

    # Compute evidence hashes if requested
    if compute_hashes and evidence_files:
        record["evidence_hashes"] = compute_evidence_hashes(evidence_files, repo_root)

    return record


def validate_record(record_path: str, repo_root: str = None) -> dict:
    """Validate a human decision record.

    Args:
        record_path: Path to the decision record JSON file.
        repo_root: Optional repo root for resolving relative evidence file paths.

    Returns:
        dict with valid, errors, and the record if parseable.
    """
    errors = []
    record = None

    path = Path(record_path)
    if not path.exists():
        return {"valid": False, "errors": ["record file not found"], "record": None}

    try:
        record = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        return {"valid": False, "errors": [f"invalid JSON: {e}"], "record": None}

    # Check required fields
    for field in REQUIRED_FIELDS:
        if not record.get(field):
            errors.append(f"missing required field: {field}")

    # Validate decision_type
    dt = record.get("decision_type", "")
    if dt and dt not in VALID_DECISION_TYPES:
        errors.append(
            f"invalid decision_type '{dt}', "
            f"must be one of: {', '.join(sorted(VALID_DECISION_TYPES))}"
        )

    # Validate evidence attachment
    evidence = record.get("evidence_files", [])
    has_evidence = len(evidence) > 0

    # Evidence file binding: check if referenced files exist on disk
    evidence_binding = {"checked": False, "all_exist": False, "missing": [], "found": []}
    if repo_root and has_evidence:
        evidence_binding["checked"] = True
        root = Path(repo_root)
        for ef in evidence:
            ef_path = Path(ef)
            if not ef_path.is_absolute():
                ef_path = root / ef
            if ef_path.exists():
                evidence_binding["found"].append(ef)
            else:
                evidence_binding["missing"].append(ef)
        evidence_binding["all_exist"] = len(evidence_binding["missing"]) == 0
        if not evidence_binding["all_exist"]:
            for m in evidence_binding["missing"]:
                errors.append(f"evidence file not found: {m}")

    # Evidence hash verification: check if stored hashes match current files
    hash_verification = {"checked": False, "match": [], "mismatch": [], "missing": [], "errors": []}
    stored_hashes = record.get("evidence_hashes", {})
    if repo_root and stored_hashes and has_evidence:
        hash_verification["checked"] = True
        hv = verify_evidence_hashes(evidence, stored_hashes, repo_root)
        hash_verification.update(hv)
        if hv["mismatch"]:
            for m in hv["mismatch"]:
                errors.append(f"evidence hash mismatch: {m}")
        if hv["missing"]:
            for m in hv["missing"]:
                errors.append(f"evidence file missing for hash check: {m}")

    # Check exit conditions
    exit_met = record.get("exit_conditions_met", {})
    if not exit_met.get("human_decision_recorded", False):
        errors.append("exit condition not met: human_decision_recorded")

    if not has_evidence:
        errors.append("no evidence files attached — T10 guard requires decision_evidence_attached")

    # Manifest binding: strict check — PACK_MANIFEST.md must be in evidence files
    # Uses exact filename matching (not substring/case-insensitive)
    manifest_binding = {"pack_manifest_included": False, "pack_manifest_file_exists": False, "pack_manifest_hash_bound": False}
    if has_evidence:
        # Strict: exact filename match via Path.name
        manifest_entries = [ef for ef in evidence if Path(ef).name == "PACK_MANIFEST.md"]
        manifest_binding["pack_manifest_included"] = len(manifest_entries) > 0
        if not manifest_binding["pack_manifest_included"]:
            errors.append("PACK_MANIFEST.md not listed in evidence_files — strict manifest binding required")

        # Check if PACK_MANIFEST file exists on disk (when repo_root provided)
        if repo_root and manifest_entries:
            root = Path(repo_root)
            for me in manifest_entries:
                me_path = Path(me)
                if not me_path.is_absolute():
                    me_path = root / me
                if me_path.exists():
                    manifest_binding["pack_manifest_file_exists"] = True
                    break
            # Fail-closed: when repo_root provided, manifest file MUST exist
            if not manifest_binding["pack_manifest_file_exists"]:
                errors.append("PACK_MANIFEST.md file not found on disk — manifest binding requires file existence")

            # Check if PACK_MANIFEST is hash-bound in evidence_hashes
            stored_hashes = record.get("evidence_hashes", {})
            for me in manifest_entries:
                if me in stored_hashes and stored_hashes[me] not in ("MISSING", ""):
                    manifest_binding["pack_manifest_hash_bound"] = True
                    break
            # Fail-closed: when repo_root provided, manifest MUST be hash-bound
            if not manifest_binding["pack_manifest_hash_bound"]:
                errors.append("PACK_MANIFEST.md not hash-bound in evidence_hashes — manifest must be integrity-verified")

    # Hash completeness: when evidence_hashes is non-empty, all evidence_files must have hash entries
    # Also detects orphaned hash entries (in evidence_hashes but not in evidence_files) — potential tampering
    stored_hashes = record.get("evidence_hashes", {})
    hash_completeness = {"checked": False, "complete": False, "missing_hash_entries": [], "orphaned_hash_entries": []}
    if stored_hashes and has_evidence:
        hash_completeness["checked"] = True
        # Check: evidence_files → evidence_hashes (missing entries)
        for ef in evidence:
            if ef not in stored_hashes:
                hash_completeness["missing_hash_entries"].append(ef)
        # Check: evidence_hashes → evidence_files (orphaned entries — hashes without corresponding files)
        evidence_set = set(evidence)
        for hk in stored_hashes:
            if hk not in evidence_set:
                hash_completeness["orphaned_hash_entries"].append(hk)
        hash_completeness["complete"] = (
            len(hash_completeness["missing_hash_entries"]) == 0
            and len(hash_completeness["orphaned_hash_entries"]) == 0
        )
        if not hash_completeness["complete"]:
            for m in hash_completeness["missing_hash_entries"]:
                errors.append(f"evidence file missing from evidence_hashes: {m}")
            for o in hash_completeness["orphaned_hash_entries"]:
                errors.append(f"orphaned hash entry in evidence_hashes (not in evidence_files): {o}")

    # Manifest content crosscheck: parse PACK_MANIFEST.md and verify all evidence_files listed
    # Only enforced when manifest has parseable table rows (manifest_paths_count > 0)
    manifest_crosscheck = {"checked": False, "all_listed": False, "not_in_manifest": [], "manifest_paths_count": 0}
    if repo_root and has_evidence and manifest_binding.get("pack_manifest_included", False):
        # Find the manifest entry path
        manifest_entry = None
        for ef in evidence:
            if Path(ef).name == "PACK_MANIFEST.md":
                manifest_entry = ef
                break
        if manifest_entry:
            xcheck = crosscheck_manifest_content(evidence, manifest_entry, repo_root)
            manifest_crosscheck.update(xcheck)
            # Only enforce crosscheck when manifest has parseable content (table rows found)
            if xcheck["checked"] and xcheck["manifest_paths_count"] > 0 and not xcheck["all_listed"]:
                for ef in xcheck["not_in_manifest"]:
                    errors.append(f"evidence file not listed in PACK_MANIFEST.md: {ef}")

    valid = len(errors) == 0
    return {
        "valid": valid,
        "errors": errors,
        "record": record,
        "exit_conditions": {
            "human_decision_recorded": not any("human_decision_recorded" in e for e in errors),
            "decision_evidence_attached": has_evidence,
        },
        "evidence_binding": evidence_binding,
        "hash_verification": hash_verification,
        "manifest_binding": manifest_binding,
        "hash_completeness": hash_completeness,
        "manifest_crosscheck": manifest_crosscheck,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Human Decision Record — create/validate decision records for human_required state"
    )
    sub = parser.add_subparsers(dest="command")

    # Create subcommand
    create_p = sub.add_parser("create", help="Create a new decision record")
    create_p.add_argument("--task-id", required=True)
    create_p.add_argument("--decision-type", required=True, choices=sorted(VALID_DECISION_TYPES))
    create_p.add_argument("--decision-reason", required=True)
    create_p.add_argument("--decision-maker", required=True)
    create_p.add_argument("--evidence-files", default=None, help="Comma-separated evidence file paths")
    create_p.add_argument("--gpt-verdict-context", default=None)
    create_p.add_argument("--repo-root", default=None, help="Repo root for resolving evidence paths")
    create_p.add_argument("--compute-hashes", action="store_true", default=False, help="Compute SHA-256 for evidence files")
    create_p.add_argument("--output", required=True, help="Output JSON file path")

    # Validate subcommand
    validate_p = sub.add_parser("validate", help="Validate an existing decision record")
    validate_p.add_argument("--record-path", required=True)
    validate_p.add_argument("--repo-root", default=None, help="Repo root for evidence binding and hash verification")

    args = parser.parse_args()

    if args.command == "create":
        evidence = [f.strip() for f in args.evidence_files.split(",")] if args.evidence_files else []
        record = create_record(
            task_id=args.task_id,
            decision_type=args.decision_type,
            decision_reason=args.decision_reason,
            decision_maker=args.decision_maker,
            evidence_files=evidence,
            gpt_verdict_context=args.gpt_verdict_context,
            repo_root=args.repo_root,
            compute_hashes=args.compute_hashes,
        )
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(record, indent=2, ensure_ascii=False), encoding="utf-8")
        print(json.dumps(record, indent=2, ensure_ascii=False))
        print(f"\nRecord saved to: {out_path}")
        sys.exit(0)

    elif args.command == "validate":
        result = validate_record(args.record_path, repo_root=args.repo_root)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        if result["valid"]:
            print("\nRECORD OK: All exit conditions met for T10 transition")
            sys.exit(0)
        else:
            print("\nRECORD INVALID:")
            for e in result["errors"]:
                print(f"  ERROR: {e}")
            sys.exit(1)

    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
