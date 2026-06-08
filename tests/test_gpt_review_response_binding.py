"""Test GPT review response binding guard — all negative and positive paths."""
import tempfile, os
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import verify_gpt_reply as guard

def _reply(content):
    d = tempfile.mkdtemp()
    p = Path(d) / "reply.txt"
    p.write_text(content, encoding="utf-8")
    return str(p)

class TestVerifyFailClosed:
    def test_missing_file_blocks(self):
        r = guard.verify("/nonexistent/reply.txt")
        assert not r["valid"]

    def test_missing_end_marker_blocks(self):
        r = guard.verify(_reply("overall_judgment: accepted"))
        assert not r["valid"]

    def test_missing_judgment_blocks(self):
        r = guard.verify(_reply("END_OF_GPT_RESPONSE"))
        assert not r["valid"]

    def test_invalid_judgment_blocks(self):
        r = guard.verify(_reply("overall_judgment: maybe\nEND_OF_GPT_RESPONSE"))
        assert not r["valid"]

    def test_accepted_without_next_auth_blocks(self):
        r = guard.verify(_reply("overall_judgment: accepted\nEND_OF_GPT_RESPONSE"))
        assert not r["valid"]

    def test_task_id_mismatch_blocks(self):
        r = guard.verify(_reply("task_id: OTHER-TASK\noverall_judgment: blocked\nEND_OF_GPT_RESPONSE"), "MY-TASK")
        assert not r["valid"]

class TestVerifyPass:
    def test_blocked_reply_valid(self):
        r = guard.verify(_reply("overall_judgment: blocked\nblocking_issues:\n  - x\nEND_OF_GPT_RESPONSE"))
        assert r["valid"]
        assert r["overall_judgment"] == "blocked"

    def test_accepted_with_next_auth_valid(self):
        r = guard.verify(_reply("overall_judgment: accepted\nnext_task_authorization:\n  authorized: yes\nEND_OF_GPT_RESPONSE"))
        assert r["valid"]
        assert r["overall_judgment"] == "accepted"

    def test_task_id_match_valid(self):
        r = guard.verify(_reply("task_id: MY-TASK\noverall_judgment: accepted\nnext_task_authorization:\n  authorized: yes\nEND_OF_GPT_RESPONSE"), "MY-TASK")
        assert r["valid"]

class TestClosureReady:
    def test_accepted_is_closure_ready(self):
        r = guard.closure_ready(_reply("task_id: T\noverall_judgment: accepted\nnext_task_authorization:\n  authorized: yes\nEND_OF_GPT_RESPONSE"), "T")
        assert r["closure_ready"]

    def test_blocked_is_not_closure_ready(self):
        r = guard.closure_ready(_reply("task_id: T\noverall_judgment: blocked\nEND_OF_GPT_RESPONSE"), "T")
        assert not r["closure_ready"]

    def test_review_unverified_not_closure_ready(self):
        r = guard.closure_ready(_reply("task_id: T\noverall_judgment: review_unverified\nEND_OF_GPT_RESPONSE"), "T")
        assert not r["closure_ready"]
