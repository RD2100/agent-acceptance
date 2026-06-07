#!/usr/bin/env python3
"""
paper_pilot_runner.py — Bounded paper pilot runner, gated by preflight.

Runs synthetic paper validation demo ONLY after preflight passes.
No real paper content. Synthetic fixtures only. Fail-closed.
"""
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SYNTHETIC_FIXTURES = {
    "title": "[SYNTHETIC] Test Paper",
    "abstract": "This is a synthetic test paper for DevFrame pipeline validation.",
    "content": "Synthetic content for testing. Not real research.",
}


def step(name, cmd, timeout=120):
    print(f"\n>> {name}")
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=str(REPO), timeout=timeout)
    print(r.stdout[-500:] if r.stdout else str(r.stderr)[:200])
    return r.returncode == 0


def main():
    print("=" * 50)
    print("  PAPER-C3 Bounded Pilot Runner")
    print("  Synthetic-only. No real paper content.")
    print("=" * 50)

    # Gate 1: Preflight must pass
    print("\n[GATE 1] Preflight check...")
    r = subprocess.run([sys.executable, "scripts/paper_pilot_preflight.py"], cwd=str(REPO), capture_output=True, text=True)
    if r.returncode != 0:
        print("BLOCKED: Preflight failed. Pilot aborted.")
        print(r.stdout)
        sys.exit(1)
    print("PASS: Preflight OK")

    # Gate 2: Privacy guard validates synthetic fixtures
    print("\n[GATE 2] Privacy guard on synthetic fixtures...")
    from validate_context_memory import check_privacy
    result = check_privacy(str(SYNTHETIC_FIXTURES), "synthetic_fixture.py")
    if not result["pass"]:
        print(f"BLOCKED: Synthetic fixture failed privacy guard: {result['issues']}")
        sys.exit(1)
    print("PASS: Synthetic fixtures are privacy-safe")

    # Run: Synthetic paper validation
    print("\n[RUN] Synthetic paper validation...")
    ok = True
    ok &= step("1. Paper validator import", [sys.executable, "-c",
        "from scripts.validate_paper_task import main; print('Validator importable')"], 10)
    ok &= step("2. ai_guard audit", [sys.executable, "tools/ai_guard.py", "audit"], 60)
    ok &= step("3. Paper privacy knowledge",
        [sys.executable, "-c",
         "from pathlib import Path; c=Path('memory/knowledge/paper_privacy.md').read_text(encoding='utf-8'); print('Paper privacy doc:', len(c), 'chars'); assert '禁止' in c"], 10)
    ok &= step("4. Synthetic fixture privacy",
        [sys.executable, "-c",
         "from scripts.validate_context_memory import check_privacy; r=check_privacy('Synthetic test paper about AI. No real data.','test'); assert r['pass'], f'Failed: {r}'"], 10)

    print(f"\n{'='*50}")
    print(f"  PILOT RESULT: {'PASS' if ok else 'FAIL'}")
    print(f"{'='*50}")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
