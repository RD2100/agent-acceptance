#!/usr/bin/env python3
"""
paper_pilot_preflight.py — Real-paper pilot preflight checker.

Verifies privacy guardrails are in place before any real-paper work.
Protocol-only check. No real paper content processed.
Fail-closed: any missing guard → BLOCKED.
"""
import hashlib
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent


def check_file(path, desc, min_size=10):
    """Verify a required file exists."""
    fp = REPO / path
    if not fp.exists():
        return False, f"MISSING: {desc} ({path})"
    if fp.stat().st_size < min_size:
        return False, f"EMPTY: {desc} ({path})"
    return True, f"OK: {desc}"


def check_string_in_file(path, search, desc):
    """Verify a string exists in a file."""
    fp = REPO / path
    if not fp.exists():
        return False, f"MISSING: {desc} ({path})"
    content = fp.read_text(encoding="utf-8")
    if search.lower() not in content.lower():
        return False, f"NOT FOUND: '{search}' in {desc} ({path})"
    return True, f"OK: {desc} contains '{search}'"


def main():
    checks = []
    ok = True

    # 1. Privacy guard script exists and operational
    c, m = check_file("scripts/validate_context_memory.py", "privacy guard script")
    checks.append(m); ok &= c

    # 2. Paper privacy knowledge exists
    c, m = check_file("memory/knowledge/paper_privacy.md", "paper privacy knowledge", 200)
    checks.append(m); ok &= c

    # 3. Paper validator exists
    c, m = check_file("scripts/validate_paper_task.py", "paper task validator")
    checks.append(m); ok &= c

    # 4. Safety boundaries documented
    c, m = check_string_in_file("BOOT_CONTEXT.md", "安全边界", "safety boundaries in BOOT_CONTEXT")
    checks.append(m); ok &= c

    # 5. PAPER-C1/C2 protocols exist
    c1, _ = check_file("evidence_packs/paper-c1-closure", "PAPER-C1 closure evidence", 1)
    c2, _ = check_file("evidence_packs/paper-c2-closure", "PAPER-C2 closure evidence", 1)
    c = c1 and c2
    checks.append(f"{'OK' if c else 'MISSING'}: PAPER-C1/C2 protocol evidence")
    ok &= c

    # 6. AI guard operational (has BLOCKED + exit(1))
    content = (REPO / "tools/ai_guard.py").read_text(encoding="utf-8")
    c = "sys.exit(1)" in content and "BLOCKED" in content
    checks.append(f"{'OK' if c else 'FAIL'}: ai_guard fail-closed mechanism")
    checks.append(m); ok &= c

    # 7. No real paper content in memory (spot-check)
    memory_files = list(REPO.glob("memory/**/*.md"))
    paper_leak = False
    for mf in memory_files:
        content = mf.read_text(encoding="utf-8")
        if "real_paper_full_text" in content.lower() and "安全" not in content:
            paper_leak = True
            break
    checks.append(f"{'FAIL' if paper_leak else 'OK'}: memory free of real paper content")
    ok &= not paper_leak

    print("\n".join(checks))
    print(f"\nPREFLIGHT: {'PASS' if ok else 'BLOCKED'}")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
