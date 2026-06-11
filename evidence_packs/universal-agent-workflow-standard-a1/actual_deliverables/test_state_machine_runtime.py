"""test_state_machine_runtime.py — Tests for state_machine_runtime.py.

Tests the process state machine runtime enforcement including:
- State definitions and valid transitions
- draft → gate_passing guard conditions (evidence pack + startup read gate)
- Integration with startup_read_gate and evidence_pack_linter
"""

import json
import pytest
from pathlib import Path

import sys
SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from state_machine_runtime import (
    is_valid_transition,
    check_transition,
    check_draft_to_gate_passing,
    check_human_required_to_gate_passing,
    STATES,
    VALID_TRANSITIONS,
)


class TestStateDefinitions:
    """Tests for state machine structure."""

    def test_eight_states(self):
        """State machine should have exactly 8 states."""
        assert len(STATES) == 8

    def test_one_initial_state(self):
        """Exactly one state should be initial."""
        initial = [s for s, d in STATES.items() if d["is_initial"]]
        assert initial == ["draft"]

    def test_one_final_state(self):
        """Exactly one state should be final."""
        final = [s for s, d in STATES.items() if d["is_final"]]
        assert final == ["closed"]

    def test_ten_transitions(self):
        """State machine should have exactly 10 transitions."""
        assert len(VALID_TRANSITIONS) == 10

    def test_all_transition_states_exist(self):
        """All states referenced in transitions should exist."""
        for from_s, to_s in VALID_TRANSITIONS:
            assert from_s in STATES, f"Unknown from-state: {from_s}"
            assert to_s in STATES, f"Unknown to-state: {to_s}"


class TestValidTransitions:
    """Tests for is_valid_transition()."""

    def test_draft_to_gate_passing(self):
        assert is_valid_transition("draft", "gate_passing") is True

    def test_gate_passing_to_gpt_reviewing(self):
        assert is_valid_transition("gate_passing", "gpt_reviewing") is True

    def test_blocked_to_draft(self):
        """Blocked state should allow retry to draft."""
        assert is_valid_transition("blocked", "draft") is True

    def test_invalid_transition(self):
        assert is_valid_transition("draft", "gpt_reviewing") is False

    def test_unknown_state(self):
        assert is_valid_transition("unknown", "draft") is False

    def test_closed_is_terminal(self):
        """Closed state should have no outgoing transitions."""
        outgoing = [(f, t) for f, t in VALID_TRANSITIONS if f == "closed"]
        assert len(outgoing) == 0

    def test_human_required_to_gate_passing(self):
        assert is_valid_transition("human_required", "gate_passing") is True

    def test_gpt_reviewing_to_human_required(self):
        assert is_valid_transition("gpt_reviewing", "human_required") is True


class TestDraftToGatePassing:
    """Tests for draft → gate_passing guard conditions."""

    def test_no_guards_blocks_transition(self):
        """Without any guard inputs, transition should be BLOCKED (fail-closed)."""
        result = check_draft_to_gate_passing()
        assert result["transition_allowed"] is False
        assert any("guard not checked" in e for e in result["errors"])

    def test_valid_pack_passes(self, tmp_path):
        """Valid evidence pack should pass linter guard."""
        pack = tmp_path / "pack"
        pack.mkdir()
        (pack / "CLOSURE_REPORT.md").write_text("# Closure\n")
        (pack / "GPT_REVIEW_PROMPT.md").write_text("# Prompt\n")
        (pack / "PACK_MANIFEST.md").write_text("# Manifest\n")
        (pack / "SAFETY_ATTESTATION.md").write_text("# Safety\ntrue\n")
        ad = pack / "actual_deliverables"
        ad.mkdir()
        (ad / "f1.py").write_text("# f\n")
        reports = pack / "reports"
        reports.mkdir()

        result = check_draft_to_gate_passing(evidence_pack_dir=str(pack))
        assert result["guards"]["evidence_pack_linter_pass"] is True
        assert result["guards"]["evidence_pack_complete"] is True

    def test_invalid_pack_blocks(self, tmp_path):
        """Invalid evidence pack should block transition."""
        pack = tmp_path / "bad_pack"
        pack.mkdir()

        result = check_draft_to_gate_passing(evidence_pack_dir=str(pack))
        assert result["guards"]["evidence_pack_linter_pass"] is False
        assert result["transition_allowed"] is False

    def test_empty_deliverables_blocks(self, tmp_path):
        """Pack with empty actual_deliverables should block."""
        pack = tmp_path / "empty_pack"
        pack.mkdir()
        (pack / "CLOSURE_REPORT.md").write_text("# Closure\n")
        (pack / "GPT_REVIEW_PROMPT.md").write_text("# Prompt\n")
        (pack / "PACK_MANIFEST.md").write_text("# Manifest\n")
        (pack / "SAFETY_ATTESTATION.md").write_text("# Safety\ntrue\n")
        ad = pack / "actual_deliverables"
        ad.mkdir()  # empty
        reports = pack / "reports"
        reports.mkdir()

        result = check_draft_to_gate_passing(evidence_pack_dir=str(pack))
        assert result["guards"]["evidence_pack_complete"] is False

    def test_startup_proof_integration(self, tmp_path):
        """Valid startup proof should pass startup_read_gate guard."""
        import hashlib

        # Create valid evidence pack
        pack = tmp_path / "pack"
        pack.mkdir()
        (pack / "CLOSURE_REPORT.md").write_text("# Closure\n")
        (pack / "GPT_REVIEW_PROMPT.md").write_text("# Prompt\n")
        (pack / "PACK_MANIFEST.md").write_text("# Manifest\n")
        (pack / "SAFETY_ATTESTATION.md").write_text("# Safety\ntrue\n")
        ad = pack / "actual_deliverables"
        ad.mkdir()
        (ad / "f1.py").write_text("# f\n")
        reports = pack / "reports"
        reports.mkdir()

        # Create valid startup proof
        fake_file = tmp_path / "doc.md"
        fake_file.write_text("# doc\n")
        file_hash = hashlib.sha256(fake_file.read_bytes()).hexdigest()

        reads_def = {"required_reads": [
            {"path": str(fake_file), "must_read_at_startup": True, "evidence_level": "P1"}
        ]}
        reads_path = tmp_path / "required_reads.json"
        reads_path.write_text(json.dumps(reads_def))

        proof = {
            "task_id": "",
            "reads_completed": [{"file": str(fake_file), "summary_hash": f"sha256:{file_hash}"}],
            "gate_status": "pass",
        }
        proof_path = tmp_path / "proof.json"
        proof_path.write_text(json.dumps(proof))

        result = check_draft_to_gate_passing(
            evidence_pack_dir=str(pack),
            startup_proof_path=str(proof_path),
            required_reads_path=str(reads_path),
        )
        assert result["guards"]["startup_read_gate_pass"] is True
        assert result["transition_allowed"] is True

    def test_invalid_proof_blocks_transition(self, tmp_path):
        """Invalid startup proof should block transition."""
        reads_def = {"required_reads": [
            {"path": "missing.md", "must_read_at_startup": True, "evidence_level": "P0"}
        ]}
        reads_path = tmp_path / "required_reads.json"
        reads_path.write_text(json.dumps(reads_def))

        proof = {
            "task_id": "",
            "reads_completed": [],
            "gate_status": "pass",
        }
        proof_path = tmp_path / "proof.json"
        proof_path.write_text(json.dumps(proof))

        result = check_draft_to_gate_passing(
            startup_proof_path=str(proof_path),
            required_reads_path=str(reads_path),
        )
        assert result["guards"]["startup_read_gate_pass"] is False
        assert result["transition_allowed"] is False


class TestCheckTransition:
    """Tests for the generic check_transition() function."""

    def test_invalid_transition_blocked(self):
        """Invalid transition should be blocked with error."""
        result = check_transition("draft", "gpt_reviewing")
        assert result["transition_allowed"] is False
        assert any("invalid transition" in e for e in result["errors"])

    def test_valid_non_draft_transition(self):
        """Valid non-draft transitions should pass (guard checks not yet implemented)."""
        result = check_transition("gate_passing", "gpt_reviewing")
        assert result["transition_allowed"] is True
        assert "note" in result

    def test_draft_gate_passing_with_pack_and_proof(self, tmp_path):
        """draft → gate_passing should pass when both pack and proof provided."""
        import hashlib
        pack = tmp_path / "pack"
        pack.mkdir()
        (pack / "CLOSURE_REPORT.md").write_text("# Closure\n")
        (pack / "GPT_REVIEW_PROMPT.md").write_text("# Prompt\n")
        (pack / "PACK_MANIFEST.md").write_text("# Manifest\n")
        (pack / "SAFETY_ATTESTATION.md").write_text("# Safety\ntrue\n")
        ad = pack / "actual_deliverables"
        ad.mkdir()
        (ad / "f.py").write_text("# f\n")
        reports = pack / "reports"
        reports.mkdir()

        # Create a valid startup proof
        fake_file = tmp_path / "doc.md"
        fake_file.write_text("# doc\n")
        file_hash = hashlib.sha256(fake_file.read_bytes()).hexdigest()
        reads_def = {"required_reads": [
            {"path": str(fake_file), "must_read_at_startup": True, "evidence_level": "P1"}
        ]}
        reads_path = tmp_path / "required_reads.json"
        reads_path.write_text(json.dumps(reads_def))
        proof = {
            "task_id": "",
            "reads_completed": [{"file": str(fake_file), "summary_hash": f"sha256:{file_hash}"}],
            "gate_status": "pass",
        }
        proof_path = tmp_path / "proof.json"
        proof_path.write_text(json.dumps(proof))

        result = check_transition(
            "draft", "gate_passing",
            evidence_pack_dir=str(pack),
            startup_proof_path=str(proof_path),
            required_reads_path=str(reads_path),
        )
        assert result["transition_allowed"] is True

    def test_draft_gate_passing_pack_only_blocked(self, tmp_path):
        """draft → gate_passing with pack but no proof should be BLOCKED."""
        pack = tmp_path / "pack"
        pack.mkdir()
        (pack / "CLOSURE_REPORT.md").write_text("# Closure\n")
        (pack / "GPT_REVIEW_PROMPT.md").write_text("# Prompt\n")
        (pack / "PACK_MANIFEST.md").write_text("# Manifest\n")
        (pack / "SAFETY_ATTESTATION.md").write_text("# Safety\ntrue\n")
        ad = pack / "actual_deliverables"
        ad.mkdir()
        (ad / "f.py").write_text("# f\n")
        reports = pack / "reports"
        reports.mkdir()

        result = check_transition("draft", "gate_passing", evidence_pack_dir=str(pack))
        assert result["transition_allowed"] is False
        assert any("startup_read_gate_pass" in e for e in result["errors"])


class TestHumanRequiredToGatePassing:
    """Tests for human_required → gate_passing (T10) guard conditions."""

    def _create_valid_record(self, tmp_path, name="record.json"):
        """Helper: create a valid decision record file."""
        from human_decision_record import create_record
        rec = create_record(
            task_id="TASK-T10",
            decision_type="override",
            decision_reason="Override justified with evidence",
            decision_maker="senior_op",
            evidence_files=["PACK_MANIFEST.md", "evidence.json"],
        )
        fpath = tmp_path / name
        fpath.write_text(json.dumps(rec, indent=2), encoding="utf-8")
        return str(fpath)

    def test_no_record_blocks_transition(self):
        """Without a decision record, T10 should be BLOCKED (fail-closed)."""
        result = check_human_required_to_gate_passing()
        assert result["transition_allowed"] is False
        assert any("guard not checked" in e for e in result["errors"])

    def test_valid_record_passes(self, tmp_path):
        """Valid decision record should pass both T10 guards."""
        path = self._create_valid_record(tmp_path)
        result = check_human_required_to_gate_passing(decision_record_path=path)
        assert result["guards"]["human_decision_recorded"] is True
        assert result["guards"]["decision_evidence_attached"] is True
        assert result["transition_allowed"] is True

    def test_no_evidence_blocks(self, tmp_path):
        """Record without evidence files should block T10."""
        from human_decision_record import create_record
        rec = create_record(
            task_id="TASK-T10-NOEV",
            decision_type="approve",
            decision_reason="Looks good",
            decision_maker="op",
            # No evidence files
        )
        fpath = tmp_path / "no_ev.json"
        fpath.write_text(json.dumps(rec, indent=2), encoding="utf-8")

        result = check_human_required_to_gate_passing(decision_record_path=str(fpath))
        assert result["guards"]["decision_evidence_attached"] is False
        assert result["transition_allowed"] is False

    def test_nonexistent_record_blocks(self, tmp_path):
        """Nonexistent record file should block T10."""
        result = check_human_required_to_gate_passing(
            decision_record_path=str(tmp_path / "nonexistent.json")
        )
        assert result["transition_allowed"] is False
        assert result["guards"]["human_decision_recorded"] is False

    def test_invalid_json_blocks(self, tmp_path):
        """Invalid JSON record should block T10."""
        fpath = tmp_path / "bad.json"
        fpath.write_text("{invalid json", encoding="utf-8")

        result = check_human_required_to_gate_passing(decision_record_path=str(fpath))
        assert result["transition_allowed"] is False

    def test_tampered_exit_conditions_blocks(self, tmp_path):
        """Record with tampered exit_conditions should block T10."""
        from human_decision_record import create_record
        rec = create_record(
            task_id="TASK-TAMPER",
            decision_type="defer",
            decision_reason="Need more info",
            decision_maker="op",
            evidence_files=["notes.txt"],
        )
        # Tamper: set human_decision_recorded to False
        rec["exit_conditions_met"]["human_decision_recorded"] = False

        fpath = tmp_path / "tampered.json"
        fpath.write_text(json.dumps(rec, indent=2), encoding="utf-8")

        result = check_human_required_to_gate_passing(decision_record_path=str(fpath))
        assert result["guards"]["human_decision_recorded"] is False
        assert result["transition_allowed"] is False

    def test_check_transition_t10_dispatch(self, tmp_path):
        """check_transition should dispatch to T10 guard for human_required → gate_passing."""
        path = self._create_valid_record(tmp_path)
        result = check_transition(
            "human_required", "gate_passing",
            decision_record_path=path,
        )
        assert result["transition"] == "human_required → gate_passing"
        assert result["transition_allowed"] is True

    def test_check_transition_t10_no_record_blocked(self):
        """check_transition for T10 without record should be blocked."""
        result = check_transition("human_required", "gate_passing")
        assert result["transition_allowed"] is False
        assert any("guard not checked" in e for e in result["errors"])

    def test_t10_with_repo_root_hash_verification(self, tmp_path):
        """T10 with repo_root enables evidence binding and hash verification."""
        from human_decision_record import create_record

        # Create evidence files
        ev = tmp_path / "ev.json"
        ev.write_text('{"data": true}', encoding="utf-8")
        pm = tmp_path / "PACK_MANIFEST.md"
        pm.write_text("# Pack Manifest\n\n## Files\n\n| # | Path | Role | SHA-256 | Size |\n|---|------|------|---------|------|\n| 1 | `PACK_MANIFEST.md` | core | `abc` | 100 |\n| 2 | `ev.json` | test | `def` | 200 |\n", encoding="utf-8")

        # Create record with hash computation
        rec = create_record(
            task_id="TASK-T10-HASH",
            decision_type="override",
            decision_reason="Hash-verified override",
            decision_maker="op",
            evidence_files=["PACK_MANIFEST.md", "ev.json"],
            repo_root=str(tmp_path),
            compute_hashes=True,
        )
        fpath = tmp_path / "record.json"
        fpath.write_text(json.dumps(rec, indent=2), encoding="utf-8")

        result = check_human_required_to_gate_passing(
            decision_record_path=str(fpath),
            repo_root=str(tmp_path),
        )
        assert result["transition_allowed"] is True
        assert result["guards"]["human_decision_recorded"] is True
        assert result["guards"]["decision_evidence_attached"] is True

    def test_t10_with_tampered_evidence_blocked(self, tmp_path):
        """T10 should block when evidence file has been tampered with."""
        from human_decision_record import create_record

        ev = tmp_path / "ev.txt"
        ev.write_text("original", encoding="utf-8")

        rec = create_record(
            task_id="TASK-T10-TAMPER",
            decision_type="approve",
            decision_reason="Tampered evidence test",
            decision_maker="op",
            evidence_files=["ev.txt"],
            repo_root=str(tmp_path),
            compute_hashes=True,
        )

        # Tamper with evidence after record creation
        ev.write_text("TAMPERED", encoding="utf-8")

        fpath = tmp_path / "record.json"
        fpath.write_text(json.dumps(rec, indent=2), encoding="utf-8")

        result = check_human_required_to_gate_passing(
            decision_record_path=str(fpath),
            repo_root=str(tmp_path),
        )
        assert result["transition_allowed"] is False
        assert any("hash mismatch" in e for e in result["errors"])
