#!/usr/bin/env python3
"""test_validate_run_id_consistency.py — Tests for validate_run_id_consistency.py.

Covers all AWSP v1.0.0 requirements:
- run_id.txt existence
- R1_RUN_ID.txt match
- Evidence pack zip existence and filename match
- {{RUN_ID}} template variable required
- {{TASK_ID}} template variable required
- PACK_MANIFEST.md run_id match
- GPT reply run_id match
"""

import json
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))

from validate_run_id_consistency import validate_run_id_consistency


def _setup_full_consistent(tmp_path, run_id="TEST_TASK_A1_20260609T120000_RD"):
    """Helper: create a fully consistent set of artifacts."""
    report_dir = tmp_path / "test-task-a1"
    report_dir.mkdir()

    (report_dir / "run_id.txt").write_text(run_id, encoding="utf-8")
    (report_dir / "R1_RUN_ID.txt").write_text(run_id, encoding="utf-8")
    (report_dir / "GPT_REVIEW_PROMPT.md").write_text(
        "## Review " + "{{TASK_ID}}" + "\nrun_id: " + "{{RUN_ID}}"
        + "\noverall_judgment: accepted\n---END_OF_GPT_RESPONSE---\n",
        encoding="utf-8",
    )

    # Create evidence pack dir and zip
    pack_dir = tmp_path / "evidence_packs" / "test-task-a1"
    pack_dir.mkdir(parents=True, exist_ok=True)
    (pack_dir / f"{run_id}.zip").write_bytes(b"PK")

    # Create PACK_MANIFEST.md with run_id
    manifest = f"# PACK_MANIFEST\n\n| Field | Value |\n|-------|-------|\n| run_id | {run_id} |\n"
    (pack_dir / "PACK_MANIFEST.md").write_text(manifest, encoding="utf-8")

    return report_dir, run_id


class TestRunIdConsistency:
    """Tests for run_id consistency validation."""

    def test_consistent_artifacts(self, tmp_path):
        """All artifacts with matching run_id → consistent."""
        report_dir, run_id = _setup_full_consistent(tmp_path)
        result = validate_run_id_consistency(str(report_dir))
        assert result["consistent"] is True
        assert result["errors"] == []

    def test_missing_run_id_file(self, tmp_path):
        """No run_id.txt → inconsistent."""
        report_dir = tmp_path / "test-task-a2"
        report_dir.mkdir()

        result = validate_run_id_consistency(str(report_dir))
        assert result["consistent"] is False
        assert any("run_id.txt not found" in e for e in result["errors"])

    def test_hardcoded_run_id_in_prompt(self, tmp_path):
        """Hardcoded run_id in prompt instead of {{RUN_ID}} → inconsistent."""
        report_dir, run_id = _setup_full_consistent(tmp_path, "TEST_TASK_A3_20260609T120000_RD")
        # Overwrite prompt with hardcoded run_id (and no {{RUN_ID}})
        (report_dir / "GPT_REVIEW_PROMPT.md").write_text(
            "## Review " + "{{TASK_ID}}" + "\nrun_id: TEST_TASK_A3_20260609T120000_RD\n",
            encoding="utf-8",
        )

        result = validate_run_id_consistency(str(report_dir))
        assert result["consistent"] is False
        assert any("hardcoded run_id" in e for e in result["errors"])

    def test_r1_run_id_mismatch(self, tmp_path):
        """R1_RUN_ID.txt has different run_id → inconsistent."""
        report_dir, run_id = _setup_full_consistent(tmp_path, "TEST_TASK_A4_20260609T120000_RD")
        (report_dir / "R1_RUN_ID.txt").write_text("WRONG_RUN_ID", encoding="utf-8")

        result = validate_run_id_consistency(str(report_dir))
        assert result["consistent"] is False
        assert any("R1_RUN_ID.txt" in e for e in result["errors"])

    def test_gpt_reply_run_id_mismatch(self, tmp_path):
        """GPT reply has different run_id than submitted → inconsistent."""
        report_dir, run_id = _setup_full_consistent(tmp_path, "TEST_TASK_A5_20260609T120000_RD")
        (report_dir / "GPT_REVIEW_RESULT.txt").write_text(
            "run_id: WRONG_RUN_ID_XYZ\nverdict: accepted\n",
            encoding="utf-8",
        )

        result = validate_run_id_consistency(str(report_dir))
        assert result["consistent"] is False
        assert any("GPT reply run_id" in e for e in result["errors"])

    def test_gpt_reply_run_id_matches(self, tmp_path):
        """GPT reply has same run_id → consistent."""
        report_dir, run_id = _setup_full_consistent(tmp_path, "TEST_TASK_A6_20260609T120000_RD")
        (report_dir / "GPT_REVIEW_RESULT.txt").write_text(
            f"run_id: {run_id}\nverdict: accepted\n",
            encoding="utf-8",
        )

        result = validate_run_id_consistency(str(report_dir))
        assert result["consistent"] is True

    def test_missing_run_id_template_var(self, tmp_path):
        """Prompt has no {{RUN_ID}} placeholder → inconsistent (AWSP requires it)."""
        report_dir, run_id = _setup_full_consistent(tmp_path, "TEST_TASK_A7_20260609T120000_RD")
        # Overwrite prompt without {{RUN_ID}}
        (report_dir / "GPT_REVIEW_PROMPT.md").write_text(
            "## Review " + "{{TASK_ID}}" + "\nverdict: accepted\n",
            encoding="utf-8",
        )

        result = validate_run_id_consistency(str(report_dir))
        assert result["consistent"] is False
        assert any("missing {{RUN_ID}}" in e for e in result["errors"])

    def test_missing_task_id_template_var(self, tmp_path):
        """Prompt has no {{TASK_ID}} placeholder → inconsistent (AWSP requires it)."""
        report_dir, run_id = _setup_full_consistent(tmp_path, "TEST_TASK_A8_20260609T120000_RD")
        # Overwrite prompt without {{TASK_ID}}
        (report_dir / "GPT_REVIEW_PROMPT.md").write_text(
            "## Review\nrun_id: " + "{{RUN_ID}}" + "\n",
            encoding="utf-8",
        )

        result = validate_run_id_consistency(str(report_dir))
        assert result["consistent"] is False
        assert any("missing {{TASK_ID}}" in e for e in result["errors"])

    def test_missing_evidence_pack_zip(self, tmp_path):
        """No evidence pack zip → inconsistent (AWSP requires it)."""
        report_dir, run_id = _setup_full_consistent(tmp_path, "TEST_TASK_A9_20260609T120000_RD")
        # Remove the zip
        pack_dir = tmp_path / "evidence_packs" / "test-task-a1"
        for z in pack_dir.glob("*.zip"):
            z.unlink()

        result = validate_run_id_consistency(str(report_dir))
        assert result["consistent"] is False
        assert any("No evidence pack zip" in e for e in result["errors"])

    def test_manifest_run_id_mismatch(self, tmp_path):
        """PACK_MANIFEST.md has different run_id → inconsistent."""
        report_dir, run_id = _setup_full_consistent(tmp_path, "TEST_TASK_B1_20260609T120000_RD")
        # Overwrite manifest with wrong run_id
        pack_dir = tmp_path / "evidence_packs" / "test-task-a1"
        manifest = "# PACK_MANIFEST\n\n| Field | Value |\n|-------|-------|\n| run_id | WRONG_MANIFEST_RUN_ID |\n"
        (pack_dir / "PACK_MANIFEST.md").write_text(manifest, encoding="utf-8")

        result = validate_run_id_consistency(str(report_dir))
        assert result["consistent"] is False
        assert any("PACK_MANIFEST.md run_id" in e for e in result["errors"])

    def test_pack_filename_mismatch(self, tmp_path):
        """Pack filename doesn't contain run_id → inconsistent."""
        report_dir, run_id = _setup_full_consistent(tmp_path, "TEST_TASK_B2_20260609T120000_RD")
        # Rename zip to wrong name
        pack_dir = tmp_path / "evidence_packs" / "test-task-a1"
        for z in pack_dir.glob("*.zip"):
            z.unlink()
        (pack_dir / "wrong_name.zip").write_bytes(b"PK")

        result = validate_run_id_consistency(str(report_dir))
        assert result["consistent"] is False
        assert any("Pack filename" in e for e in result["errors"])

    def test_empty_run_id_file(self, tmp_path):
        """Empty run_id.txt → inconsistent."""
        report_dir = tmp_path / "test-task-b3"
        report_dir.mkdir()
        (report_dir / "run_id.txt").write_text("", encoding="utf-8")

        result = validate_run_id_consistency(str(report_dir))
        assert result["consistent"] is False
        assert any("empty" in e for e in result["errors"])

    def test_missing_pack_manifest(self, tmp_path):
        """Evidence pack zip exists but PACK_MANIFEST.md missing → inconsistent."""
        report_dir, run_id = _setup_full_consistent(tmp_path, "TEST_TASK_B4_20260609T120000_RD")
        # Remove PACK_MANIFEST.md
        pack_dir = tmp_path / "evidence_packs" / "test-task-a1"
        manifest = pack_dir / "PACK_MANIFEST.md"
        if manifest.exists():
            manifest.unlink()

        result = validate_run_id_consistency(str(report_dir))
        assert result["consistent"] is False
        assert any("PACK_MANIFEST.md not found" in e for e in result["errors"])

    def test_manifest_run_id_field_missing(self, tmp_path):
        """PACK_MANIFEST.md exists but has no run_id field → inconsistent."""
        report_dir, run_id = _setup_full_consistent(tmp_path, "TEST_TASK_B5_20260609T120000_RD")
        # Overwrite manifest without run_id field
        pack_dir = tmp_path / "evidence_packs" / "test-task-a1"
        manifest = "# PACK_MANIFEST\n\n| Field | Value |\n|-------|-------|\n| task_id | TEST |\n"
        (pack_dir / "PACK_MANIFEST.md").write_text(manifest, encoding="utf-8")

        result = validate_run_id_consistency(str(report_dir))
        assert result["consistent"] is False
        assert any("run_id field not found" in e for e in result["errors"])
