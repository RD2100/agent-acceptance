import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from handoff_stale_check import run_stale_check


def write(path: Path, text: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_detects_boot_context_internal_test_count_conflict(tmp_path):
    write(tmp_path / "BOOT_CONTEXT.md", "agent-acceptance 测试 232 PASS\n247 tests PASS\n")
    write(tmp_path / "memory/index.md", "247 tests PASS\n")
    write(tmp_path / "PROJECT_HISTORY.md", "tests: 247 PASS\n")

    result = run_stale_check(tmp_path, conversational_claims=[])

    ids = {item["id"] for item in result["findings"]}
    assert "BOOT_CONTEXT_TEST_COUNT_CONFLICT" in ids


def test_flags_memory_and_boot_counts_without_fresh_p0_output(tmp_path):
    write(tmp_path / "BOOT_CONTEXT.md", "247 tests PASS\n")
    write(tmp_path / "memory/index.md", "247 tests PASS\n")
    write(tmp_path / "PROJECT_HISTORY.md", "tests: 247 PASS\n")

    result = run_stale_check(tmp_path, conversational_claims=[])

    ids = {item["id"] for item in result["findings"]}
    assert "TEST_COUNT_WITHOUT_FRESH_P0" in ids


def test_detects_memory_frozen_vs_repo_active(tmp_path):
    write(tmp_path / "memory/knowledge/paper_privacy.md", "论文处理被 freeze。不进行 PAPER-C3。\n")
    write(tmp_path / "_reports/PAPER_PROJECT_INDEX.json", '{"overall_status":"in_progress","modules":[]}')
    (tmp_path / "evidence_packs/paper-c3-dry-run").mkdir(parents=True)

    result = run_stale_check(tmp_path, conversational_claims=[])

    ids = {item["id"] for item in result["findings"]}
    assert "MEMORY_FROZEN_REPO_ACTIVE" in ids


def test_detects_unverified_conversational_claim(tmp_path):
    write(tmp_path / "BOOT_CONTEXT.md", "247 tests PASS\n")
    write(tmp_path / "memory/index.md", "247 tests PASS\n")
    write(tmp_path / "PROJECT_HISTORY.md", "tests: 247 PASS\n")

    result = run_stale_check(tmp_path, conversational_claims=["296 PASS"])

    ids = {item["id"] for item in result["findings"]}
    assert "UNVERIFIED_CONVERSATIONAL_CLAIM" in ids
    assert "unverified conversational claim" in result["findings"][-1]["message"]


def test_detects_boot_context_older_than_head(tmp_path):
    write(tmp_path / "BOOT_CONTEXT.md", "> 生成时间: 2026-06-07\n")

    result = run_stale_check(tmp_path, conversational_claims=[], head_date="2026-06-08T12:00:00+00:00")

    ids = {item["id"] for item in result["findings"]}
    assert "BOOT_CONTEXT_BEHIND_HEAD" in ids
