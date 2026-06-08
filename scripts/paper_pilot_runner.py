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
        # Validator expects the 4 required files directly in the source directory, each with full schema
        import yaml
        privacy_fields = {
            "task_id": "SYNTHETIC-PILOT",
            "contains_real_paper_full_text": False,
            "contains_user_private_text": False,
            "contains_raw_transcript": False,
            "contains_memory_write": False,
            "contains_external_upload": False,
            "redaction_applied": True,
            "manual_review_required": False,
            "memory_write_policy": "redacted_workflow_lesson_only",
        }
        redaction_fields = {
            "task_id": "SYNTHETIC-PILOT",
            "redaction_applied": True,
            "contains_real_paper_full_text": False,
            "contains_user_private_text": False,
            "contains_raw_transcript": False,
            "manual_review_required": False,
        }
        (Path(tmp) / "PAPER_TASK_INPUT.yaml").write_text(yaml.dump({
            "task_id": "SYNTHETIC-PILOT",
            "task_type": "cssci_review",
            "paper_data_classification": "synthetic",
            "user_authorization": "synthetic",
            "input_materials": ["synthetic_test_data.md"],
            "privacy_constraints": ["no_real_paper"],
            "memory_policy": "redacted_workflow_lesson_only",
            "expected_outputs": ["report"]
        }), encoding="utf-8")
        (Path(tmp) / "PAPER_TASK_OUTPUT.yaml").write_text(yaml.dump({
            "task_id": "SYNTHETIC-PILOT",
            "task_type": "cssci_review",
            "output_summary": "Synthetic validation passed.",
            "findings": [{"severity": "info", "description": "Synthetic-only test"}],
            "evidence_basis": "synthetic_test_fixtures",
            "privacy_redaction_status": "full",
            "manual_review_required": False,
            "limitations": ["synthetic_data_only"],
            "contains_real_paper_full_text": False,
            "contains_unredacted_excerpt": False,
            "contains_user_identity": False
        }), encoding="utf-8")
        (Path(tmp) / "PRIVACY_ATTESTATION.yaml").write_text(yaml.dump(privacy_fields), encoding="utf-8")
        (Path(tmp) / "REDACTION_REPORT.yaml").write_text(yaml.dump(redaction_fields), encoding="utf-8")

        # 2. Run validator on synthetic input — MUST exit 0 for PILOT PASS
        r = subprocess.run([sys.executable, "scripts/validate_paper_task.py", tmp], capture_output=True, text=True, cwd=str(REPO), timeout=30)
        validator_pass = r.returncode == 0
        ok &= validator_pass
        print(f"\n>> 1. Paper validator on synthetic input")
        print(f"   Exit: {r.returncode}, {'PASS' if validator_pass else 'FAIL'}")
        if not validator_pass:
            print(f"   Validator output: {(r.stdout or '')[:300]}")
            print("   BLOCKED: Validator must pass for PILOT PASS.")

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

    # 5. Auth gate check (expected: CLOSED)
    print("\n[GATE 3] Authorization gate check (expected: CLOSED)...")
    import paper_auth_gate
    auth = paper_auth_gate.check()
    print(f"  Auth: {'CLOSED' if not auth['authorized'] else 'OPEN'} ({auth['reason']})")
    ok &= not auth['authorized']  # Must be CLOSED by default

    # 6. GO/NOGO check (expected: NOGO)
    print("\n[GATE 4] GO/NOGO decision...")
    import paper_go_nogo
    go = paper_go_nogo.check()
    print(f"  GO/NOGO: {'GO' if go['go'] else 'NOGO'} (auth={go['checks']['auth']['authorized']})")
    ok &= not go['go']  # Must be NOGO by default

    print(f"\n{'='*50}")
    if ok:
        print(f"  PILOT RESULT: PASS (gates operational, validator correctly validates)")
    else:
        print(f"  PILOT RESULT: FAIL (gates malfunction)")
    print(f"{'='*50}")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
