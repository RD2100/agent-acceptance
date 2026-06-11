"""Runtime negative-path evidence for hook failure semantics (v2.3.0).

Generates synthetic latest.json files with failure scenarios and validates
them against the validator. Proves (9 scenarios):
1. sadp_audit failure → BLOCKED → validator PASS (correct semantics)
2. ai_guard failure → BLOCKED → validator PASS (correct semantics)
3. test_governance failure → PASS advisory → validator PASS (advisory, not blocking)
4. ai_guard failure + result=PASS → REJECTED (validator exit nonzero)
5. PASS_WITH_WARNINGS → REJECTED (forbidden in v2.3.0)
6. Invalid JSON → REJECTED (validator exit nonzero)
7. Missing sadp-audit stage → REJECTED (fail-closed: absence = BLOCKED)
8. Null exit_code + PASS → REJECTED (fail-closed: null = expected BLOCKED)
9. Missing ai-guard stage → REJECTED (fail-closed: absence = BLOCKED)

This script generates evidence files for the evidence pack.
"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent  # scripts/ → project root

VALIDATOR = PROJECT_ROOT / "scripts" / "validate_hook_output.py"
SCHEMA = PROJECT_ROOT / "schemas" / "agent-runtime" / "evidence-capture.schema.json"
OUT_DIR = PROJECT_ROOT / "_evidence" / "runtime-negative-path-evidence"

BASELINE = {
    "timestamp": "2026-06-11T12:00:00Z",
    "hook_version": "2.3.0",
    "stages": [
        {"name": "manifest-regen", "exit_code": 0, "output_file": None, "duration_ms": 100},
        {"name": "sadp-audit", "exit_code": 0, "output_file": "sadp-audit.txt", "duration_ms": 500},
        {"name": "ai-guard", "exit_code": 0, "output_file": "ai-guard.txt", "duration_ms": 200},
        {"name": "test-governance", "exit_code": 0, "output_file": "test-governance.txt", "duration_ms": 300},
    ],
    "git_context": {"branch": "master", "commit_count": 224, "staged_file_count": 9},
    "overall_result": "PASS",
}


def run_validator(json_data: dict, label: str) -> tuple[int, str]:
    """Write synthetic latest.json to temp file and run validator."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as f:
        json.dump(json_data, f, indent=2)
        tmp_path = f.name

    result = subprocess.run(
        [sys.executable, str(VALIDATOR), "--file", tmp_path, "--schema", str(SCHEMA)],
        capture_output=True, text=True
    )
    Path(tmp_path).unlink(missing_ok=True)
    return result.returncode, result.stdout + result.stderr


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    results = []

    # Test 1: sadp_audit failure → BLOCKED → validator should PASS (correct semantics)
    data = json.loads(json.dumps(BASELINE))
    data["stages"][1]["exit_code"] = 1
    data["overall_result"] = "BLOCKED"
    rc, out = run_validator(data, "sadp_audit_failure_blocked")
    results.append(("sadp_audit_failure_blocks", rc, out))
    print(f"[1] sadp_audit failure → BLOCKED: exit={rc} {'PASS' if rc == 0 else 'FAIL'}")

    # Test 2: ai_guard failure → BLOCKED → validator should PASS
    data = json.loads(json.dumps(BASELINE))
    data["stages"][2]["exit_code"] = 1
    data["overall_result"] = "BLOCKED"
    rc, out = run_validator(data, "ai_guard_failure_blocked")
    results.append(("ai_guard_failure_blocks", rc, out))
    print(f"[2] ai_guard failure → BLOCKED: exit={rc} {'PASS' if rc == 0 else 'FAIL'}")

    # Test 3: test_governance failure → advisory → validator should PASS (advisory, not blocking)
    data = json.loads(json.dumps(BASELINE))
    data["stages"][3]["exit_code"] = 1
    data["overall_result"] = "PASS"
    rc, out = run_validator(data, "test_governance_failure_advisory")
    results.append(("test_governance_failure_advisory", rc, out))
    print(f"[3] test_governance failure → PASS (advisory): exit={rc} {'PASS' if rc == 0 else 'FAIL'}")

    # Test 4: ai_guard failure but overall_result=PASS → validator should FAIL (exit nonzero)
    data = json.loads(json.dumps(BASELINE))
    data["stages"][2]["exit_code"] = 1
    data["overall_result"] = "PASS"
    rc, out = run_validator(data, "ai_guard_failure_mismatch")
    results.append(("ai_guard_failure_mismatch_rejected", rc, out))
    print(f"[4] ai_guard failure + result=PASS → REJECTED: exit={rc} {'PASS' if rc != 0 else 'FAIL'}")

    # Test 5: PASS_WITH_WARNINGS → validator should FAIL (forbidden in v2.3.0)
    data = json.loads(json.dumps(BASELINE))
    data["overall_result"] = "PASS_WITH_WARNINGS"
    rc, out = run_validator(data, "pass_with_warnings_forbidden")
    results.append(("pass_with_warnings_forbidden", rc, out))
    print(f"[5] PASS_WITH_WARNINGS → REJECTED: exit={rc} {'PASS' if rc != 0 else 'FAIL'}")

    # Test 6: invalid JSON → validator should FAIL
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as f:
        f.write("{ invalid json }")
        tmp_path = f.name
    result = subprocess.run(
        [sys.executable, str(VALIDATOR), "--file", tmp_path, "--schema", str(SCHEMA)],
        capture_output=True, text=True
    )
    Path(tmp_path).unlink(missing_ok=True)
    results.append(("invalid_json_rejected", result.returncode, result.stdout + result.stderr))
    print(f"[6] Invalid JSON → REJECTED: exit={result.returncode} {'PASS' if result.returncode != 0 else 'FAIL'}")

    # Test 7: missing blocking stage (sadp-audit) → validator should FAIL (fail-closed)
    data = json.loads(json.dumps(BASELINE))
    data["stages"] = [s for s in data["stages"] if s["name"] != "sadp-audit"]
    rc, out = run_validator(data, "missing_sadp_audit_rejected")
    results.append(("missing_sadp_audit_rejected", rc, out))
    print(f"[7] Missing sadp-audit → REJECTED: exit={rc} {'PASS' if rc != 0 else 'FAIL'}")

    # Test 8: null exit_code on blocking stage → validator should FAIL (fail-closed)
    data = json.loads(json.dumps(BASELINE))
    data["stages"][2]["exit_code"] = None  # ai-guard
    data["overall_result"] = "PASS"
    rc, out = run_validator(data, "null_exit_code_rejected")
    results.append(("null_exit_code_rejected", rc, out))
    print(f"[8] Null exit_code + PASS → REJECTED: exit={rc} {'PASS' if rc != 0 else 'FAIL'}")

    # Test 9: missing blocking stage (ai-guard) → validator should FAIL (fail-closed)
    data = json.loads(json.dumps(BASELINE))
    data["stages"] = [s for s in data["stages"] if s["name"] != "ai-guard"]
    rc, out = run_validator(data, "missing_ai_guard_rejected")
    results.append(("missing_ai_guard_rejected", rc, out))
    print(f"[9] Missing ai-guard → REJECTED: exit={rc} {'PASS' if rc != 0 else 'FAIL'}")

    # Write all evidence to files
    all_output = []
    for label, rc, output in results:
        fname = f"{label}.txt"
        fpath = OUT_DIR / fname
        # Determine expected label based on scenario type
        if "blocks" in label:
            expected_text = "0 (correct semantics — blocking stage failure → BLOCKED)"
        elif "advisory" in label:
            expected_text = "0 (advisory semantics — failure logged but not blocking)"
        else:
            expected_text = "nonzero (mismatch/invalid input rejected by validator)"
        content = f"# Runtime Negative-Path Evidence: {label}\n# Validator exit code: {rc}\n# Expected: {expected_text}\n\n{output}\n"
        fpath.write_text(content, encoding="utf-8")
        all_output.append(f"=== {label} (exit={rc}) ===\n{output}\n")

    # Write combined evidence file
    combined = OUT_DIR / "combined-runtime-evidence.txt"
    combined.write_text("\n".join(all_output), encoding="utf-8")

    print(f"\nEvidence written to: {OUT_DIR}")
    print(f"Combined evidence: {combined}")

    # Summary
    all_pass = True
    for label, rc, _ in results:
        if "blocks" in label and rc != 0:
            all_pass = False
        if "advisory" in label and rc != 0:
            all_pass = False
        if "rejected" in label and rc == 0:
            all_pass = False
        if "forbidden" in label and rc == 0:
            all_pass = False

    print(f"\nOverall: {'ALL PASS' if all_pass else 'SOME FAILURES'}")
    sys.exit(0 if all_pass else 1)


if __name__ == "__main__":
    main()
