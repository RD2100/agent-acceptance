#!/usr/bin/env python3
"""
smoke_suite.py — One-command health check for DevFrame agent-acceptance.

Verifies: tests, ai_guard, BOOT_CONTEXT, memory/index, review_queue, demo artifacts.
Outputs JSON result. Exit 0 = all pass.
"""
import json
import subprocess
import sys
import hashlib
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
RESULTS = []


def check(name: str, cmd: list, expect_pass: bool = True) -> dict:
    """Run a check command, return result dict."""
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, cwd=str(REPO), timeout=120)
        passed = (r.returncode == 0) == expect_pass
        return {
            "name": name,
            "passed": passed,
            "exit_code": r.returncode,
            "output_tail": r.stdout.strip().split("\n")[-1] if r.stdout else str(r.stderr)[:200],
        }
    except Exception as e:
        return {"name": name, "passed": False, "exit_code": -1, "output_tail": str(e)[:200]}


def file_check(name: str, path: str, min_size: int = 10) -> dict:
    """Check a file exists and has minimum size."""
    fp = REPO / path
    if fp.exists() and fp.stat().st_size >= min_size:
        return {"name": name, "passed": True, "size": fp.stat().st_size}
    return {"name": name, "passed": False, "size": fp.stat().st_size if fp.exists() else 0}


def main():
    # 1. Full test suite
    RESULTS.append(check("full_tests", [sys.executable, "-m", "pytest", "tests/", "-q", "--tb=line"]))

    # 2. ai_guard staged mode
    RESULTS.append(check("ai_guard_staged", [sys.executable, "tools/ai_guard.py", "staged"]))

    # 3. ai_guard task mode (should PASS — no dirty files in staged)
    RESULTS.append(check("ai_guard_task", [sys.executable, "tools/ai_guard.py", "task", ".ai/current-task.yaml"]))

    # 4. BOOT_CONTEXT readability
    RESULTS.append(file_check("BOOT_CONTEXT", "BOOT_CONTEXT.md", 2000))

    # 5. memory/index readability
    RESULTS.append(file_check("memory_index", "memory/index.md", 500))

    # 6. Review queue status
    try:
        r = subprocess.run([sys.executable, "scripts/review_queue.py", "status"], capture_output=True, text=True, cwd=str(REPO))
        q = json.loads(r.stdout)
        RESULTS.append({"name": "review_queue", "passed": isinstance(q, dict) and "total" in q, "total": q.get("total", 0)})
    except Exception:
        RESULTS.append({"name": "review_queue", "passed": False})

    # 7. Demo artifacts
    RESULTS.append(file_check("demo_readme", "demo/README.md", 100))
    RESULTS.append(file_check("demo_guide", "demo/USER_GUIDE.md", 100))

    # 8. Cross-repo (lightweight — just check control-plane exists)
    cp_tests = Path("D:/devframe-control-plane/tests")
    RESULTS.append({"name": "control_plane_tests_dir", "passed": cp_tests.is_dir()})

    # Compile report
    passed = sum(1 for r in RESULTS if r["passed"])
    failed = len(RESULTS) - passed
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "overall": "PASS" if failed == 0 else "FAIL",
        "passed": passed,
        "failed": failed,
        "total": len(RESULTS),
        "checks": RESULTS,
    }

    print(json.dumps(report, indent=2, ensure_ascii=False))
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
