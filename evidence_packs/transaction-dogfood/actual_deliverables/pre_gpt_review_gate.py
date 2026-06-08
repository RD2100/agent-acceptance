#!/usr/bin/env python3
"""
pre_gpt_review_gate.py — Gate evidence pack before CDP submission.
Runs linter + targeted checks. Blocks submission on SD-01 or missing evidence.
"""
import json, sys
from pathlib import Path
from evidence_pack_linter import lint

REPO = Path(__file__).resolve().parent.parent

def gate(pack_dir: str) -> dict:
    """Run pre-GPT-review gate. Returns verdict. Blocks on errors."""
    result = lint(pack_dir)

    # Additional checks
    p = Path(pack_dir)
    extra_checks = {}

    # Actual deliverables content check
    ad = p / "actual_deliverables"
    if ad.is_dir():
        files = list(ad.rglob("*"))
        extra_checks["deliverable_count"] = len(files)
        if len(files) == 0:
            result["errors"].append("SD-01: summary-only pack — no actual deliverables")

    # Manifest hash check
    manifest = p / "PACK_MANIFEST.md"
    if manifest.exists():
        content = manifest.read_text(encoding="utf-8", errors="replace")
        extra_checks["has_sha256_entries"] = "sha256" in content.lower() or "|" in content

    # Blocking decision
    blocked = len(result["errors"]) > 0
    return {
        "gate_passed": not blocked,
        "errors": result["errors"],
        "warnings": result.get("warnings", []),
        "extra_checks": extra_checks,
        "recommendation": "READY for GPT submission" if not blocked else "BLOCKED: fix errors before CDP submit",
    }

def main():
    if len(sys.argv) < 2:
        print("Usage: pre_gpt_review_gate.py <pack_dir>")
        sys.exit(1)
    r = gate(sys.argv[1])
    print(json.dumps(r, indent=2, ensure_ascii=False))
    sys.exit(0 if r["gate_passed"] else 1)

if __name__ == "__main__":
    main()
