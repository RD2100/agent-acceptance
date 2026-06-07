#!/usr/bin/env python3
"""
test_impact_map.py — Map changed files to affected tests.

Usage: python scripts/test_impact_map.py [--changed <base>]
Recommends which tests to run based on git diff.
"""
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

# File pattern → recommended tests mapping
IMPACT_MAP = {
    "tools/ai_guard.py": ["tests/test_ai_guard_staged_scope.py", "tests/test_chain_evidence_hardening.py"],
    "scripts/review_queue.py": ["tests/test_review_queue.py"],
    "scripts/compress_project_context.py": ["tests/test_context_compression.py"],
    "scripts/build_boot_context.py": ["tests/test_boot_context_builder.py"],
    "scripts/validate_context_memory.py": ["tests/test_context_memory_privacy.py"],
    "contracts/": ["tests/test_*_schema.py", "tests/test_*_policy.py"],
    "schemas/": ["tests/test_*_schema.py", "tests/test_*_policy.py"],
    "memory/": ["tests/test_context_compression.py", "tests/test_boot_context_builder.py"],
    "policies/": ["tests/test_*_policy.py"],
    "tests/test_*.py": [],  # test files changed → recommend themselves
    ".ai/tasks/": [],
    "docs/": [],
    "demo/": [],
    "evidence_packs/": [],
}


def changed_files(base="HEAD"):
    r = subprocess.run(["git", "diff", "--name-only", base], capture_output=True, text=True, cwd=str(REPO))
    return [l.strip().replace("\\", "/") for l in r.stdout.splitlines() if l.strip()]


def recommend(files):
    tests = set()
    for f in files:
        matched = False
        for pattern, test_list in IMPACT_MAP.items():
            if f.startswith(pattern.replace("*", "")) or pattern.replace("*", "") in f:
                for t in test_list:
                    if t:
                        tests.add(t)
                matched = True
                break
        if not matched:
            if f.startswith("tests/"):
                tests.add(f)
            elif f.startswith("scripts/"):
                name = Path(f).stem
                glob = REPO.glob(f"tests/test_*{name}*.py")
                for g in glob:
                    tests.add(str(g.relative_to(REPO)))
            elif f.startswith("tools/"):
                name = Path(f).stem
                glob = REPO.glob(f"tests/test_*{name}*.py")
                for g in glob:
                    tests.add(str(g.relative_to(REPO)))
    if not tests:
        tests.add("tests/ (full suite — no specific test mapped)")
    return sorted(tests)


def main():
    base = "HEAD~1"
    if "--changed" in sys.argv:
        idx = sys.argv.index("--changed")
        base = sys.argv[idx + 1] if idx + 1 < len(sys.argv) else "HEAD~1"

    files = changed_files(base)
    tests = recommend(files)

    print(f"Changed files ({base}): {len(files)}")
    print(f"Recommended tests: {len(tests)}")
    for t in tests:
        print(f"  - {t}")

    if tests:
        print(f"\nRun: python -m pytest {' '.join(tests)} -v")


if __name__ == "__main__":
    main()
