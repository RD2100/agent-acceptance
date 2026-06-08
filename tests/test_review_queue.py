"""Test GPT Review Queue lifecycle and fail-closed behavior."""
import json
import os
import sys
import tempfile
import shutil
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))
import review_queue as rq


class TestE2EQueue:
    """End-to-end: real evidence pack lifecycle."""

    def setup_method(self):
        self.tmp = tempfile.mkdtemp()
        self.orig = rq.QUEUE_DIR
        rq.QUEUE_DIR = Path(self.tmp) / "review_queue"

    def teardown_method(self):
        rq.QUEUE_DIR = self.orig
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_e2e_with_real_evidence_pack(self):
        """Full lifecycle with actual evidence pack from agent-acceptance."""
        real_pack = REPO_ROOT / "evidence_packs/context-compression-a1/closure-pack-r6.zip"
        if not real_pack.exists():
            return  # Skip if pack not found

        t = rq.create_ticket("E2E-TEST", str(real_pack))
        assert t["status"] == "queued"
        assert len(t["evidence_pack_sha256"]) == 64

        t = rq.submit_ticket(t["ticket_id"], "https://chatgpt.com/c/test")
        assert t["status"] == "submitted"

        reply = Path(self.tmp) / "gpt_reply.txt"
        reply.write_text("overall_judgment: accepted\nnext_task_authorization:\n  authorized: yes\nEND_OF_GPT_RESPONSE")
        validation = rq.validate_gpt_reply(str(reply))
        assert validation["valid"]

        t = rq.record_gpt_reply(t["ticket_id"], "accepted", str(reply))
        assert t["status"] == "gpt_replied"
        assert t["gpt_verdict"] == "accepted"

        t = rq.accept_ticket(t["ticket_id"])
        assert t["status"] == "accepted"

        t = rq.close_ticket(t["ticket_id"])
        assert t["status"] == "closed"


class TestTicketLifecycle:
    """Full lifecycle: create → submit → reply → accept → close."""

    def setup_method(self):
        self.tmp = tempfile.mkdtemp()
        self.orig_queue = rq.QUEUE_DIR
        rq.QUEUE_DIR = Path(self.tmp) / "review_queue"
        # Create a dummy evidence pack
        self.evidence = Path(self.tmp) / "test-pack.zip"
        self.evidence.write_text("dummy evidence")

    def teardown_method(self):
        rq.QUEUE_DIR = self.orig_queue
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_full_lifecycle(self):
        """Ticket goes through all states without error."""
        t = rq.create_ticket("TEST-TASK", str(self.evidence))
        assert t["status"] == "queued"

        t = rq.submit_ticket(t["ticket_id"], "https://chatgpt.com/c/test")
        assert t["status"] == "submitted"

        reply = Path(self.tmp) / "gpt_reply.txt"
        reply.write_text("overall_judgment: accepted\nnext_task_authorization:\n  authorized: yes\nEND_OF_GPT_RESPONSE")
        t = rq.record_gpt_reply(t["ticket_id"], "accepted", str(reply))
        assert t["status"] == "gpt_replied"
        assert t["gpt_verdict"] == "accepted"

        t = rq.accept_ticket(t["ticket_id"])
        assert t["status"] == "accepted"

        t = rq.close_ticket(t["ticket_id"])
        assert t["status"] == "closed"

    def test_only_one_active(self):
        """Cannot submit a second ticket while one is submitted/gpt_replied."""
        ev2 = Path(self.tmp) / "test2.zip"
        ev2.write_text("dummy2")

        t1 = rq.create_ticket("TASK-1", str(self.evidence))
        t2 = rq.create_ticket("TASK-2", str(ev2))

        t1 = rq.submit_ticket(t1["ticket_id"], "http://x.com")
        assert t1["status"] == "submitted"

        try:
            rq.submit_ticket(t2["ticket_id"], "http://y.com")
            assert False, "Should have failed"
        except SystemExit:
            pass  # expected

        # Block first (blocked is terminal, releases active slot)
        reply = Path(self.tmp) / "blocked_r.txt"
        reply.write_text("overall_judgment: blocked\nEND_OF_GPT_RESPONSE")
        t1 = rq.record_gpt_reply(t1["ticket_id"], "blocked", str(reply))
        assert t1["status"] == "gpt_replied"
        t2 = rq.submit_ticket(t2["ticket_id"], "http://y.com")
        assert t2["status"] == "submitted"

    def test_cannot_accept_without_gpt_accepted(self):
        """Cannot accept a ticket whose GPT verdict is blocked."""
        t = rq.create_ticket("TASK-3", str(self.evidence))
        t = rq.submit_ticket(t["ticket_id"], "http://x.com")

        reply = Path(self.tmp) / "reply.txt"
        reply.write_text("overall_judgment: blocked\nEND_OF_GPT_RESPONSE")
        t = rq.record_gpt_reply(t["ticket_id"], "blocked", str(reply))

        try:
            rq.accept_ticket(t["ticket_id"])
            assert False, "Should have failed"
        except SystemExit:
            pass

    def test_ticket_requires_existing_evidence(self):
        """Creating a ticket with non-existent pack must fail."""
        try:
            rq.create_ticket("TASK-4", "/nonexistent/pack.zip")
            assert False, "Should have failed"
        except SystemExit:
            pass

    def test_queue_status(self):
        """Status command reports correct counts."""
        rq.create_ticket("TASK-A", str(self.evidence))
        status = rq.queue_status()
        assert status["total"] >= 1
        assert status["by_status"]["queued"] >= 1

    def test_sha256_verified_on_create(self):
        """Creating ticket with mismatched SHA256 fails validation."""
        t = rq.create_ticket("TASK-HASH", str(self.evidence))
        t["evidence_pack_sha256"] = "0" * 64  # fake hash
        errors = rq._validate_ticket(t)
        assert any("mismatch" in e for e in errors)

    def test_gpt_reply_must_have_end_marker(self):
        """GPT reply without END_OF_GPT_RESPONSE fails validation."""
        reply = Path(self.tmp) / "bad_reply.txt"
        reply.write_text("overall_judgment: accepted\n(no end marker)")
        result = rq.validate_gpt_reply(str(reply))
        assert not result["valid"]

    def test_gpt_reply_valid(self):
        """Valid GPT reply passes."""
        reply = Path(self.tmp) / "good_reply.txt"
        reply.write_text("overall_judgment: accepted\nnext_task_authorization:\n  authorized: yes\nEND_OF_GPT_RESPONSE")
        result = rq.validate_gpt_reply(str(reply))
        assert result["valid"]
        assert result["verdict"] == "accepted"

    def test_gpt_reply_without_next_auth_fails(self):
        """GPT reply missing next_task_authorization fails validation."""
        reply = Path(self.tmp) / "no_auth.txt"
        reply.write_text("overall_judgment: accepted\nEND_OF_GPT_RESPONSE")
        result = rq.validate_gpt_reply(str(reply))
        assert not result["valid"]
