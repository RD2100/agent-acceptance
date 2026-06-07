#!/usr/bin/env python3
"""
ci_matrix.py — CI matrix runner driven by test impact mapping.

Usage: python scripts/ci_matrix.py [--base HEAD~1] [--mode full|impact|quick]
Runs the appropriate test suite based on changed files.
"""
import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))
from test_impact_map import changed_files, recommend


def run_tests(test_list, timeout=300):
    start = time.time()
    cmd = [sys.executable, "-m", "pytest", "-q", "--tb=line", "--json-report"]
    for t in test_list:
        cmd.append(str(REPO / t) if not t.startswith("tests/") else str(REPO / t))
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=str(REPO), timeout=timeout)
    elapsed = time.time() - start
    return {
        "exit_code": r.returncode,
        "elapsed_sec": round(elapsed, 1),
        "stdout_tail": r.stdout.strip().split("\n")[-2:] if r.stdout else [str(r.stderr)[:200]],
    }


def main():
    base = "HEAD~1"
    mode = "impact"

    for i, arg in enumerate(sys.argv[1:], 1):
        if arg == "--base" and i < len(sys.argv) - 1:
            base = sys.argv[i + 1]
        if arg == "--mode" and i < len(sys.argv) - 1:
            mode = sys.argv[i + 1]

    files = changed_files(base)
    recommended = recommend(files)
    full = "tests/ (full suite)" in recommended

    if mode == "quick" or full:
        test_list = ["tests/"]
    elif mode == "full":
        test_list = ["tests/"]
    else:
        test_list = [t for t in recommended if t.startswith("tests/") and "*" not in t]
        if not test_list:
            test_list = ["tests/"]

    print(f"CI-MATRIX [{mode}] base={base}")
    print(f"  Changed files: {len(files)}")
    print(f"  Running: {test_list}")

    result = run_tests(test_list)
    result["mode"] = mode
    result["base"] = base
    result["changed_count"] = len(files)
    result["timestamp"] = datetime.now(timezone.utc).isoformat()

    print(json.dumps(result, indent=2, ensure_ascii=False))
    sys.exit(result["exit_code"])


if __name__ == "__main__":
    main()
