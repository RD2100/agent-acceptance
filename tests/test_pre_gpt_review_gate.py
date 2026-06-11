"""test_pre_gpt_review_gate.py — Regression tests for pre_gpt_review_gate.py + evidence_pack_linter.py.

Test cases per HANDOFF_WORKFLOW_HARDENING_PLAN.md section 5.5:
  PGT-001: Complete evidence pack -> PASS
  PGT-002: Missing manifest -> FAIL
  PGT-003: Hash inconsistency -> FAIL (not fully testable without real hashes)
  PGT-004: Empty evidence pack -> FAIL
  PGT-005: Invalid reference -> FAIL (not fully testable)
  PGT-006: Thin deliverables -> WARNING
"""

import json
import pytest
from pathlib import Path

from evidence_pack_linter import lint
from pre_gpt_review_gate import gate, resolve_required_reads_path, _extract_task_id_from_manifest


class TestEvidencePackLinter:
    """Tests for evidence_pack_linter.lint()."""

    def test_pgt001_complete_pack(self, valid_evidence_pack):
        """PGT-001: Complete evidence pack should PASS."""
        result = lint(valid_evidence_pack)
        assert result["valid"] is True
        assert len(result["errors"]) == 0

    def test_pgt002_missing_manifest(self, pack_missing_manifest):
        """PGT-002: Pack missing PACK_MANIFEST.md should FAIL."""
        result = lint(pack_missing_manifest)
        assert result["valid"] is False
        assert any("PACK_MANIFEST.md" in e for e in result["errors"])

    def test_pgt004_empty_pack(self, empty_evidence_pack):
        """PGT-004: Empty evidence pack directory should FAIL."""
        result = lint(empty_evidence_pack)
        assert result["valid"] is False
        # Should report multiple missing files
        assert len(result["errors"]) >= 4  # CLOSURE, PROMPT, MANIFEST, SAFETY + dirs

    def test_nonexistent_directory(self, tmp_path):
        """Lint on non-existent directory should FAIL gracefully."""
        result = lint(str(tmp_path / "nonexistent"))
        assert result["valid"] is False
        assert any("not found" in e for e in result["errors"])

    def test_missing_required_files(self, tmp_path):
        """Pack missing some required files should report each missing file."""
        pack = tmp_path / "partial_pack"
        pack.mkdir()
        (pack / "CLOSURE_REPORT.md").write_text("# Closure\n")
        # Missing: GPT_REVIEW_PROMPT.md, PACK_MANIFEST.md, SAFETY_ATTESTATION.md

        result = lint(str(pack))
        assert result["valid"] is False
        missing_files = [e for e in result["errors"] if "missing required file" in e]
        assert len(missing_files) == 3

    def test_missing_required_dirs(self, tmp_path):
        """Pack missing required directories should report each."""
        pack = tmp_path / "no_dirs_pack"
        pack.mkdir()
        (pack / "CLOSURE_REPORT.md").write_text("# Closure\n")
        (pack / "GPT_REVIEW_PROMPT.md").write_text("# Prompt\n")
        (pack / "PACK_MANIFEST.md").write_text("# Manifest\n")
        (pack / "SAFETY_ATTESTATION.md").write_text("# Safety\ntrue\n")
        # Missing: actual_deliverables/, reports/

        result = lint(str(pack))
        assert result["valid"] is False
        missing_dirs = [e for e in result["errors"] if "missing required directory" in e]
        assert len(missing_dirs) == 2

    def test_empty_actual_deliverables_sd01(self, tmp_path):
        """SD-01: Empty actual_deliverables should flag summary-only risk."""
        pack = tmp_path / "sd01_pack"
        pack.mkdir()
        (pack / "CLOSURE_REPORT.md").write_text("# Closure\n")
        (pack / "GPT_REVIEW_PROMPT.md").write_text("# Prompt\n")
        (pack / "PACK_MANIFEST.md").write_text("# Manifest\n")
        (pack / "SAFETY_ATTESTATION.md").write_text("# Safety\ntrue\n")
        ad = pack / "actual_deliverables"
        ad.mkdir()  # Empty!
        reports = pack / "reports"
        reports.mkdir()

        result = lint(str(pack))
        assert any("SD-01" in e for e in result["errors"])
        assert result["summary_only_risk"] == "SD-01"

    def test_thin_deliverables_warning(self, tmp_path):
        """PGT-006: <= 3 deliverable files should generate thin evidence warning."""
        pack = tmp_path / "thin_pack"
        pack.mkdir()
        (pack / "CLOSURE_REPORT.md").write_text("# Closure\n")
        (pack / "GPT_REVIEW_PROMPT.md").write_text("# Prompt\n")
        (pack / "PACK_MANIFEST.md").write_text("# Manifest\n")
        (pack / "SAFETY_ATTESTATION.md").write_text("# Safety\ntrue\n")
        ad = pack / "actual_deliverables"
        ad.mkdir()
        (ad / "file1.py").write_text("# 1\n")
        (ad / "file2.py").write_text("# 2\n")
        reports = pack / "reports"
        reports.mkdir()
        (reports / "TEST_OUTPUT.txt").write_text("PASS\n")

        result = lint(str(pack))
        assert result["valid"] is True
        assert any("thin evidence" in w for w in result["warnings"])

    def test_safety_attestation_warning(self, tmp_path):
        """Empty or thin SAFETY_ATTESTATION should warn."""
        pack = tmp_path / "safety_pack"
        pack.mkdir()
        (pack / "CLOSURE_REPORT.md").write_text("# Closure\n")
        (pack / "GPT_REVIEW_PROMPT.md").write_text("# Prompt\n")
        (pack / "PACK_MANIFEST.md").write_text("# Manifest\n")
        (pack / "SAFETY_ATTESTATION.md").write_text("# Empty safety\n")  # No 'true'
        ad = pack / "actual_deliverables"
        ad.mkdir()
        (ad / "f.py").write_text("# f\n")
        (ad / "g.py").write_text("# g\n")
        (ad / "h.py").write_text("# h\n")
        (ad / "i.py").write_text("# i\n")
        reports = pack / "reports"
        reports.mkdir()

        result = lint(str(pack))
        assert any("SAFETY_ATTESTATION" in w for w in result["warnings"])


class TestPreGptReviewGate:
    """Tests for pre_gpt_review_gate.gate()."""

    def test_pgt001_gate_passes_valid_pack(self, valid_evidence_pack):
        """PGT-001: Gate should pass for a valid evidence pack."""
        result = gate(valid_evidence_pack)
        assert result["gate_passed"] is True
        assert len(result["errors"]) == 0
        assert "READY" in result["recommendation"]

    def test_pgt002_gate_blocks_missing_manifest(self, pack_missing_manifest):
        """PGT-002: Gate should block when manifest is missing."""
        result = gate(pack_missing_manifest)
        assert result["gate_passed"] is False
        assert "BLOCKED" in result["recommendation"]

    def test_pgt004_gate_blocks_empty_pack(self, empty_evidence_pack):
        """PGT-004: Gate should block on empty evidence pack."""
        result = gate(empty_evidence_pack)
        assert result["gate_passed"] is False
        assert len(result["errors"]) > 0

    def test_gate_extra_checks_deliverable_count(self, valid_evidence_pack):
        """Gate should report deliverable count in extra_checks."""
        result = gate(valid_evidence_pack)
        assert "deliverable_count" in result["extra_checks"]
        assert result["extra_checks"]["deliverable_count"] >= 4

    def test_gate_has_sha256_entries(self, valid_evidence_pack):
        """Gate should check manifest for SHA-256 entries."""
        result = gate(valid_evidence_pack)
        assert result["extra_checks"].get("has_sha256_entries") is True

    def test_gate_sd01_blocks_summary_only(self, tmp_path):
        """Gate should block summary-only packs (SD-01)."""
        pack = tmp_path / "sd01_gate_pack"
        pack.mkdir()
        (pack / "CLOSURE_REPORT.md").write_text("# Closure\n")
        (pack / "GPT_REVIEW_PROMPT.md").write_text("# Prompt\n")
        (pack / "PACK_MANIFEST.md").write_text("# Manifest\n")
        (pack / "SAFETY_ATTESTATION.md").write_text("# Safety\ntrue\n")
        ad = pack / "actual_deliverables"
        ad.mkdir()  # Empty
        reports = pack / "reports"
        reports.mkdir()

        result = gate(str(pack))
        assert result["gate_passed"] is False
        assert any("SD-01" in e for e in result["errors"])


class TestStartupReadGateIntegration:
    """Tests for pre_gpt_review_gate startup read gate integration."""

    def _make_valid_pack(self, tmp_path):
        """Create a minimal valid evidence pack."""
        pack = tmp_path / "pack"
        pack.mkdir()
        (pack / "CLOSURE_REPORT.md").write_text("# Closure\n")
        (pack / "GPT_REVIEW_PROMPT.md").write_text("# Prompt\n")
        (pack / "PACK_MANIFEST.md").write_text("# Manifest\n| task_id | TEST-TASK |\nsha256: abc\n")
        (pack / "SAFETY_ATTESTATION.md").write_text("# Safety\ntrue\n")
        ad = pack / "actual_deliverables"
        ad.mkdir()
        (ad / "file1.py").write_text("# f1\n")
        (ad / "file2.py").write_text("# f2\n")
        (ad / "file3.py").write_text("# f3\n")
        (ad / "file4.py").write_text("# f4\n")
        reports = pack / "reports"
        reports.mkdir()
        (reports / "TEST_OUTPUT.txt").write_text("PASS\n")
        return pack

    def test_no_proof_path_skips_startup_check(self, tmp_path):
        """Without startup_proof_path, gate should behave as before."""
        pack = self._make_valid_pack(tmp_path)
        result = gate(str(pack))
        assert result["gate_passed"] is True
        assert "startup_read_gate" not in result["extra_checks"]

    def test_valid_proof_passes_startup_gate(self, tmp_path):
        """Valid startup proof + valid pack → gate passes."""
        import hashlib
        pack = self._make_valid_pack(tmp_path)

        # Create a file to be read
        fake_file = tmp_path / "doc.md"
        fake_file.write_text("# doc\n")
        file_hash = hashlib.sha256(fake_file.read_bytes()).hexdigest()

        # Create required reads definition
        reads_def = {"required_reads": [
            {"path": str(fake_file), "must_read_at_startup": True, "evidence_level": "P1"}
        ]}
        reads_path = tmp_path / "required_reads.json"
        reads_path.write_text(json.dumps(reads_def))

        # Create valid proof
        proof = {
            "task_id": "TEST-TASK",
            "reads_completed": [{"file": str(fake_file), "summary_hash": f"sha256:{file_hash}"}],
            "gate_status": "pass",
        }
        proof_path = tmp_path / "proof.json"
        proof_path.write_text(json.dumps(proof))

        result = gate(
            str(pack),
            startup_proof_path=str(proof_path),
            required_reads_path=str(reads_path),
        )
        assert result["gate_passed"] is True
        assert "startup_read_gate" in result["extra_checks"]
        assert result["extra_checks"]["startup_read_gate"]["gate_passed"] is True

    def test_invalid_proof_blocks_gate(self, tmp_path):
        """Invalid startup proof → gate blocks even with valid pack."""
        pack = self._make_valid_pack(tmp_path)

        reads_def = {"required_reads": [
            {"path": "missing.md", "must_read_at_startup": True, "evidence_level": "P0"}
        ]}
        reads_path = tmp_path / "required_reads.json"
        reads_path.write_text(json.dumps(reads_def))

        # Proof with empty reads_completed — required file missing
        proof = {
            "task_id": "TEST-TASK",
            "reads_completed": [],
            "gate_status": "pass",
        }
        proof_path = tmp_path / "proof.json"
        proof_path.write_text(json.dumps(proof))

        result = gate(
            str(pack),
            startup_proof_path=str(proof_path),
            required_reads_path=str(reads_path),
        )
        assert result["gate_passed"] is False
        assert any("startup_read_gate" in e for e in result["errors"])

    def test_strict_mode_promotes_warnings(self, tmp_path):
        """Strict mode should promote task_id mismatch to error."""
        pack = self._make_valid_pack(tmp_path)

        reads_def = {"required_reads": []}
        reads_path = tmp_path / "required_reads.json"
        reads_path.write_text(json.dumps(reads_def))

        # Proof with wrong task_id
        proof = {
            "task_id": "WRONG-TASK",
            "reads_completed": [],
            "gate_status": "pass",
        }
        proof_path = tmp_path / "proof.json"
        proof_path.write_text(json.dumps(proof))

        # Non-strict: passes
        result_normal = gate(
            str(pack),
            startup_proof_path=str(proof_path),
            required_reads_path=str(reads_path),
            strict=False,
        )
        assert result_normal["gate_passed"] is True

        # Strict: fails due to task_id mismatch
        result_strict = gate(
            str(pack),
            startup_proof_path=str(proof_path),
            required_reads_path=str(reads_path),
            strict=True,
        )
        assert result_strict["gate_passed"] is False
        assert any("startup_read_gate" in e and "task_id" in e for e in result_strict["errors"])

    def test_startup_coverage_ratio_reported(self, tmp_path):
        """Startup read gate coverage ratio should appear in extra_checks."""
        pack = self._make_valid_pack(tmp_path)

        reads_def = {"required_reads": [
            {"path": "f1.md", "must_read_at_startup": True},
            {"path": "f2.md", "must_read_at_startup": True},
        ]}
        reads_path = tmp_path / "required_reads.json"
        reads_path.write_text(json.dumps(reads_def))

        proof = {
            "task_id": "",
            "reads_completed": [{"file": "f1.md"}],
            "gate_status": "pass",
        }
        proof_path = tmp_path / "proof.json"
        proof_path.write_text(json.dumps(proof))

        result = gate(
            str(pack),
            startup_proof_path=str(proof_path),
            required_reads_path=str(reads_path),
        )
        assert "startup_coverage_ratio" in result["extra_checks"]
        assert result["extra_checks"]["startup_coverage_ratio"] == 0.5

    def test_missing_required_reads_blocks_gate(self, tmp_path):
        """When required reads file not found, gate should block."""
        pack = self._make_valid_pack(tmp_path)

        proof = {
            "task_id": "",
            "reads_completed": [],
            "gate_status": "pass",
        }
        proof_path = tmp_path / "proof.json"
        proof_path.write_text(json.dumps(proof))

        # Point to a nonexistent required reads file
        result = gate(
            str(pack),
            startup_proof_path=str(proof_path),
            required_reads_path=str(tmp_path / "nonexistent_reads.json"),
        )
        assert result["gate_passed"] is False
        assert any("NEXT_AGENT_REQUIRED_READS.json not found" in e for e in result["errors"])


class TestResolveRequiredReadsPath:
    """Tests for resolve_required_reads_path() auto-detection."""

    def test_explicit_path_exists(self, tmp_path):
        """Explicit path that exists should be returned."""
        f = tmp_path / "reads.json"
        f.write_text("{}")
        assert resolve_required_reads_path(str(f)) == str(f)

    def test_explicit_path_not_exists(self, tmp_path):
        """Explicit path that doesn't exist should return None."""
        assert resolve_required_reads_path(str(tmp_path / "missing.json")) is None

    def test_auto_detect_in_reports_subdir(self, tmp_path):
        """Should find file in _reports subdirectory."""
        # Create a fake _reports structure
        reports_dir = tmp_path / "_reports" / "some-task"
        reports_dir.mkdir(parents=True)
        reads_file = reports_dir / "NEXT_AGENT_REQUIRED_READS.json"
        reads_file.write_text("{}")

        # Temporarily monkey-patch the search paths
        import pre_gpt_review_gate
        old_paths = pre_gpt_review_gate._REQUIRED_READS_SEARCH_PATHS
        pre_gpt_review_gate._REQUIRED_READS_SEARCH_PATHS = [
            tmp_path / "NEXT_AGENT_REQUIRED_READS.json",  # doesn't exist
        ]
        old_repo = pre_gpt_review_gate.REPO
        pre_gpt_review_gate.REPO = tmp_path
        try:
            result = resolve_required_reads_path()
            assert result == str(reads_file)
        finally:
            pre_gpt_review_gate._REQUIRED_READS_SEARCH_PATHS = old_paths
            pre_gpt_review_gate.REPO = old_repo

    def test_no_reads_found(self, tmp_path):
        """Should return None when no file found anywhere."""
        import pre_gpt_review_gate
        old_paths = pre_gpt_review_gate._REQUIRED_READS_SEARCH_PATHS
        pre_gpt_review_gate._REQUIRED_READS_SEARCH_PATHS = [
            tmp_path / "nonexistent.json",
        ]
        old_repo = pre_gpt_review_gate.REPO
        pre_gpt_review_gate.REPO = tmp_path
        try:
            result = resolve_required_reads_path()
            assert result is None
        finally:
            pre_gpt_review_gate._REQUIRED_READS_SEARCH_PATHS = old_paths
            pre_gpt_review_gate.REPO = old_repo


class TestExtractTaskIdFromManifest:
    """Tests for _extract_task_id_from_manifest()."""

    def test_standard_manifest(self, tmp_path):
        """Should extract task_id from standard table format."""
        m = tmp_path / "PACK_MANIFEST.md"
        m.write_text(
            "# PACK_MANIFEST\n\n"
            "| Field | Value |\n"
            "|-------|-------|\n"
            "| task_id | MY-TASK-A1 |\n"
            "| run_id | MY_RUN_ID |\n"
        )
        assert _extract_task_id_from_manifest(m) == "MY-TASK-A1"

    def test_no_task_id(self, tmp_path):
        """Should return empty string when no task_id row."""
        m = tmp_path / "PACK_MANIFEST.md"
        m.write_text("# Manifest\n\n| Field | Value |\n|---|---|\n| run_id | X |\n")
        assert _extract_task_id_from_manifest(m) == ""

    def test_missing_file(self, tmp_path):
        """Should return empty string for nonexistent file."""
        m = tmp_path / "missing.md"
        assert _extract_task_id_from_manifest(m) == ""

    def test_backtick_wrapped_value(self, tmp_path):
        """Should handle backtick-wrapped task_id values."""
        m = tmp_path / "PACK_MANIFEST.md"
        m.write_text(
            "| Field | Value |\n"
            "| task_id | `MY-TASK-A1` |\n"
        )
        assert _extract_task_id_from_manifest(m) == "MY-TASK-A1"
