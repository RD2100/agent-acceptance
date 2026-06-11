#!/usr/bin/env python3
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

TEST_COUNT_RE = re.compile(r"(\d+)\s*(?:tests?\s+)?PASS|测试\s+(\d+)\s+PASS", re.I)
DATE_RE = re.compile(r"(20\d{2}-\d{2}-\d{2})(?:T([0-9:.+-]+))?")


def _read(path: Path):
    return path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""


def _test_counts(text):
    counts = []
    for match in TEST_COUNT_RE.finditer(text):
        counts.append(int(next(g for g in match.groups() if g)))
    return counts


def _first_date(text):
    m = DATE_RE.search(text)
    if not m:
        return None
    return m.group(0)


def _source_contains(root: Path, needle: str):
    for rel in ["BOOT_CONTEXT.md", "memory/index.md", "PROJECT_HISTORY.md", "PROJECT_HISTORY_FINAL.md"]:
        if needle in _read(root / rel):
            return True
    return False


def _git_head_date(root: Path):
    try:
        r = subprocess.run(["git", "log", "-1", "--format=%cI"], cwd=str(root), capture_output=True, text=True, timeout=10)
        if r.returncode == 0:
            return r.stdout.strip()
    except Exception:
        pass
    return None


def run_stale_check(repo_root, conversational_claims=None, head_date=None):
    root = Path(repo_root)
    conversational_claims = conversational_claims or []
    findings = []

    boot = _read(root / "BOOT_CONTEXT.md")
    memory_index = _read(root / "memory/index.md")
    history = _read(root / "PROJECT_HISTORY.md")
    paper_privacy = _read(root / "memory/knowledge/paper_privacy.md")

    boot_counts = _test_counts(boot)
    if len(set(boot_counts)) > 1:
        findings.append({
            "id": "BOOT_CONTEXT_TEST_COUNT_CONFLICT",
            "severity": "HIGH",
            "message": f"BOOT_CONTEXT.md contains conflicting test counts: {sorted(set(boot_counts))}",
            "stale_reference": True,
        })

    all_counts = _test_counts(boot) + _test_counts(memory_index) + _test_counts(history)
    # Targeted handoff tests are useful evidence for this task, but they do not
    # verify historical total-suite claims such as 232/247/296 PASS.
    fresh_outputs = [root / "TEST_OUTPUT.txt", root / "FULL_TEST_OUTPUT.txt"]
    has_fresh_p0 = any(p.exists() for p in fresh_outputs)
    if all_counts and not has_fresh_p0:
        findings.append({
            "id": "TEST_COUNT_WITHOUT_FRESH_P0",
            "severity": "MEDIUM",
            "message": "Test count claims exist in handoff/memory/history but no fresh P0 test output was found.",
            "stale_reference": True,
        })

    frozen = "freeze" in paper_privacy.lower() or "frozen" in paper_privacy.lower() or "论文处理被 freeze" in paper_privacy
    repo_active = (root / "_reports/PAPER_PROJECT_INDEX.json").exists() or (root / "evidence_packs/paper-c3-dry-run").exists()
    if frozen and repo_active:
        findings.append({
            "id": "MEMORY_FROZEN_REPO_ACTIVE",
            "severity": "MEDIUM",
            "message": "Memory describes paper workflow as frozen, while repo has active paper index/evidence. Treat memory as stale reference.",
            "stale_reference": True,
        })

    head_date = head_date or _git_head_date(root)
    boot_date = _first_date(boot)
    if boot_date and head_date and boot_date[:10] < head_date[:10]:
        findings.append({
            "id": "BOOT_CONTEXT_BEHIND_HEAD",
            "severity": "MEDIUM",
            "message": f"BOOT_CONTEXT date {boot_date} appears older than git HEAD date {head_date}.",
            "stale_reference": True,
        })

    for claim in conversational_claims:
        if claim and not _source_contains(root, claim):
            findings.append({
                "id": "UNVERIFIED_CONVERSATIONAL_CLAIM",
                "severity": "INFO",
                "message": f"'{claim}' is an unverified conversational claim; no local source-of-truth text matched it.",
                "stale_reference": True,
            })

    return {
        "task_id": "HANDOFF-PIPELINE-REFACTOR-A1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "repo_root": str(root),
        "findings": findings,
        "summary": {"finding_count": len(findings), "has_high": any(f["severity"] == "HIGH" for f in findings)},
    }


def write_markdown(result, output_path):
    lines = ["# Handoff Stale Check", "", f"- generated_at: {result['generated_at']}", f"- findings: {len(result['findings'])}", "", "## Findings"]
    if not result["findings"]:
        lines.append("- none")
    for item in result["findings"]:
        lines.append(f"- **{item['id']}** ({item['severity']}): {item['message']}")
    Path(output_path).write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent
    result = run_stale_check(root, conversational_claims=["296 PASS"])
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
