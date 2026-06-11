"""Tests for MULTI-AGENT-BOUNDED-EXECUTION-B1 bounded dry run mechanism."""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
SCRIPTS = REPO / "scripts"
sys.path.insert(0, str(SCRIPTS))

B1_DIR = REPO / "_reports" / "multi-agent-bounded-execution-b1"
EXEC_REPORT = B1_DIR / "EXECUTION_REPORT.json"
RUN_SPECS = B1_DIR / "RUN_SPECS.json"
CHAIN_EV = B1_DIR / "CHAIN_EVIDENCE.json"
GATE_RES = B1_DIR / "GATE_RESULTS.json"
AUTH_REC = B1_DIR / "AUTHORIZATION_RECORD.json"
CDP_EV = B1_DIR / "cdp_raw_evidence.json"
TEST_EV = B1_DIR / "raw_test_output.json"
CAP_EV = B1_DIR / "cap029_passport.json"
SUMMARY = B1_DIR / "DRY_RUN_SUMMARY.json"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


# ── TestB1AuthorizationRecord ──────────────────────────────────────────


class TestB1AuthorizationRecord:
    """Verify human authorization record for B1 execution gate."""

    def test_authorization_file_exists(self):
        assert AUTH_REC.exists()

    def test_authorization_has_required_fields(self):
        data = _load(AUTH_REC)
        for field in ["authorization_id", "task_id", "scope", "decision_maker",
                       "approved_at", "expires_at", "risk_acknowledged"]:
            assert field in data, f"Missing field: {field}"

    def test_risk_acknowledged_is_true(self):
        data = _load(AUTH_REC)
        assert data["risk_acknowledged"] is True

    def test_scope_is_bounded_local_only(self):
        data = _load(AUTH_REC)
        assert "bounded" in data["scope"].lower() or "local" in data["scope"].lower()

    def test_forbidden_commands_include_dangerous_ops(self):
        data = _load(AUTH_REC)
        forbidden = data.get("forbidden_commands", [])
        assert any("push" in c for c in forbidden)
        assert any("reset" in c for c in forbidden)

    def test_expected_write_set_is_reports_only(self):
        data = _load(AUTH_REC)
        for w in data.get("expected_write_set", []):
            assert w.startswith("_reports/"), f"Write set must be in _reports/: {w}"


# ── TestB1ExecutionReport ──────────────────────────────────────────────


class TestB1ExecutionReport:
    """Verify ExecutionReport artifact structure and content."""

    def test_execution_report_exists(self):
        assert EXEC_REPORT.exists()

    def test_execution_report_has_required_fields(self):
        data = _load(EXEC_REPORT)
        for field in ["report_id", "batch_id", "generated_at", "status", "summary"]:
            assert field in data, f"Missing field: {field}"

    def test_execution_report_status_is_pass(self):
        data = _load(EXEC_REPORT)
        assert data["status"] == "pass"

    def test_execution_report_has_run_ids(self):
        data = _load(EXEC_REPORT)
        assert "run_ids" in data
        assert len(data["run_ids"]) >= 1

    def test_execution_report_has_gate_results(self):
        data = _load(EXEC_REPORT)
        assert "gate_results" in data
        assert len(data["gate_results"]) >= 5

    def test_execution_report_has_trust_record(self):
        data = _load(EXEC_REPORT)
        trust = data.get("trust_record", {})
        assert "session_id" in trust
        assert "dispatch_method" in trust

    def test_execution_report_summary_mentions_dry_run(self):
        data = _load(EXEC_REPORT)
        assert "dry_run" in data["summary"].lower() or "dry run" in data["summary"].lower()

    def test_execution_report_recommendations_exist(self):
        data = _load(EXEC_REPORT)
        assert "recommendations" in data
        assert len(data["recommendations"]) >= 1


# ── TestB1RunSpecs ─────────────────────────────────────────────────────


class TestB1RunSpecs:
    """Verify RunSpec artifacts for each assignment."""

    def test_run_specs_file_exists(self):
        assert RUN_SPECS.exists()

    def test_run_specs_is_array(self):
        data = _load(RUN_SPECS)
        assert isinstance(data, list)
        assert len(data) >= 1

    def test_each_run_spec_has_required_fields(self):
        data = _load(RUN_SPECS)
        for rs in data:
            for field in ["run_id", "task_id", "started_at", "status", "exit_code"]:
                assert field in rs, f"Missing field: {field}"

    def test_all_run_specs_are_dry_run(self):
        data = _load(RUN_SPECS)
        for rs in data:
            assert rs.get("dry_run") is True, f"{rs['run_id']} is not dry_run"

    def test_all_run_specs_completed(self):
        data = _load(RUN_SPECS)
        for rs in data:
            assert rs["status"] == "completed", f"{rs['run_id']} status is {rs['status']}"
            assert rs["exit_code"] == 0, f"{rs['run_id']} exit_code is {rs['exit_code']}"


# ── TestB1ChainEvidence ────────────────────────────────────────────────


class TestB1ChainEvidence:
    """Verify chain evidence audit trail."""

    def test_chain_evidence_exists(self):
        assert CHAIN_EV.exists()

    def test_chain_evidence_has_required_fields(self):
        data = _load(CHAIN_EV)
        for field in ["run_id", "task_file", "executor_id", "created_at", "producer"]:
            assert field in data, f"Missing field: {field}"

    def test_executor_is_local_bounded(self):
        data = _load(CHAIN_EV)
        assert "bounded" in data["executor_id"].lower() or "local" in data["executor_id"].lower()

    def test_producer_is_bounded_script(self):
        data = _load(CHAIN_EV)
        assert "bounded" in data["producer"].lower()


# ── TestB1GateResults ──────────────────────────────────────────────────


class TestB1GateResults:
    """Verify gate result structure and P0 compliance."""

    def test_gate_results_file_exists(self):
        assert GATE_RES.exists()

    def test_gate_results_has_entries(self):
        data = _load(GATE_RES)
        assert isinstance(data, list)
        assert len(data) >= 5

    def test_each_gate_has_required_fields(self):
        data = _load(GATE_RES)
        for g in data:
            for field in ["gate_id", "run_id", "gate_level", "gate_name", "result", "checked_at"]:
                assert field in g, f"Missing field: {field}"

    def test_no_p0_failures(self):
        data = _load(GATE_RES)
        p0_fails = [g for g in data if g["gate_level"] == "P0" and g["result"] == "fail"]
        assert len(p0_fails) == 0, f"P0 failures: {[g['gate_name'] for g in p0_fails]}"

    def test_signer_is_not_executor(self):
        data = _load(GATE_RES)
        for g in data:
            signer = g.get("signer_role", "")
            assert signer not in ("executor", "fixer", "coder"), f"Signer is {signer}"


# ── TestB1SupplementaryEvidence ────────────────────────────────────────


class TestB1SupplementaryEvidence:
    """Verify supplementary evidence for R2 limitations."""

    def test_cdp_evidence_exists(self):
        assert CDP_EV.exists()

    def test_cdp_evidence_has_raw_responses(self):
        data = _load(CDP_EV)
        assert data.get("cdp_active") is True
        assert data.get("raw_version_response") is not None

    def test_test_evidence_exists(self):
        assert TEST_EV.exists()

    def test_test_evidence_passed(self):
        data = _load(TEST_EV)
        assert data.get("passed") is True
        assert data.get("exit_code") == 0

    def test_test_evidence_has_raw_output(self):
        data = _load(TEST_EV)
        assert len(data.get("stdout", "")) > 100

    def test_cap029_evidence_exists(self):
        assert CAP_EV.exists()

    def test_cap029_evidence_found(self):
        data = _load(CAP_EV)
        assert data.get("found") is True
        assert len(data.get("raw_passport_excerpt", "")) > 50


# ── TestB1DryRunSummary ────────────────────────────────────────────────


class TestB1DryRunSummary:
    """Verify overall dry run summary metrics."""

    def test_summary_exists(self):
        assert SUMMARY.exists()

    def test_summary_all_completed(self):
        data = _load(SUMMARY)
        assert data["completed"] == data["total_assignments"]
        assert data["blocked"] == 0

    def test_summary_all_gates_passed(self):
        data = _load(SUMMARY)
        assert data["gates_failed"] == 0
        assert data["gates_passed"] == data["total_gates"]

    def test_summary_evidence_flags(self):
        data = _load(SUMMARY)
        assert data["cdp_active"] is True
        assert data["tests_passed"] is True
        assert data["cap029_found"] is True


# ── TestB1ScriptModule ─────────────────────────────────────────────────


class TestB1ScriptModule:
    """Test the bounded_execution_dry_run module directly."""

    def test_import_module(self):
        from bounded_execution_dry_run import (
            verify_taskspec_schema, verify_conflict_registry,
            verify_no_forbidden_actions, collect_cdp_evidence,
        )
        assert callable(verify_taskspec_schema)

    def test_verify_taskspec_passes_valid(self):
        from bounded_execution_dry_run import verify_taskspec_schema
        result = verify_taskspec_schema({
            "task_id": "test", "title": "Test", "priority": "P2",
            "status": "ready", "description": "A test task"
        })
        assert result["result"] == "pass"

    def test_verify_taskspec_fails_missing(self):
        from bounded_execution_dry_run import verify_taskspec_schema
        result = verify_taskspec_schema({"task_id": "test"})
        assert result["result"] == "fail"

    def test_verify_no_forbidden_clean(self):
        from bounded_execution_dry_run import verify_no_forbidden_actions
        result = verify_no_forbidden_actions({
            "task_id": "test", "description": "Read-only verification"
        })
        assert result["result"] == "pass"

    def test_verify_no_forbidden_blocks(self):
        from bounded_execution_dry_run import verify_no_forbidden_actions
        result = verify_no_forbidden_actions({
            "task_id": "test", "description": "Run npm install to set up"
        })
        assert result["result"] == "fail"
