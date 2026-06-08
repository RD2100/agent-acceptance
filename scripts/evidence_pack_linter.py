#!/usr/bin/env python3
"""
evidence_pack_linter.py — Pre-submission evidence pack quality checker.
Detects SD-01 (summary-only), missing outputs, stale files, missing requirements.
Usage: python scripts/evidence_pack_linter.py <pack_dir>
"""
import json, sys, os
from pathlib import Path

REQUIRED_FILES = [
    "CLOSURE_REPORT.md", "GPT_REVIEW_PROMPT.md", "PACK_MANIFEST.md",
    "SAFETY_ATTESTATION.md",
]
REQUIRED_DIRS = ["actual_deliverables", "reports"]
EXPECTED_REPORTS = ["TARGETED_TEST_OUTPUT.txt", "TEST_OUTPUT.txt"]

def lint(pack_dir: str) -> dict:
    p = Path(pack_dir)
    if not p.exists():
        return {"valid": False, "errors": [f"pack directory not found: {pack_dir}"], "warnings": []}

    errors = []
    warnings = []

    # Required files
    for f in REQUIRED_FILES:
        if not (p / f).exists():
            errors.append(f"missing required file: {f}")

    # Required dirs
    for d in REQUIRED_DIRS:
        if not (p / d).is_dir():
            errors.append(f"missing required directory: {d}")

    # Actual deliverables check
    ad = p / "actual_deliverables"
    if ad.is_dir():
        files = list(ad.rglob("*"))
        if len(files) == 0:
            errors.append("actual_deliverables is empty — summary-only risk (SD-01)")
        elif len(files) <= 3:
            warnings.append("actual_deliverables has <= 3 files — thin evidence")

    # Reports check
    reports = p / "reports"
    if reports.is_dir():
        for r in EXPECTED_REPORTS:
            if not (reports / r).exists():
                warnings.append(f"missing expected report: {r}")

    # Check for stale PILOT_OUTPUT
    for old in [p / "reports" / "PILOT_OUTPUT.txt", p / "reports" / "TEST_OUTPUT.txt"]:
        if old.exists() and "_PASS" not in old.name and "R6" not in old.name:
            content = old.read_text(encoding="utf-8", errors="replace")[:200] if old.exists() else ""
            if "FAIL" in content or "exit=1" in content:
                warnings.append(f"stale/failing output: {old.name}")

    # SAEFTY attestation
    safety = p / "SAFETY_ATTESTATION.md"
    if safety.exists():
        content = safety.read_text(encoding="utf-8", errors="replace")
        if "true" not in content.lower():
            warnings.append("SAFETY_ATTESTATION may be empty or thin")

    valid = len(errors) == 0
    return {
        "valid": valid,
        "errors": errors,
        "warnings": warnings,
        "summary_only_risk": "SD-01" if any("SD-01" in e for e in errors) else "none",
        "recommendation": "ready for GPT submission" if valid else "FIX ERRORS before submitting",
    }

def main():
    if len(sys.argv) < 2:
        print("Usage: evidence_pack_linter.py <pack_dir>")
        sys.exit(1)
    result = lint(sys.argv[1])
    print(json.dumps(result, indent=2, ensure_ascii=False))
    sys.exit(0 if result["valid"] else 1)

if __name__ == "__main__":
    main()
