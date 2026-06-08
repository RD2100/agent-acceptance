#!/usr/bin/env python3
"""
gpt_review_transaction.py — Complete GPT review transaction runner.
Runs: pre-gate → lint → (CDP submit — manual) → verify reply → closure check.
"""
import json, sys, subprocess
from pathlib import Path
from datetime import datetime, timezone

REPO = Path(__file__).resolve().parent.parent

def run_transaction(pack_dir: str, task_id: str = None) -> dict:
    """Run the full pre-submission checklist. Returns verdict."""
    steps = {}
    now = datetime.now(timezone.utc).isoformat()

    # Step 1: Pre-GPT review gate
    r = subprocess.run([sys.executable, "scripts/pre_gpt_review_gate.py", pack_dir],
                       capture_output=True, text=True, timeout=30, cwd=str(REPO))
    try:
        gate_result = json.loads(r.stdout)
    except:
        gate_result = {"gate_passed": False, "errors": ["gate parse error"]}
    steps["1_pre_gate"] = {"passed": gate_result.get("gate_passed", False), "result": gate_result}

    # Step 2: Evidence pack linter
    r = subprocess.run([sys.executable, "scripts/evidence_pack_linter.py", pack_dir],
                       capture_output=True, text=True, timeout=30, cwd=str(REPO))
    try:
        lint_result = json.loads(r.stdout)
    except:
        lint_result = {"valid": False, "errors": ["linter parse error"]}
    steps["2_linter"] = {"passed": lint_result.get("valid", False), "result": lint_result}

    # Step 3: Check for GPT reply file
    reply_files = list(Path(pack_dir).glob("GPT_REVIEW_RESULT*.txt"))
    steps["3_reply_exists"] = len(reply_files) > 0

    # Step 4: If reply exists, verify it
    if reply_files:
        latest_reply = sorted(reply_files)[-1]
        r = subprocess.run([sys.executable, "scripts/verify_gpt_reply.py", str(latest_reply), task_id or "unknown"],
                          capture_output=True, text=True, timeout=10, cwd=str(REPO))
        steps["4_reply_verified"] = r.returncode == 0
    else:
        steps["4_reply_verified"] = None

    all_pass = steps["1_pre_gate"]["passed"] and steps["2_linter"]["passed"]
    return {
        "timestamp": now,
        "task_id": task_id,
        "ready_for_cdp_submit": all_pass,
        "steps": steps,
        "next_action": "CDP submit the evidence pack" if all_pass else "Fix errors before submitting",
    }

def main():
    if len(sys.argv) < 2:
        print("Usage: gpt_review_transaction.py <pack_dir> [task_id]")
        sys.exit(1)
    r = run_transaction(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
    print(json.dumps(r, indent=2, ensure_ascii=False))
    sys.exit(0 if r["ready_for_cdp_submit"] else 1)

if __name__ == "__main__":
    main()
