#!/usr/bin/env python3
"""
review_workflow_ci_gate.py — CI gate for GPT review workflow.
Checks: pre-gate → linter → verify_gpt_reply → transaction ready.
Used in CI/CD to block merge if review evidence is incomplete.
"""
import json, sys, subprocess
from pathlib import Path
from datetime import datetime, timezone

REPO = Path(__file__).resolve().parent.parent

def ci_gate() -> dict:
    checks = {}
    now = datetime.now(timezone.utc).isoformat()

    # 1. Tests pass
    r = subprocess.run([sys.executable, "-m", "pytest", "tests/", "-q", "--tb=line"],
                       capture_output=True, text=True, timeout=60, cwd=str(REPO))
    checks["tests_pass"] = r.returncode == 0

    # 2. AI guard operational
    r = subprocess.run([sys.executable, "tools/ai_guard.py", "staged"],
                       capture_output=True, text=True, timeout=15, cwd=str(REPO))
    checks["ai_guard_ok"] = r.returncode == 0

    # 3. TaskSpecs valid
    r = subprocess.run([sys.executable, "scripts/validate_taskspec.py"],
                       capture_output=True, text=True, timeout=10, cwd=str(REPO))
    checks["taskspecs_valid"] = r.returncode == 0

    # 4. GPT reply guard importable
    try:
        from verify_gpt_reply import verify
        checks["reply_guard_importable"] = True
    except:
        checks["reply_guard_importable"] = False

    # 5. No dirty baseline in staged
    r = subprocess.run(["git", "diff", "--cached", "--name-only"],
                       capture_output=True, text=True, timeout=10, cwd=str(REPO))
    dirty = [f for f in r.stdout.splitlines() if any(d in f for d in ["runs/","HANDOFF","archive/draft",".tmp"])]
    checks["no_dirty_baseline"] = len(dirty) == 0

    all_pass = all(checks.values())
    return {
        "timestamp": now,
        "ci_gate_passed": all_pass,
        "checks": checks,
        "recommendation": "CI PASS — ready for merge" if all_pass else "CI FAILED — fix before merge",
    }

def main():
    r = ci_gate()
    print(json.dumps(r, indent=2, ensure_ascii=False))
    sys.exit(0 if r["ci_gate_passed"] else 1)

if __name__ == "__main__":
    main()
