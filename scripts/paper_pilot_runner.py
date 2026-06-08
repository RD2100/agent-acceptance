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

    # Run: Full synthetic validation pipeline
    print("\n[RUN] Synthetic paper validation pipeline...")
    ok = True

    # 1. Build synthetic test fixtures
    import tempfile, os, shutil
    tmp = tempfile.mkdtemp(prefix="paper_pilot_")
    try:
        paper_dir = Path(tmp) / "PAPER_TASK_INPUT"
        paper_dir.mkdir()
        (paper_dir / "PAPER_TASK.yaml").write_text("task_id: SYNTHETIC-PILOT\ntitle: Synthetic Paper Validation\n", encoding="utf-8")
        (paper_dir / "PAPER_TASK_INPUT.yaml").write_text("input_type: synthetic\nsource: test_fixture\n", encoding="utf-8")
        (paper_dir / "PAPER_TASK_OUTPUT.yaml").write_text("status: completed\nverdict: accepted\nsynthetic_only: true\n", encoding="utf-8")
        (paper_dir / "PRIVACY_ATTESTATION.yaml").write_text("synthetic_only: true\nno_real_data: true\n", encoding="utf-8")
        (paper_dir / "REDACTION_REPORT.yaml").write_text("redacted: none\nreason: synthetic_only\n", encoding="utf-8")

        # 2. Run validator on synthetic input — must PASS (exit 0)
        r = subprocess.run([sys.executable, "scripts/validate_paper_task.py", tmp], capture_output=True, text=True, cwd=str(REPO), timeout=30)
        validator_pass = r.returncode == 0
        ok &= validator_pass
        print(f"\n>> 1. Paper validator on synthetic input")
        print(f"   Exit: {r.returncode}, {'PASS' if validator_pass else 'FAIL'}: {(r.stdout or '')[:200]}")
        if not validator_pass:
            print("   BLOCKED: Validator failed. Pilot cannot proceed.")

        # 3. ai_guard audit
        ok &= step("2. ai_guard audit", [sys.executable, "tools/ai_guard.py", "audit"], 60)

        # 4. Privacy guard on output
        ok &= step("3. Privacy guard validation",
            [sys.executable, "-c",
             "from scripts.validate_context_memory import check_privacy; r=check_privacy('Synthetic paper test. No real data.','test'); assert r['pass']"], 10)

        # 5. Check paper privacy guardrail
        ok &= step("4. Paper privacy guardrail",
            [sys.executable, "-c",
             "from pathlib import Path; c=Path('memory/knowledge/paper_privacy.md').read_text(encoding='utf-8'); assert '禁止' in c; print('Guardrail operational')"], 10)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    print(f"\n{'='*50}")
    print(f"  PILOT RESULT: {'PASS' if ok else 'FAIL'}")
    print(f"{'='*50}")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
