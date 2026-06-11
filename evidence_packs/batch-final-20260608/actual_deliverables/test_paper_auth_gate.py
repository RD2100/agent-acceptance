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

    def test_overbroad_auth_fields_blocked(self):
        import json, tempfile, shutil
        forbidden = ['real_paper_full_text_allowed', 'paper_excerpt_allowed', 'paper_excerpt',
                     'raw_paper_text', 'external_upload_allowed', 'live_cdp_allowed',
                     'memory_write_with_paper_content', 'private_user_text']
        for field in forbidden:
            d = tempfile.mkdtemp()
            try:
                gate_file = Path(d) / '.ai' / 'paper_authorization.json'
                gate_file.parent.mkdir()
                gate_file.write_text(json.dumps({
                    'authorized': True, 'token': 'x' * 20,
                    'scope': 'synthetic_only',
                    field: True
                }))
                paper_auth_gate.GATE_FILE = gate_file
                r = paper_auth_gate.check()
                assert not r['authorized'], f'{field} must block but did not'
            finally:
                paper_auth_gate.GATE_FILE = REPO / '.ai' / 'paper_authorization.json'
                shutil.rmtree(d, ignore_errors=True)
