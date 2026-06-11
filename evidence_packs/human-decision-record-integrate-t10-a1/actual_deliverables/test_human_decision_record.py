#!/usr/bin/env python3
"""
test_human_decision_record.py — Tests for human_decision_record.py.

Covers:
  - TestCreateRecord: record creation with valid/invalid inputs
  - TestValidateRecord: record validation with various scenarios
  - TestExitConditions: T10 transition guard (human_decision_recorded + decision_evidence_attached)
  - TestCLI: CLI smoke tests for create/validate subcommands
"""

import json
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))

from human_decision_record import (
    VALID_DECISION_TYPES,
    REQUIRED_FIELDS,
    create_record,
    validate_record,
)


# ---------------------------------------------------------------------------
# TestCreateRecord
# ---------------------------------------------------------------------------
class TestCreateRecord:
    """Tests for create_record()."""

    def test_valid_record_override(self):
        rec = create_record(
            task_id="TASK-001",
            decision_type="override",
            decision_reason="GPT verdict too conservative",
            decision_maker="operator_a",
        )
        assert rec["task_id"] == "TASK-001"
        assert rec["decision_type"] == "override"
        assert rec["decision_reason"] == "GPT verdict too conservative"
        assert rec["decision_maker"] == "operator_a"
        assert rec["schema_version"] == "1.0.0"
        assert rec["decision_timestamp"]  # non-empty ISO timestamp
        assert rec["evidence_files"] == []
        assert rec["exit_conditions_met"]["human_decision_recorded"] is True

    def test_valid_record_approve(self):
        rec = create_record(
            task_id="TASK-002",
            decision_type="approve",
            decision_reason="Changes look correct",
            decision_maker="operator_b",
        )
        assert rec["decision_type"] == "approve"

    def test_valid_record_reject(self):
        rec = create_record(
            task_id="TASK-003",
            decision_type="reject",
            decision_reason="Insufficient test coverage",
            decision_maker="operator_c",
        )
        assert rec["decision_type"] == "reject"

    def test_valid_record_defer(self):
        rec = create_record(
            task_id="TASK-004",
            decision_type="defer",
            decision_reason="Need more information from stakeholder",
            decision_maker="operator_d",
        )
        assert rec["decision_type"] == "defer"

    def test_all_valid_decision_types(self):
        for dt in VALID_DECISION_TYPES:
            rec = create_record(
                task_id="TASK-DT",
                decision_type=dt,
                decision_reason="test",
                decision_maker="tester",
            )
            assert rec["decision_type"] == dt

    def test_invalid_decision_type_raises(self):
        with pytest.raises(ValueError, match="Invalid decision_type"):
            create_record(
                task_id="TASK-BAD",
                decision_type="escalate",
                decision_reason="test",
                decision_maker="op",
            )

    def test_empty_reason_raises(self):
        with pytest.raises(ValueError, match="decision_reason must not be empty"):
            create_record(
                task_id="TASK-EMPTY",
                decision_type="approve",
                decision_reason="",
                decision_maker="op",
            )

    def test_whitespace_only_reason_raises(self):
        with pytest.raises(ValueError, match="decision_reason must not be empty"):
            create_record(
                task_id="TASK-WS",
                decision_type="approve",
                decision_reason="   ",
                decision_maker="op",
            )

    def test_empty_maker_raises(self):
        with pytest.raises(ValueError, match="decision_maker must not be empty"):
            create_record(
                task_id="TASK-NOMAKER",
                decision_type="approve",
                decision_reason="valid reason",
                decision_maker="",
            )

    def test_whitespace_only_maker_raises(self):
        with pytest.raises(ValueError, match="decision_maker must not be empty"):
            create_record(
                task_id="TASK-WSM",
                decision_type="approve",
                decision_reason="valid reason",
                decision_maker="   ",
            )

    def test_evidence_files_attached(self):
        rec = create_record(
            task_id="TASK-EV",
            decision_type="override",
            decision_reason="Evidence supports override",
            decision_maker="op",
            evidence_files=["screenshot.png", "test_log.txt"],
        )
        assert rec["evidence_files"] == ["screenshot.png", "test_log.txt"]
        assert rec["exit_conditions_met"]["decision_evidence_attached"] is True

    def test_no_evidence_files_means_not_attached(self):
        rec = create_record(
            task_id="TASK-NOEV",
            decision_type="approve",
            decision_reason="Simple approve",
            decision_maker="op",
        )
        assert rec["evidence_files"] == []
        assert rec["exit_conditions_met"]["decision_evidence_attached"] is False

    def test_gpt_verdict_context_stored(self):
        ctx = "GPT returned blocked due to missing test coverage for edge case X"
        rec = create_record(
            task_id="TASK-CTX",
            decision_type="override",
            decision_reason="Edge case X is handled by existing test Y",
            decision_maker="op",
            gpt_verdict_context=ctx,
        )
        assert rec["gpt_verdict_context"] == ctx

    def test_reason_and_maker_stripped(self):
        rec = create_record(
            task_id="TASK-STRIP",
            decision_type="approve",
            decision_reason="  reason with spaces  ",
            decision_maker="  maker  ",
        )
        assert rec["decision_reason"] == "reason with spaces"
        assert rec["decision_maker"] == "maker"

    def test_timestamp_is_iso_cst(self):
        rec = create_record(
            task_id="TASK-TS",
            decision_type="approve",
            decision_reason="test",
            decision_maker="op",
        )
        ts = rec["decision_timestamp"]
        # Should contain timezone offset +08:00
        assert "+08:00" in ts


# ---------------------------------------------------------------------------
# TestValidateRecord
# ---------------------------------------------------------------------------
class TestValidateRecord:
    """Tests for validate_record()."""

    @pytest.fixture
    def valid_record_file(self, tmp_path):
        """Create a valid record file and return its path."""
        rec = create_record(
            task_id="TASK-VALID",
            decision_type="approve",
            decision_reason="All checks pass",
            decision_maker="operator_a",
            evidence_files=["proof.json"],
        )
        fpath = tmp_path / "valid_record.json"
        fpath.write_text(json.dumps(rec, indent=2), encoding="utf-8")
        return str(fpath)

    @pytest.fixture
    def record_file(self, tmp_path):
        """Helper to create a record file from a dict."""
        def _make(data, name="record.json"):
            fpath = tmp_path / name
            fpath.write_text(json.dumps(data, indent=2), encoding="utf-8")
            return str(fpath)
        return _make

    def test_valid_record_passes(self, valid_record_file):
        result = validate_record(valid_record_file)
        assert result["valid"] is True
        assert result["errors"] == []
        assert result["record"] is not None

    def test_nonexistent_file(self):
        result = validate_record("/nonexistent/path/record.json")
        assert result["valid"] is False
        assert "record file not found" in result["errors"][0]

    def test_invalid_json(self, tmp_path):
        fpath = tmp_path / "bad.json"
        fpath.write_text("{invalid json content", encoding="utf-8")
        result = validate_record(str(fpath))
        assert result["valid"] is False
        assert any("invalid JSON" in e for e in result["errors"])

    def test_missing_task_id(self, record_file):
        rec = create_record(
            task_id="X", decision_type="approve",
            decision_reason="r", decision_maker="m",
            evidence_files=["e.json"],
        )
        del rec["task_id"]
        path = record_file(rec)
        result = validate_record(path)
        assert result["valid"] is False
        assert any("task_id" in e for e in result["errors"])

    def test_missing_decision_type(self, record_file):
        rec = create_record(
            task_id="X", decision_type="approve",
            decision_reason="r", decision_maker="m",
            evidence_files=["e.json"],
        )
        del rec["decision_type"]
        path = record_file(rec)
        result = validate_record(path)
        assert result["valid"] is False
        assert any("decision_type" in e for e in result["errors"])

    def test_missing_decision_reason(self, record_file):
        rec = create_record(
            task_id="X", decision_type="approve",
            decision_reason="r", decision_maker="m",
            evidence_files=["e.json"],
        )
        rec["decision_reason"] = ""
        path = record_file(rec)
        result = validate_record(path)
        assert result["valid"] is False
        assert any("decision_reason" in e for e in result["errors"])

    def test_missing_decision_maker(self, record_file):
        rec = create_record(
            task_id="X", decision_type="approve",
            decision_reason="r", decision_maker="m",
            evidence_files=["e.json"],
        )
        rec["decision_maker"] = ""
        path = record_file(rec)
        result = validate_record(path)
        assert result["valid"] is False
        assert any("decision_maker" in e for e in result["errors"])

    def test_missing_decision_timestamp(self, record_file):
        rec = create_record(
            task_id="X", decision_type="approve",
            decision_reason="r", decision_maker="m",
            evidence_files=["e.json"],
        )
        del rec["decision_timestamp"]
        path = record_file(rec)
        result = validate_record(path)
        assert result["valid"] is False
        assert any("decision_timestamp" in e for e in result["errors"])

    def test_invalid_decision_type_in_file(self, record_file):
        rec = create_record(
            task_id="X", decision_type="approve",
            decision_reason="r", decision_maker="m",
            evidence_files=["e.json"],
        )
        rec["decision_type"] = "invalid_type"
        path = record_file(rec)
        result = validate_record(path)
        assert result["valid"] is False
        assert any("invalid decision_type" in e for e in result["errors"])

    def test_no_evidence_files_fails(self, record_file):
        rec = create_record(
            task_id="X", decision_type="approve",
            decision_reason="r", decision_maker="m",
        )
        # No evidence files — should fail T10 guard
        path = record_file(rec)
        result = validate_record(path)
        assert result["valid"] is False
        assert any("evidence files" in e for e in result["errors"])

    def test_exit_conditions_structure(self, valid_record_file):
        result = validate_record(valid_record_file)
        ec = result["exit_conditions"]
        assert ec["human_decision_recorded"] is True
        assert ec["decision_evidence_attached"] is True

    def test_exit_conditions_no_evidence(self, record_file):
        rec = create_record(
            task_id="X", decision_type="approve",
            decision_reason="r", decision_maker="m",
        )
        path = record_file(rec)
        result = validate_record(path)
        assert result["exit_conditions"]["decision_evidence_attached"] is False

    def test_multiple_missing_fields(self, record_file):
        """Record with only task_id — all other required fields missing."""
        rec = {"task_id": "X"}
        path = record_file(rec)
        result = validate_record(path)
        assert result["valid"] is False
        # Should report at least 4 missing fields
        missing = [e for e in result["errors"] if "missing required field" in e]
        assert len(missing) >= 4

    def test_empty_record(self, record_file):
        """Completely empty record."""
        path = record_file({})
        result = validate_record(path)
        assert result["valid"] is False
        assert len(result["errors"]) > 0


# ---------------------------------------------------------------------------
# TestExitConditions — T10 transition guard
# ---------------------------------------------------------------------------
class TestExitConditions:
    """Tests specifically for T10 guard: human_decision_recorded AND decision_evidence_attached."""

    def test_full_t10_guard_pass(self, tmp_path):
        """Both exit conditions met → T10 transition allowed."""
        rec = create_record(
            task_id="TASK-T10",
            decision_type="override",
            decision_reason="Override justified with evidence",
            decision_maker="senior_op",
            evidence_files=["evidence.json", "approval_email.eml"],
        )
        fpath = tmp_path / "t10_record.json"
        fpath.write_text(json.dumps(rec, indent=2), encoding="utf-8")

        result = validate_record(str(fpath))
        assert result["valid"] is True
        assert result["exit_conditions"]["human_decision_recorded"] is True
        assert result["exit_conditions"]["decision_evidence_attached"] is True

    def test_t10_blocked_no_evidence(self, tmp_path):
        """human_decision_recorded=True but no evidence → T10 blocked."""
        rec = create_record(
            task_id="TASK-T10-NOEV",
            decision_type="approve",
            decision_reason="Looks good",
            decision_maker="op",
            # No evidence files
        )
        fpath = tmp_path / "t10_no_ev.json"
        fpath.write_text(json.dumps(rec, indent=2), encoding="utf-8")

        result = validate_record(str(fpath))
        assert result["valid"] is False
        assert result["exit_conditions"]["human_decision_recorded"] is True
        assert result["exit_conditions"]["decision_evidence_attached"] is False

    def test_t10_blocked_decision_not_recorded(self, tmp_path):
        """exit_conditions_met.human_decision_recorded=False → T10 blocked."""
        rec = create_record(
            task_id="TASK-T10-NOREC",
            decision_type="defer",
            decision_reason="Need more info",
            decision_maker="op",
            evidence_files=["notes.txt"],
        )
        # Tamper: set human_decision_recorded to False
        rec["exit_conditions_met"]["human_decision_recorded"] = False

        fpath = tmp_path / "t10_norec.json"
        fpath.write_text(json.dumps(rec, indent=2), encoding="utf-8")

        result = validate_record(str(fpath))
        assert result["valid"] is False
        assert result["exit_conditions"]["human_decision_recorded"] is False

    def test_t10_both_conditions_fail(self, tmp_path):
        """Neither condition met → T10 fully blocked."""
        rec = {
            "schema_version": "1.0.0",
            "task_id": "TASK-T10-FAIL",
            "decision_type": "reject",
            "decision_reason": "Rejected",
            "decision_maker": "op",
            "decision_timestamp": "2026-06-09T10:00:00+08:00",
            "evidence_files": [],
            "exit_conditions_met": {
                "human_decision_recorded": False,
            },
        }
        fpath = tmp_path / "t10_fail.json"
        fpath.write_text(json.dumps(rec, indent=2), encoding="utf-8")

        result = validate_record(str(fpath))
        assert result["valid"] is False
        assert result["exit_conditions"]["human_decision_recorded"] is False
        assert result["exit_conditions"]["decision_evidence_attached"] is False


# ---------------------------------------------------------------------------
# TestCLI — Smoke tests for CLI subcommands
# ---------------------------------------------------------------------------
class TestCLI:
    """CLI smoke tests for create/validate subcommands."""

    SCRIPT = str(SCRIPTS / "human_decision_record.py")

    def test_create_subcommand(self, tmp_path):
        output_path = tmp_path / "cli_create.json"
        result = subprocess.run(
            [
                sys.executable, self.SCRIPT, "create",
                "--task-id", "CLI-TASK-001",
                "--decision-type", "approve",
                "--decision-reason", "CLI test approval",
                "--decision-maker", "cli_tester",
                "--output", str(output_path),
            ],
            capture_output=True, text=True,
        )
        assert result.returncode == 0
        assert output_path.exists()
        rec = json.loads(output_path.read_text(encoding="utf-8"))
        assert rec["task_id"] == "CLI-TASK-001"
        assert rec["decision_type"] == "approve"

    def test_create_with_evidence(self, tmp_path):
        output_path = tmp_path / "cli_ev.json"
        result = subprocess.run(
            [
                sys.executable, self.SCRIPT, "create",
                "--task-id", "CLI-TASK-002",
                "--decision-type", "override",
                "--decision-reason", "Override with evidence",
                "--decision-maker", "cli_tester",
                "--evidence-files", "file1.json,file2.png",
                "--output", str(output_path),
            ],
            capture_output=True, text=True,
        )
        assert result.returncode == 0
        rec = json.loads(output_path.read_text(encoding="utf-8"))
        assert rec["evidence_files"] == ["file1.json", "file2.png"]

    def test_validate_subcommand_valid(self, tmp_path):
        # First create a valid record
        rec = create_record(
            task_id="CLI-VALID",
            decision_type="approve",
            decision_reason="Valid for CLI test",
            decision_maker="op",
            evidence_files=["proof.json"],
        )
        fpath = tmp_path / "valid.json"
        fpath.write_text(json.dumps(rec, indent=2), encoding="utf-8")

        result = subprocess.run(
            [
                sys.executable, self.SCRIPT, "validate",
                "--record-path", str(fpath),
            ],
            capture_output=True, text=True,
        )
        assert result.returncode == 0
        assert "RECORD OK" in result.stdout

    def test_validate_subcommand_invalid(self, tmp_path):
        fpath = tmp_path / "invalid.json"
        fpath.write_text(json.dumps({"task_id": "X"}), encoding="utf-8")

        result = subprocess.run(
            [
                sys.executable, self.SCRIPT, "validate",
                "--record-path", str(fpath),
            ],
            capture_output=True, text=True,
        )
        assert result.returncode == 1
        assert "RECORD INVALID" in result.stdout

    def test_no_subcommand_shows_help(self):
        result = subprocess.run(
            [sys.executable, self.SCRIPT],
            capture_output=True, text=True,
        )
        assert result.returncode == 1

    def test_invalid_decision_type_cli_rejected(self, tmp_path):
        """argparse choices should reject invalid decision_type."""
        output_path = tmp_path / "bad.json"
        result = subprocess.run(
            [
                sys.executable, self.SCRIPT, "create",
                "--task-id", "CLI-BAD",
                "--decision-type", "escalate",
                "--decision-reason", "test",
                "--decision-maker", "op",
                "--output", str(output_path),
            ],
            capture_output=True, text=True,
        )
        assert result.returncode != 0
