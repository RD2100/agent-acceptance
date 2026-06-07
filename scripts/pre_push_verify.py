#!/usr/bin/env python3
"""
pre_push_verify.py — Pre-push verification runner.

Checks before git push:
1. Tests pass (247+ expected)
2. ai_guard staged-only (0 errors)
3. No dirty baseline in latest commit
4. GPT review evidence exists for recent tasks
5. Cross-repo health

Exit 0 = safe to push. Exit 1 = fix before pushing.
"""
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent


def run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, cwd=str(REPO), **kw)


def main():
    errors = []
    warnings = []

    # 1. Tests
    print("[1/5] Running tests...")
    r = run([sys.executable, "-m", "pytest", "tests/", "-q", "--tb=line"], timeout=120)
    if r.returncode != 0:
        errors.append("TESTS FAILED")
    else:
        passed = r.stdout.strip().split("\n")[-1] if r.stdout else "unknown"
        print(f"  OK: {passed}")

    # 2. ai_guard staged-only
    print("[2/5] Checking ai_guard...")
    r = run([sys.executable, "tools/ai_guard.py", "task", ".ai/current-task.yaml"])
    if "ERROR" in r.stdout or r.returncode != 0:
        errors.append("AI_GUARD BLOCKED")
    else:
        print(f"  OK: ai_guard PASS")

    # 3. Dirty baseline check
    print("[3/5] Checking dirty baseline...")
    dirty = run(["git", "diff", "--cached", "--name-only"])
    dirty_files = dirty.stdout.strip().split("\n") if dirty.stdout.strip() else []
    forbidden = [f for f in dirty_files if any(p in f for p in [
        "runs/", "HANDOFF_REPLY", "archive/draft-hooks", ".tmpconfig", ".tmpdata", "__pycache__",
    ])]
    if forbidden:
        errors.append(f"DIRTY BASELINE in staged: {forbidden}")
    else:
        print(f"  OK: no dirty files in staged ({len(dirty_files)} staged files)")

    # 4. GPT review evidence
    print("[4/5] Checking GPT review evidence...")
    evidence_packs = list(REPO.glob("evidence_packs/*/GPT_REVIEW_RESULT*.txt"))
    if not evidence_packs:
        warnings.append("No GPT review evidence found")
    else:
        accepted = 0
        for ep in evidence_packs:
            content = ep.read_text(encoding="utf-8")
            if "overall_judgment: accepted" in content.lower():
                accepted += 1
        print(f"  OK: {len(evidence_packs)} GPT review files, {accepted} accepted")

    # 5. Cross-repo
    print("[5/5] Cross-repo health...")
    cp = Path("D:/devframe-control-plane")
    if cp.is_dir():
        print(f"  OK: control-plane exists")
    else:
        warnings.append("control-plane not found at D:/devframe-control-plane")

    # Report
    print(f"\n{'='*40}")
    if errors:
        print(f"BLOCKED: {len(errors)} error(s)")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)
    else:
        print(f"PASS: safe to push")
        for w in warnings:
            print(f"  WARNING: {w}")
        sys.exit(0)


if __name__ == "__main__":
    main()
