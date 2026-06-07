"""Test paper GO/NOGO gate fail-closed behavior."""
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))
import paper_go_nogo

class TestPaperGoNogo:
    def test_default_is_nogo(self):
        r = paper_go_nogo.check()
        assert not r["go"], "Must be NOGO by default"

    def test_has_all_checks(self):
        r = paper_go_nogo.check()
        for key in ("auth", "preflight", "pilot_runner", "dry_run_packet"):
            assert key in r["checks"], f"Missing check: {key}"

    def test_has_timestamp(self):
        r = paper_go_nogo.check()
        assert "timestamp" in r

    def test_auth_must_pass_for_go(self):
        r = paper_go_nogo.check()
        assert not r["checks"]["auth"]["authorized"]
        assert not r["go"]
