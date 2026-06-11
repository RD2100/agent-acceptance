#!/usr/bin/env python3
"""
startup_read_gate.py — Startup Read Gate enforcement script.

Verifies that an agent has completed all required reads before starting work.
Per HANDOFF_WORKFLOW_HARDENING_PLAN.md section 5.7.

Usage:
    python scripts/startup_read_gate.py \
        --task-id "TASK-ID" \
        --proof-path "./startup_proofs/task_id.json" \
        --required-reads "./NEXT_AGENT_REQUIRED_READS.json" \
        [--strict]

Exit codes:
    0 — gate PASS (all required reads verified)
    1 — gate FAIL (missing reads, hash mismatch, or invalid proof)

Strict mode (--strict):
    - task_id mismatch becomes error (instead of warning)
    - P0/must_read files without summary_hash in proof become error
    - Non-existent fail_closed files with proof hash become error
    - coverage_ratio uses matched required reads / must_read_count
"""

import argparse
import hashlib
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent


def sha256_file(path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _normalize_path(p: str) -> str:
    """Normalize path separators for comparison."""
    return p.replace("\\", "/").strip()


def gate(
    task_id: str,
    proof_path: str,
    required_reads_path: str,
    repo_root: str = None,
    strict: bool = False,
) -> dict:
    """Run startup read gate check.

    Args:
        task_id: The task ID being checked.
        proof_path: Path to the startup proof JSON file.
        required_reads_path: Path to the NEXT_AGENT_REQUIRED_READS.json file.
        repo_root: Root directory of the repo (default: auto-detect).
        strict: If True, promote warnings to errors for task_id mismatch,
                missing hashes on P0/must_read files, and non-existent
                fail_closed files.

    Returns:
        dict with gate_passed, errors, warnings, and extra_checks.
    """
    repo = Path(repo_root) if repo_root else REPO
    errors = []
    warnings = []
    extra_checks = {}

    # 1. Check proof file exists
    proof_fp = Path(proof_path)
    if not proof_fp.exists():
        return {
            "gate_passed": False,
            "errors": [f"startup proof file not found: {proof_path}"],
            "warnings": [],
            "extra_checks": {},
            "recommendation": "BLOCKED — no startup proof file",
        }

    try:
        proof = json.loads(proof_fp.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        return {
            "gate_passed": False,
            "errors": [f"invalid startup proof JSON: {e}"],
            "warnings": [],
            "extra_checks": {},
            "recommendation": "BLOCKED — malformed startup proof",
        }

    # 2. Check required reads file exists
    reads_fp = Path(required_reads_path)
    if not reads_fp.exists():
        return {
            "gate_passed": False,
            "errors": [f"required reads file not found: {required_reads_path}"],
            "warnings": [],
            "extra_checks": {},
            "recommendation": "BLOCKED — no required reads definition",
        }

    try:
        reads_def = json.loads(reads_fp.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        return {
            "gate_passed": False,
            "errors": [f"invalid required reads JSON: {e}"],
            "warnings": [],
            "extra_checks": {},
            "recommendation": "BLOCKED — malformed required reads definition",
        }

    # 3. Extract required reads list
    required_reads = reads_def.get("required_reads", [])
    must_read_files = [
        r for r in required_reads
        if r.get("must_read_at_startup", False)
    ]
    extra_checks["total_required_reads"] = len(required_reads)
    extra_checks["must_read_count"] = len(must_read_files)

    # 4. Extract proof's reads_completed
    proof_reads = proof.get("reads_completed", [])
    proof_read_paths = {r.get("file", ""): r for r in proof_reads}
    extra_checks["proof_reads_completed"] = len(proof_reads)

    # 5. Check all must-read files are in proof
    missing_reads = []
    for req in must_read_files:
        req_path = req.get("path", "")
        # Try exact match and normalized match
        if req_path not in proof_read_paths:
            # Try with repo prefix
            alt_path = str(repo / req_path)
            if alt_path not in proof_read_paths:
                missing_reads.append(req_path)

    if missing_reads:
        errors.append(
            f"missing {len(missing_reads)} required reads: "
            + ", ".join(missing_reads[:5])
            + ("..." if len(missing_reads) > 5 else "")
        )

    # 5b. Build lookup: normalized proof path → entry for matching required reads
    proof_read_norm = {}
    for pr in proof_reads:
        norm = _normalize_path(pr.get("file", ""))
        proof_read_norm[norm] = pr

    def _find_proof_entry(req_path: str):
        """Find proof entry matching a required read path."""
        norm = _normalize_path(req_path)
        if norm in proof_read_norm:
            return proof_read_norm[norm]
        # Try with repo prefix
        alt = _normalize_path(str(repo / req_path))
        if alt in proof_read_norm:
            return proof_read_norm[alt]
        return None

    # 5c. Strict: hash presence check for P0/must_read files
    #     If a must_read file has evidence_level P0 or fail_closed_if_missing,
    #     its proof entry MUST include a non-empty summary_hash.
    if strict:
        hash_missing_strict = []
        for req in must_read_files:
            is_p0 = req.get("evidence_level") == "P0"
            is_fail_closed = req.get("fail_closed_if_missing", False)
            if not (is_p0 or is_fail_closed):
                continue
            pe = _find_proof_entry(req.get("path", ""))
            if pe is None:
                continue  # already caught in step 5
            pe_hash = pe.get("summary_hash", "")
            if not pe_hash:
                hash_missing_strict.append(req.get("path", ""))
        if hash_missing_strict:
            errors.append(
                f"strict: {len(hash_missing_strict)} P0/fail_closed file(s) "
                f"missing summary_hash in proof: "
                + ", ".join(hash_missing_strict[:5])
            )
        extra_checks["strict_hash_missing_count"] = len(hash_missing_strict)

    # 6. Verify SHA-256 hashes (optional — only if proof includes hashes)
    hash_mismatches = []
    hash_verified = 0
    hash_nonexistent_fail_closed = []
    for pr in proof_reads:
        proof_file = pr.get("file", "")
        proof_hash = pr.get("summary_hash", "")
        if not proof_hash:
            continue

        # Strip "sha256:" prefix if present
        clean_hash = proof_hash
        if clean_hash.startswith("sha256:"):
            clean_hash = clean_hash[7:]

        # Find the actual file
        actual_path = repo / proof_file
        if not actual_path.exists():
            # Try absolute path
            actual_path = Path(proof_file)

        if actual_path.exists():
            actual_hash = sha256_file(actual_path)
            if actual_hash.lower() != clean_hash.lower():
                hash_mismatches.append(proof_file)
            else:
                hash_verified += 1
        else:
            warnings.append(f"cannot verify hash for non-existent file: {proof_file}")
            # Strict: non-existent file with proof hash + fail_closed → error
            if strict:
                norm_pf = _normalize_path(proof_file)
                for req in must_read_files:
                    req_norm = _normalize_path(req.get("path", ""))
                    alt_norm = _normalize_path(str(repo / req.get("path", "")))
                    if norm_pf in (req_norm, alt_norm):
                        if req.get("fail_closed_if_missing", False):
                            hash_nonexistent_fail_closed.append(proof_file)
                        break

    if hash_mismatches:
        errors.append(
            f"hash mismatch for {len(hash_mismatches)} files: "
            + ", ".join(hash_mismatches[:5])
        )
    if hash_nonexistent_fail_closed:
        errors.append(
            f"strict: {len(hash_nonexistent_fail_closed)} fail_closed file(s) "
            f"not found on disk despite proof hash: "
            + ", ".join(hash_nonexistent_fail_closed[:5])
        )

    extra_checks["hash_verified"] = hash_verified
    extra_checks["hash_mismatches"] = len(hash_mismatches)
    extra_checks["hash_nonexistent_fail_closed"] = len(hash_nonexistent_fail_closed)

    # 7. Check gate_status in proof
    proof_gate_status = proof.get("gate_status", "").lower()
    if proof_gate_status != "pass":
        errors.append(f"proof gate_status is '{proof_gate_status}', expected 'pass'")

    # 8. Check task_id match
    proof_task_id = proof.get("task_id", "")
    if task_id and proof_task_id:
        if task_id.upper() != proof_task_id.upper():
            msg = f"task_id mismatch: expected {task_id}, proof has {proof_task_id}"
            if strict:
                errors.append(f"strict: {msg}")
            else:
                warnings.append(msg)

    # 9. Coverage ratio — matched required reads / must_read_count
    #    Only count proof entries that match a required must_read file,
    #    not all proof entries (which may include extra non-required reads).
    matched_required = 0
    for req in must_read_files:
        pe = _find_proof_entry(req.get("path", ""))
        if pe is not None:
            matched_required += 1
    coverage = matched_required / len(must_read_files) if must_read_files else 1.0
    extra_checks["coverage_ratio"] = round(coverage, 2)
    extra_checks["matched_required_reads"] = matched_required

    # 10. P0 files check
    p0_reads = [r for r in must_read_files if r.get("evidence_level") == "P0"]
    p0_proof_paths = set()
    for r in p0_reads:
        rp = r.get("path", "")
        if rp in proof_read_paths or str(repo / rp) in proof_read_paths:
            p0_proof_paths.add(rp)
    p0_missing = len(p0_reads) - len(p0_proof_paths)
    if p0_missing > 0:
        errors.append(f"P0 critical: {p0_missing} P0-level required reads missing from proof")
    extra_checks["p0_required"] = len(p0_reads)
    extra_checks["p0_covered"] = len(p0_proof_paths)

    gate_passed = len(errors) == 0
    recommendation = (
        "READY — startup read gate passed"
        if gate_passed
        else f"BLOCKED — {len(errors)} error(s) in startup read proof"
    )

    return {
        "gate_passed": gate_passed,
        "errors": errors,
        "warnings": warnings,
        "extra_checks": extra_checks,
        "recommendation": recommendation,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Startup Read Gate — verify agent has completed required reads"
    )
    parser.add_argument("--task-id", required=True, help="Task ID being checked")
    parser.add_argument(
        "--proof-path", required=True, help="Path to startup proof JSON"
    )
    parser.add_argument(
        "--required-reads",
        required=True,
        help="Path to NEXT_AGENT_REQUIRED_READS.json",
    )
    parser.add_argument(
        "--repo-root", default=None, help="Repo root directory (default: auto-detect)"
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        default=False,
        help="Strict mode: promote task_id mismatch, missing P0 hashes, "
        "and non-existent fail_closed files to errors",
    )

    args = parser.parse_args()
    result = gate(
        task_id=args.task_id,
        proof_path=args.proof_path,
        required_reads_path=args.required_reads,
        repo_root=args.repo_root,
        strict=args.strict,
    )

    print(json.dumps(result, indent=2, ensure_ascii=False))

    if result["gate_passed"]:
        print(f"\nGATE OK: {result['recommendation']}")
        sys.exit(0)
    else:
        print(f"\nGATE BLOCKED: {result['recommendation']}")
        for e in result["errors"]:
            print(f"  ERROR: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
