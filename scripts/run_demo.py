#!/usr/bin/env python3
"""
run_demo.py — One-command synthetic paper demo runner.

Usage: python scripts/run_demo.py
Runs the full DevFrame synthetic paper workflow verification in one command.
No real paper content. No external API calls.
External runtime checks are presence-only preflights; they do not run sibling repos.
"""
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
STEPS = []


def step(name, cmd):
    print(f"\n{'='*60}\n>> {name}\n{'='*60}")
    r = subprocess.run(cmd, cwd=str(REPO), capture_output=False)
    STEPS.append({"name": name, "ok": r.returncode == 0})
    return r.returncode == 0


def external_runtime_presence_command(path: Path):
    code = (
        "from pathlib import Path; "
        f"cp=Path({str(path)!r}); "
        "print("
        "f'scope=presence_only executed=false "
        "human_gate_required_for_execution=true "
        "control_plane_exists={cp.is_dir()} tests_dir_exists={(cp / \"tests\").is_dir()}'"
        ")"
    )
    return [sys.executable, "-c", code]


def main():
    print("=" * 60)
    print("  DevFrame Synthetic Paper Demo — One-Command Runner")
    print("=" * 60)

    ok = True
    ok &= step("1. Full Test Suite", [sys.executable, "-m", "pytest", "tests/", "-q", "--tb=line"])
    ok &= step("2. AI Guard Staged Mode", [sys.executable, "tools/ai_guard.py", "staged"])
    ok &= step("3. AI Guard Task Mode", [sys.executable, "tools/ai_guard.py", "task", ".ai/current-task.yaml"])
    ok &= step("4. BOOT_CONTEXT Check", [sys.executable, "-c",
        "import sys; c=open('BOOT_CONTEXT.md',encoding='utf-8').read(); print(f'BOOT_CONTEXT: {len(c)} chars, sections={c.count(\"##\")}'); sys.exit(0 if len(c)>=2000 else 1)"])
    ok &= step("5. Memory Index Check", [sys.executable, "-c",
        "import sys; c=open('memory/index.md',encoding='utf-8').read(); print(f'memory/index: {len(c)} chars'); sys.exit(0 if len(c)>=500 else 1)"])
    ok &= step("6. Review Queue Status", [sys.executable, "scripts/review_queue.py", "status"])
    ok &= step(
        "7. External Runtime Presence Preflight",
        external_runtime_presence_command(Path("D:/devframe-control-plane")),
    )

    print(f"\n{'='*60}")
    print(f"  DEMO RESULT: {'ALL PASS' if ok else 'SOME FAILED'}")
    for s in STEPS:
        print(f"  [{'PASS' if s['ok'] else 'FAIL'}] {s['name']}")
    print(f"{'='*60}")

    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
