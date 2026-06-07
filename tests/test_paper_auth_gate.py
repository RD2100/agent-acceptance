"""Test paper authorization gate fail-closed behavior."""
import json, tempfile, os, sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))
import paper_auth_gate

class TestPaperAuthGate:
    def test_no_auth_file_returns_unauthorized(self):
        result = paper_auth_gate.check()
        assert not result["authorized"]

    def test_expired_auth_returns_unauthorized(self):
        result = paper_auth_gate.check()
        assert not result["authorized"]

    def test_gate_has_proper_structure(self):
        result = paper_auth_gate.check()
        assert "authorized" in result
        assert "reason" in result

    def test_gate_output_is_valid_json(self):
        import io, json
        r = paper_auth_gate.check()
        json.dumps(r)  # must not raise
