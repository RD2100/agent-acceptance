"""test_startup_read_gate.py — Regression tests for startup_read_gate.py.

Tests the startup read gate enforcement script per hardening plan §5.7.
"""

import json
import pytest
from pathlib import Path

import sys
SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from startup_read_gate import gate


def make_proof(tmp_path, proof_data: dict, filename="proof.json") -> str:
    """Write a startup proof JSON file and return its path."""
    p = tmp_path / filename
    p.write_text(json.dumps(proof_data), encoding="utf-8")
    return str(p)


def make_required_reads(tmp_path, reads_data: dict, filename="required_reads.json") -> str:
    """Write a required reads definition JSON file and return its path."""
    p = tmp_path / filename
    p.write_text(json.dumps(reads_data), encoding="utf-8")
    return str(p)


class TestGatePass:
    """Tests where the gate should pass."""

    def test_complete_proof_passes(self, tmp_path):
        """All required reads covered with valid hashes — gate PASS."""
        # Create a fake repo file
        fake_file = tmp_path / "rules" / "core.md"
        fake_file.parent.mkdir(parents=True, exist_ok=True)
        fake_file.write_text("# core rules\n")

        import hashlib
        file_hash = hashlib.sha256(fake_file.read_bytes()).hexdigest()

        required = {
            "required_reads": [
                {
                    "path": "rules/core.md",
                    "must_read_at_startup": True,
                    "evidence_level": "P0",
                    "sha256": file_hash,
                    "fail_closed_if_missing": True,
                }
            ]
        }

        proof = {
            "task_id": "TEST-TASK",
            "startup_timestamp": "2026-06-09T01:00:00+00:00",
            "reads_completed": [
                {
                    "file": str(fake_file),
                    "summary_hash": f"sha256:{file_hash}",
                }
            ],
            "total_required": 1,
            "total_completed": 1,
            "gate_status": "pass",
        }

        proof_path = make_proof(tmp_path, proof)
        reads_path = make_required_reads(tmp_path, required)
        result = gate("TEST-TASK", proof_path, reads_path, repo_root=str(tmp_path))
        assert result["gate_passed"] is True
        assert len(result["errors"]) == 0

    def test_empty_required_reads_passes(self, tmp_path):
        """No required reads defined — gate should PASS (nothing to check)."""
        required = {"required_reads": []}
        proof = {
            "task_id": "TEST-TASK",
            "reads_completed": [],
            "gate_status": "pass",
        }

        proof_path = make_proof(tmp_path, proof)
        reads_path = make_required_reads(tmp_path, required)
        result = gate("TEST-TASK", proof_path, reads_path, repo_root=str(tmp_path))
        assert result["gate_passed"] is True


class TestGateFail:
    """Tests where the gate should fail."""

    def test_missing_proof_file(self, tmp_path):
        """Proof file doesn't exist — gate FAIL."""
        reads_path = make_required_reads(tmp_path, {"required_reads": []})
        result = gate(
            "TEST-TASK",
            str(tmp_path / "nonexistent.json"),
            reads_path,
            repo_root=str(tmp_path),
        )
        assert result["gate_passed"] is False
        assert any("not found" in e for e in result["errors"])

    def test_missing_required_reads_file(self, tmp_path):
        """Required reads file doesn't exist — gate FAIL."""
        proof = {"task_id": "TEST", "reads_completed": [], "gate_status": "pass"}
        proof_path = make_proof(tmp_path, proof)
        result = gate(
            "TEST-TASK",
            proof_path,
            str(tmp_path / "nonexistent.json"),
            repo_root=str(tmp_path),
        )
        assert result["gate_passed"] is False
        assert any("not found" in e for e in result["errors"])

    def test_incomplete_proof_fails(self, tmp_path):
        """Proof missing required reads — gate FAIL."""
        required = {
            "required_reads": [
                {"path": "file1.md", "must_read_at_startup": True, "evidence_level": "P0"},
                {"path": "file2.md", "must_read_at_startup": True, "evidence_level": "P1"},
            ]
        }
        proof = {
            "task_id": "TEST-TASK",
            "reads_completed": [
                {"file": "file1.md"}  # Only 1 of 2 required
            ],
            "gate_status": "pass",
        }

        proof_path = make_proof(tmp_path, proof)
        reads_path = make_required_reads(tmp_path, required)
        result = gate("TEST-TASK", proof_path, reads_path, repo_root=str(tmp_path))
        assert result["gate_passed"] is False
        assert any("missing" in e for e in result["errors"])

    def test_gate_status_not_pass(self, tmp_path):
        """Proof has gate_status != 'pass' — gate FAIL."""
        required = {"required_reads": []}
        proof = {
            "task_id": "TEST-TASK",
            "reads_completed": [],
            "gate_status": "fail",
        }

        proof_path = make_proof(tmp_path, proof)
        reads_path = make_required_reads(tmp_path, required)
        result = gate("TEST-TASK", proof_path, reads_path, repo_root=str(tmp_path))
        assert result["gate_passed"] is False
        assert any("gate_status" in e for e in result["errors"])

    def test_hash_mismatch_fails(self, tmp_path):
        """Proof has wrong hash for a file — gate FAIL."""
        fake_file = tmp_path / "doc.md"
        fake_file.write_text("actual content\n")

        required = {
            "required_reads": [
                {"path": "doc.md", "must_read_at_startup": True, "evidence_level": "P0"},
            ]
        }
        proof = {
            "task_id": "TEST-TASK",
            "reads_completed": [
                {"file": str(fake_file), "summary_hash": "sha256:0000000000000000000000000000000000000000000000000000000000000000"},
            ],
            "gate_status": "pass",
        }

        proof_path = make_proof(tmp_path, proof)
        reads_path = make_required_reads(tmp_path, required)
        result = gate("TEST-TASK", proof_path, reads_path, repo_root=str(tmp_path))
        assert result["gate_passed"] is False
        assert any("hash mismatch" in e for e in result["errors"])

    def test_p0_missing_is_critical(self, tmp_path):
        """P0-level required read missing — gate FAIL with P0 critical message."""
        required = {
            "required_reads": [
                {"path": "critical.md", "must_read_at_startup": True, "evidence_level": "P0", "fail_closed_if_missing": True},
            ]
        }
        proof = {
            "task_id": "TEST-TASK",
            "reads_completed": [],
            "gate_status": "pass",
        }

        proof_path = make_proof(tmp_path, proof)
        reads_path = make_required_reads(tmp_path, required)
        result = gate("TEST-TASK", proof_path, reads_path, repo_root=str(tmp_path))
        assert result["gate_passed"] is False
        assert any("P0" in e for e in result["errors"])

    def test_invalid_proof_json(self, tmp_path):
        """Malformed JSON in proof file — gate FAIL."""
        proof_path = tmp_path / "bad_proof.json"
        proof_path.write_text("{invalid json", encoding="utf-8")
        reads_path = make_required_reads(tmp_path, {"required_reads": []})
        result = gate("TEST-TASK", str(proof_path), reads_path, repo_root=str(tmp_path))
        assert result["gate_passed"] is False
        assert any("invalid" in e.lower() for e in result["errors"])


class TestGateExtraChecks:
    """Test extra_checks output."""

    def test_coverage_ratio(self, tmp_path):
        """Coverage ratio should be computed correctly."""
        required = {
            "required_reads": [
                {"path": "f1.md", "must_read_at_startup": True},
                {"path": "f2.md", "must_read_at_startup": True},
            ]
        }
        proof = {
            "task_id": "TEST-TASK",
            "reads_completed": [{"file": "f1.md"}],
            "gate_status": "pass",
        }

        proof_path = make_proof(tmp_path, proof)
        reads_path = make_required_reads(tmp_path, required)
        result = gate("TEST-TASK", proof_path, reads_path, repo_root=str(tmp_path))
        assert result["extra_checks"]["coverage_ratio"] == 0.5

    def test_task_id_mismatch_warning(self, tmp_path):
        """Task ID mismatch should generate warning, not error."""
        required = {"required_reads": []}
        proof = {
            "task_id": "WRONG-TASK",
            "reads_completed": [],
            "gate_status": "pass",
        }

        proof_path = make_proof(tmp_path, proof)
        reads_path = make_required_reads(tmp_path, required)
        result = gate("CORRECT-TASK", proof_path, reads_path, repo_root=str(tmp_path))
        assert result["gate_passed"] is True  # Warning, not error
        assert any("task_id mismatch" in w for w in result["warnings"])

    def test_optional_reads_not_checked(self, tmp_path):
        """Reads with must_read_at_startup=false should not be required."""
        required = {
            "required_reads": [
                {"path": "optional.md", "must_read_at_startup": False},
            ]
        }
        proof = {
            "task_id": "TEST-TASK",
            "reads_completed": [],
            "gate_status": "pass",
        }

        proof_path = make_proof(tmp_path, proof)
        reads_path = make_required_reads(tmp_path, required)
        result = gate("TEST-TASK", proof_path, reads_path, repo_root=str(tmp_path))
        assert result["gate_passed"] is True

    def test_coverage_ratio_with_extra_proof_entries(self, tmp_path):
        """Coverage should count matched required / must_read, not total proof entries."""
        required = {
            "required_reads": [
                {"path": "f1.md", "must_read_at_startup": True},
                {"path": "f2.md", "must_read_at_startup": True},
            ]
        }
        proof = {
            "task_id": "TEST-TASK",
            "reads_completed": [
                {"file": "f1.md"},
                {"file": "f2.md"},
                {"file": "extra_bonuses.md"},  # not required
            ],
            "gate_status": "pass",
        }

        proof_path = make_proof(tmp_path, proof)
        reads_path = make_required_reads(tmp_path, required)
        result = gate("TEST-TASK", proof_path, reads_path, repo_root=str(tmp_path))
        # Matched required = 2, must_read_count = 2 → 1.0 (not 1.5)
        assert result["extra_checks"]["coverage_ratio"] == 1.0
        assert result["extra_checks"]["matched_required_reads"] == 2


class TestStrictMode:
    """Tests for --strict mode enhancements."""

    def test_strict_task_id_mismatch_becomes_error(self, tmp_path):
        """In strict mode, task_id mismatch should be error, not warning."""
        required = {"required_reads": []}
        proof = {
            "task_id": "WRONG-TASK",
            "reads_completed": [],
            "gate_status": "pass",
        }

        proof_path = make_proof(tmp_path, proof)
        reads_path = make_required_reads(tmp_path, required)

        # Non-strict: warning only, gate passes
        result_normal = gate("CORRECT-TASK", proof_path, reads_path, repo_root=str(tmp_path), strict=False)
        assert result_normal["gate_passed"] is True
        assert any("task_id mismatch" in w for w in result_normal["warnings"])

        # Strict: becomes error, gate fails
        result_strict = gate("CORRECT-TASK", proof_path, reads_path, repo_root=str(tmp_path), strict=True)
        assert result_strict["gate_passed"] is False
        assert any("strict" in e and "task_id mismatch" in e for e in result_strict["errors"])

    def test_strict_p0_missing_hash_is_error(self, tmp_path):
        """In strict mode, P0/fail_closed file without summary_hash → error."""
        fake_file = tmp_path / "critical.md"
        fake_file.write_text("critical content\n")

        required = {
            "required_reads": [
                {
                    "path": "critical.md",
                    "must_read_at_startup": True,
                    "evidence_level": "P0",
                    "fail_closed_if_missing": True,
                }
            ]
        }
        proof = {
            "task_id": "TEST-TASK",
            "reads_completed": [
                {"file": str(fake_file)}  # no summary_hash!
            ],
            "gate_status": "pass",
        }

        proof_path = make_proof(tmp_path, proof)
        reads_path = make_required_reads(tmp_path, required)

        # Non-strict: passes (hash check is optional)
        result_normal = gate("TEST-TASK", proof_path, reads_path, repo_root=str(tmp_path), strict=False)
        assert result_normal["gate_passed"] is True

        # Strict: fails because P0 file missing hash in proof
        result_strict = gate("TEST-TASK", proof_path, reads_path, repo_root=str(tmp_path), strict=True)
        assert result_strict["gate_passed"] is False
        assert any("strict" in e and "summary_hash" in e for e in result_strict["errors"])

    def test_strict_p1_without_hash_is_ok(self, tmp_path):
        """In strict mode, P1 file without summary_hash should NOT error."""
        fake_file = tmp_path / "info.md"
        fake_file.write_text("info\n")

        required = {
            "required_reads": [
                {
                    "path": "info.md",
                    "must_read_at_startup": True,
                    "evidence_level": "P1",
                    "fail_closed_if_missing": False,
                }
            ]
        }
        proof = {
            "task_id": "TEST-TASK",
            "reads_completed": [
                {"file": str(fake_file)}  # no summary_hash, but P1
            ],
            "gate_status": "pass",
        }

        proof_path = make_proof(tmp_path, proof)
        reads_path = make_required_reads(tmp_path, required)
        result = gate("TEST-TASK", proof_path, reads_path, repo_root=str(tmp_path), strict=True)
        assert result["gate_passed"] is True

    def test_strict_fail_closed_nonexistent_file(self, tmp_path):
        """In strict mode, non-existent fail_closed file with proof hash → error."""
        required = {
            "required_reads": [
                {
                    "path": "missing_critical.md",
                    "must_read_at_startup": True,
                    "evidence_level": "P0",
                    "fail_closed_if_missing": True,
                }
            ]
        }
        # Proof claims to have read the file with a hash, but file doesn't exist
        proof = {
            "task_id": "TEST-TASK",
            "reads_completed": [
                {
                    "file": "missing_critical.md",
                    "summary_hash": "sha256:abc123",
                }
            ],
            "gate_status": "pass",
        }

        proof_path = make_proof(tmp_path, proof)
        reads_path = make_required_reads(tmp_path, required)

        # Non-strict: warning only
        result_normal = gate("TEST-TASK", proof_path, reads_path, repo_root=str(tmp_path), strict=False)
        assert any("non-existent" in w for w in result_normal["warnings"])
        # Still fails due to missing read (step 5), but not strict-specific error
        assert not any("strict" in e for e in result_normal["errors"])

        # Strict: error for fail_closed
        result_strict = gate("TEST-TASK", proof_path, reads_path, repo_root=str(tmp_path), strict=True)
        assert any("strict" in e and "fail_closed" in e for e in result_strict["errors"])

    def test_strict_with_valid_p0_hash_passes(self, tmp_path):
        """Strict mode with valid P0 hash should pass."""
        import hashlib
        fake_file = tmp_path / "rules" / "core.md"
        fake_file.parent.mkdir(parents=True, exist_ok=True)
        fake_file.write_text("# core\n")
        file_hash = hashlib.sha256(fake_file.read_bytes()).hexdigest()

        required = {
            "required_reads": [
                {
                    "path": "rules/core.md",
                    "must_read_at_startup": True,
                    "evidence_level": "P0",
                    "fail_closed_if_missing": True,
                }
            ]
        }
        proof = {
            "task_id": "TEST-TASK",
            "reads_completed": [
                {
                    "file": str(fake_file),
                    "summary_hash": f"sha256:{file_hash}",
                }
            ],
            "gate_status": "pass",
        }

        proof_path = make_proof(tmp_path, proof)
        reads_path = make_required_reads(tmp_path, required)
        result = gate("TEST-TASK", proof_path, reads_path, repo_root=str(tmp_path), strict=True)
        assert result["gate_passed"] is True
        assert result["extra_checks"]["hash_verified"] == 1

    def test_strict_coverage_ratio_capped_at_one(self, tmp_path):
        """Strict coverage ratio should be capped at 1.0 even with extra proof entries."""
        required = {
            "required_reads": [
                {"path": "f1.md", "must_read_at_startup": True},
            ]
        }
        proof = {
            "task_id": "TEST-TASK",
            "reads_completed": [
                {"file": "f1.md"},
                {"file": "bonus1.md"},
                {"file": "bonus2.md"},
            ],
            "gate_status": "pass",
        }

        proof_path = make_proof(tmp_path, proof)
        reads_path = make_required_reads(tmp_path, required)
        result = gate("TEST-TASK", proof_path, reads_path, repo_root=str(tmp_path), strict=True)
        # 1 matched / 1 must_read = 1.0 (not 3.0)
        assert result["extra_checks"]["coverage_ratio"] == 1.0
        assert result["extra_checks"]["matched_required_reads"] == 1
