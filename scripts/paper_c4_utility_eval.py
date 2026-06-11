#!/usr/bin/env python3
"""paper_c4_utility_eval.py — Self-evaluation report for C4 pipeline."""
import json, sys, subprocess
from datetime import datetime, timezone
from pathlib import Path

def evaluate():
    checks = {}
    # Test each component
    r1 = subprocess.run(["python", "-m", "pytest", "tests/test_paper_c4_section_review.py", "-q"], capture_output=True, text=True)
    checks["validator_tests"] = r1.returncode == 0

    r2 = subprocess.run(["python", "scripts/paper_c4_section_review.py", "--input", "examples/paper_c4_section_review/SECTION_REVIEW_INPUT.synthetic.yaml"], capture_output=True, text=True)
    checks["synthetic_review"] = r2.returncode == 0

    r3 = subprocess.run(["python", "scripts/paper_c4_section_review.py", "--input", "examples/paper_c4_section_review/PILOT_INPUT.user_sanitized.yaml"], capture_output=True, text=True)
    checks["sanitized_pilot"] = r3.returncode == 0

    all_ok = all(checks.values())
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "overall": "PASS" if all_ok else "FAIL",
        "checks": checks,
        "pipeline_status": "operational" if all_ok else "degraded",
        "ready_for_human_review": all_ok,
        "limitations": ["synthetic/sanitized only", "no real paper ingestion", "bounded to section-level"],
    }

def main():
    r = evaluate()
    print(json.dumps(r, indent=2, ensure_ascii=False))
    sys.exit(0 if r["overall"] == "PASS" else 1)

if __name__ == "__main__":
    main()
