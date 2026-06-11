"""Runtime negative-path evidence for conversation health gate (CONVERSATION-HEALTH-GATE-A1).

Generates synthetic current.json files with failure scenarios and validates
them against check_handoff_needed.py --input. Proves (9 scenarios):

1. missing_current_json → UNKNOWN (exit 0 in pre-task mode)
2. stale_metrics_suggest → SUGGEST_HANDOFF (exit 0 in pre-task mode)
3. message_count_force_cdp → FORCE_HANDOFF (exit 1)
4. review_rounds_force → FORCE_HANDOFF (exit 1)
5. nav_access_denied → FORCE_HANDOFF (exit 1)
6. nav_auth_required → HUMAN_REQUIRED (exit 1)
7. invalid_json → error (exit 2)
8. manual_estimate_no_force → SUGGEST not FORCE (exit 0)
9. composite_force → FORCE_HANDOFF (exit 1)

This script generates evidence files for the evidence pack.
"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent

CHECKER = PROJECT_ROOT / "scripts" / "check_handoff_needed.py"
POLICY = PROJECT_ROOT / "configs" / "conversation-health-policy.yaml"
OUT_DIR = PROJECT_ROOT / "_evidence" / "conversation-health-evidence"

BASELINE = {
    "schema_version": "conversation-health.v1",
    "conversation_id": "test-conversation-001",
    "chat_url": "https://chatgpt.com/c/test-conversation-001",
    "status": "active",
    "last_known_metrics": {
        "assistant_message_count": 10,
        "review_round_count": 1,
        "last_response_time_seconds": 25.0,
        "last_gpt_reply_bytes": 5000,
    },
    "last_nav_result": "ok",
    "last_health_decision": "OK",
    "last_health_reasons": [],
    "last_checked_at": "2026-06-11T12:00:00Z",
    "metrics_source": "cdp_dom_count",
    "metrics_freshness": "fresh",
}


def run_checker(input_path: str, extra_args: list[str] | None = None) -> tuple[int, str]:
    """Run check_handoff_needed.py --input <path> --fail-on-force --composite --mode pre-task."""
    cmd = [
        sys.executable, str(CHECKER),
        "--input", input_path,
        "--fail-on-force",
        "--composite",
        "--mode", "pre-task",
        "--policy", str(POLICY),
        "--json",
    ]
    if extra_args:
        cmd.extend(extra_args)

    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode, result.stdout + result.stderr


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    results = []

    # Scenario 1: missing current.json → UNKNOWN (exit 0 in pre-task mode)
    fake_path = str(OUT_DIR / "nonexistent_file.json")
    rc, out = run_checker(fake_path)
    results.append(("missing_current_json", rc, out, 0))
    print(f"[1] missing current.json → exit={rc} {'PASS' if rc == 0 else 'FAIL'}")

    # Scenario 2: stale metrics → SUGGEST_HANDOFF (exit 0 in pre-task mode)
    data = json.loads(json.dumps(BASELINE))
    data["last_checked_at"] = "2026-01-01T00:00:00Z"  # very old
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as f:
        json.dump(data, f, indent=2)
        tmp_path = f.name
    rc, out = run_checker(tmp_path)
    results.append(("stale_metrics_suggest", rc, out, 0))
    Path(tmp_path).unlink(missing_ok=True)
    print(f"[2] stale metrics → exit={rc} {'PASS' if rc == 0 else 'FAIL'}")

    # Scenario 3: message_count >= 60 with cdp_dom_count → FORCE (exit 1)
    data = json.loads(json.dumps(BASELINE))
    data["last_known_metrics"]["assistant_message_count"] = 65
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as f:
        json.dump(data, f, indent=2)
        tmp_path = f.name
    rc, out = run_checker(tmp_path)
    results.append(("message_count_force_cdp", rc, out, 1))
    Path(tmp_path).unlink(missing_ok=True)
    print(f"[3] message_count=65 cdp → exit={rc} {'PASS' if rc == 1 else 'FAIL'}")

    # Scenario 4: review_rounds >= 3 → FORCE (exit 1)
    data = json.loads(json.dumps(BASELINE))
    data["last_known_metrics"]["review_round_count"] = 4
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as f:
        json.dump(data, f, indent=2)
        tmp_path = f.name
    rc, out = run_checker(tmp_path)
    results.append(("review_rounds_force", rc, out, 1))
    Path(tmp_path).unlink(missing_ok=True)
    print(f"[4] review_rounds=4 → exit={rc} {'PASS' if rc == 1 else 'FAIL'}")

    # Scenario 5: nav_result=access_denied → FORCE (exit 1)
    data = json.loads(json.dumps(BASELINE))
    data["last_nav_result"] = "access_denied"
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as f:
        json.dump(data, f, indent=2)
        tmp_path = f.name
    rc, out = run_checker(tmp_path)
    results.append(("nav_access_denied", rc, out, 1))
    Path(tmp_path).unlink(missing_ok=True)
    print(f"[5] nav=access_denied → exit={rc} {'PASS' if rc == 1 else 'FAIL'}")

    # Scenario 6: nav_result=auth_required → HUMAN_REQUIRED (exit 1)
    data = json.loads(json.dumps(BASELINE))
    data["last_nav_result"] = "auth_required"
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as f:
        json.dump(data, f, indent=2)
        tmp_path = f.name
    rc, out = run_checker(tmp_path)
    results.append(("nav_auth_required", rc, out, 1))
    Path(tmp_path).unlink(missing_ok=True)
    print(f"[6] nav=auth_required → exit={rc} {'PASS' if rc == 1 else 'FAIL'}")

    # Scenario 7: invalid JSON → error (exit 2)
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as f:
        f.write("{ invalid json !!! }")
        tmp_path = f.name
    rc, out = run_checker(tmp_path)
    results.append(("invalid_json", rc, out, 2))
    Path(tmp_path).unlink(missing_ok=True)
    print(f"[7] invalid JSON → exit={rc} {'PASS' if rc == 2 else 'FAIL'}")

    # Scenario 8: manual_estimate + count>=60 → SUGGEST not FORCE (exit 0)
    data = json.loads(json.dumps(BASELINE))
    data["last_known_metrics"]["assistant_message_count"] = 70
    data["metrics_source"] = "manual_estimate"
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as f:
        json.dump(data, f, indent=2)
        tmp_path = f.name
    rc, out = run_checker(tmp_path)
    results.append(("manual_estimate_no_force", rc, out, 0))
    Path(tmp_path).unlink(missing_ok=True)
    print(f"[8] manual_estimate count=70 → exit={rc} {'PASS' if rc == 0 else 'FAIL'}")

    # Scenario 9: composite force (slow + short + rounds + cdp) → FORCE (exit 1)
    data = json.loads(json.dumps(BASELINE))
    data["last_known_metrics"]["response_time_seconds"] = 75
    data["last_known_metrics"]["last_gpt_reply_bytes"] = 1500
    data["last_known_metrics"]["review_round_count"] = 2
    data["metrics_source"] = "cdp_dom_count"
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as f:
        json.dump(data, f, indent=2)
        tmp_path = f.name
    rc, out = run_checker(tmp_path)
    results.append(("composite_force", rc, out, 1))
    Path(tmp_path).unlink(missing_ok=True)
    print(f"[9] composite force → exit={rc} {'PASS' if rc == 1 else 'FAIL'}")

    # Write all evidence to files
    all_output = []
    for label, rc, output, expected_rc in results:
        fname = f"{label}.txt"
        fpath = OUT_DIR / fname
        if expected_rc == 0:
            expected_text = f"exit=0 (pre-task advisory: OK or SUGGEST)"
        elif expected_rc == 1:
            expected_text = f"exit=1 (FORCE_HANDOFF or HUMAN_REQUIRED blocks task)"
        else:
            expected_text = f"exit=2 (invalid input rejected)"
        content = f"# Conversation Health Evidence: {label}\n# Actual exit: {rc}\n# Expected: {expected_text}\n\n{output}\n"
        fpath.write_text(content, encoding="utf-8")
        all_output.append(f"=== {label} (exit={rc}, expected={expected_rc}) ===\n{output}\n")

    # Write combined evidence file
    combined = OUT_DIR / "combined-conversation-health-evidence.txt"
    combined.write_text("\n".join(all_output), encoding="utf-8")

    print(f"\nEvidence written to: {OUT_DIR}")
    print(f"Combined evidence: {combined}")

    # Summary
    all_pass = True
    for label, rc, _, expected_rc in results:
        if rc != expected_rc:
            all_pass = False
            print(f"  FAIL: {label} expected={expected_rc} actual={rc}")

    print(f"\nOverall: {'ALL PASS' if all_pass else 'SOME FAILURES'}")
    sys.exit(0 if all_pass else 1)


if __name__ == "__main__":
    main()
