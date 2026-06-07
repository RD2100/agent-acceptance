#!/usr/bin/env python3
"""
review_queue.py — GPT Review Queue manager for DevFrame evidence packs.

Lifecycle: queued → submitted → gpt_replied → accepted|blocked → closed.
Only ONE ticket actively submitted at a time. Fail-closed on missing evidence.
"""
import json
import hashlib
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
QUEUE_DIR = REPO_ROOT / ".ai" / "review_queue"

STATES = ["queued", "submitted", "gpt_replied", "accepted", "blocked", "closed"]
TERMINAL_STATES = {"accepted", "closed"}
ACTIVE_STATES = {"submitted", "gpt_replied", "blocked"}

# One active submission at a time
MAX_ACTIVE = 1


def _now():
    return datetime.now(timezone.utc).isoformat()


def _validate_ticket(ticket: dict) -> list[str]:
    """Validate ticket structure. Returns list of errors (empty = valid)."""
    errors = []
    if not ticket.get("ticket_id"):
        errors.append("missing ticket_id")
    if not ticket.get("task_id"):
        errors.append("missing task_id")
    if ticket.get("status") not in STATES:
        errors.append(f"invalid status: {ticket.get('status')}")
    if not ticket.get("evidence_pack_path"):
        errors.append("missing evidence_pack_path")
    pack = Path(ticket.get("evidence_pack_path", ""))
    if not pack.exists():
        errors.append(f"evidence pack not found: {pack}")
    else:
        # Verify SHA256 matches actual file
        expected = ticket.get("evidence_pack_sha256", "")
        if len(expected) == 64:
            actual = hashlib.sha256(pack.read_bytes()).hexdigest()
            if actual != expected:
                errors.append(f"evidence_pack_sha256 mismatch: expected {expected[:16]}..., got {actual[:16]}...")
    return errors


def validate_gpt_reply(reply_path: str) -> dict:
    """Validate GPT reply file. Fail-closed if END_OF_GPT_RESPONSE missing."""
    fp = Path(reply_path)
    if not fp.exists():
        return {"valid": False, "error": f"reply file not found: {reply_path}"}
    content = fp.read_text(encoding="utf-8")
    if "END_OF_GPT_RESPONSE" not in content:
        return {"valid": False, "error": "missing END_OF_GPT_RESPONSE marker"}
    if "overall_judgment" not in content.lower():
        return {"valid": False, "error": "missing overall_judgment in GPT reply"}
    verdict = "accepted" if "overall_judgment: accepted" in content.lower() or "overall_judgment:accepted" in content.lower().replace(" ", "") else "blocked"
    return {"valid": True, "verdict": verdict, "size": len(content)}


def all_tickets() -> list[dict]:
    """List all tickets sorted by created_at."""
    QUEUE_DIR.mkdir(parents=True, exist_ok=True)
    tickets = []
    for fp in sorted(QUEUE_DIR.glob("*.json")):
        try:
            tickets.append(json.loads(fp.read_text(encoding="utf-8")))
        except json.JSONDecodeError:
            pass
    tickets.sort(key=lambda t: t.get("created_at", ""))
    return tickets


def active_tickets() -> list[dict]:
    return [t for t in all_tickets() if t.get("status") in ACTIVE_STATES]


def pending_tickets() -> list[dict]:
    return [t for t in all_tickets() if t.get("status") == "queued"]


def create_ticket(task_id: str, evidence_pack_path: str, notes: str = "") -> dict:
    """Create a new review ticket. Multiple tickets can be queued."""
    pack_path = Path(evidence_pack_path)
    if not pack_path.exists():
        print(f"ERROR: evidence pack not found: {evidence_pack_path}")
        sys.exit(1)

    sha = hashlib.sha256(pack_path.read_bytes()).hexdigest()
    ticket_id = f"REVIEW-{task_id}"
    existing = [t for t in all_tickets() if t["ticket_id"] == ticket_id]
    if existing:
        ticket_id = f"REVIEW-{task_id}-R{len(existing)+1}"

    ticket = {
        "ticket_id": ticket_id,
        "task_id": task_id,
        "status": "queued",
        "evidence_pack_path": str(pack_path.resolve()),
        "evidence_pack_sha256": sha,
        "reviewer": "gpt",
        "created_at": _now(),
        "round": 1,
        "notes": notes,
    }

    QUEUE_DIR.mkdir(parents=True, exist_ok=True)
    (QUEUE_DIR / f"{ticket_id}.json").write_text(json.dumps(ticket, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"CREATED: {ticket_id} (status=queued)")
    return ticket


def submit_ticket(ticket_id: str, conversation_url: str) -> dict:
    """Mark ticket as submitted to GPT."""
    ticket = _load_ticket(ticket_id)
    if ticket["status"] != "queued":
        print(f"ERROR: ticket {ticket_id} is {ticket['status']}, expected queued")
        sys.exit(1)

    active = [t for t in active_tickets() if t["ticket_id"] != ticket_id]
    if len(active) >= MAX_ACTIVE:
        print(f"ERROR: another ticket is already active: {active[0]['ticket_id']}")
        sys.exit(1)

    ticket["status"] = "submitted"
    ticket["submitted_at"] = _now()
    ticket["submission_target"] = conversation_url
    _save_ticket(ticket)
    print(f"SUBMITTED: {ticket_id} → {conversation_url}")
    return ticket


def record_gpt_reply(ticket_id: str, verdict: str, reply_path: str, blocker_issues: list = None) -> dict:
    """Record GPT's response. verdict must be 'accepted' or 'blocked'."""
    ticket = _load_ticket(ticket_id)
    if ticket["status"] not in ("submitted", "gpt_replied"):
        print(f"ERROR: ticket {ticket_id} is {ticket['status']}, expected submitted/gpt_replied")
        sys.exit(1)

    reply_file = Path(reply_path)
    if not reply_file.exists():
        print(f"ERROR: reply file not found: {reply_path}")
        sys.exit(1)

    ticket["status"] = "gpt_replied"
    ticket["gpt_replied_at"] = _now()
    ticket["gpt_verdict"] = verdict
    ticket["gpt_reply_path"] = str(reply_file.resolve())
    ticket["gpt_reply_sha256"] = hashlib.sha256(reply_file.read_bytes()).hexdigest()
    if blocker_issues:
        ticket["blocking_issues"] = blocker_issues
    ticket["round"] = ticket.get("round", 1)
    _save_ticket(ticket)
    print(f"GPT REPLIED: {ticket_id} verdict={verdict}")
    return ticket


def accept_ticket(ticket_id: str) -> dict:
    """Mark ticket as accepted (GPT accepted, ready for binding)."""
    ticket = _load_ticket(ticket_id)
    if ticket["status"] != "gpt_replied":
        print(f"ERROR: ticket {ticket_id} is {ticket['status']}, expected gpt_replied")
        sys.exit(1)
    if ticket.get("gpt_verdict") != "accepted":
        print(f"ERROR: GPT verdict is {ticket.get('gpt_verdict')}, cannot accept")
        sys.exit(1)

    ticket["status"] = "accepted"
    _save_ticket(ticket)
    print(f"ACCEPTED: {ticket_id}")
    return ticket


def close_ticket(ticket_id: str) -> dict:
    """Close ticket after binding."""
    ticket = _load_ticket(ticket_id)
    if ticket["status"] not in ("accepted",):
        print(f"ERROR: ticket {ticket_id} is {ticket['status']}, expected accepted")
        sys.exit(1)

    ticket["status"] = "closed"
    ticket["closed_at"] = _now()
    _save_ticket(ticket)
    print(f"CLOSED: {ticket_id}")
    return ticket


def queue_status() -> dict:
    """Return current queue status."""
    tickets = all_tickets()
    return {
        "total": len(tickets),
        "active": len(active_tickets()),
        "pending": len(pending_tickets()),
        "by_status": {s: len([t for t in tickets if t["status"] == s]) for s in STATES},
        "tickets": [
            {"ticket_id": t["ticket_id"], "task_id": t["task_id"], "status": t["status"]}
            for t in tickets
        ],
    }


def _load_ticket(ticket_id: str) -> dict:
    fp = QUEUE_DIR / f"{ticket_id}.json"
    if not fp.exists():
        print(f"ERROR: ticket not found: {ticket_id}")
        sys.exit(1)
    return json.loads(fp.read_text(encoding="utf-8"))


def _save_ticket(ticket: dict):
    QUEUE_DIR.mkdir(parents=True, exist_ok=True)
    (QUEUE_DIR / f"{ticket['ticket_id']}.json").write_text(
        json.dumps(ticket, indent=2, ensure_ascii=False), encoding="utf-8"
    )


# ── CLI ────────────────────────────────────────────────────────────
def main():
    if len(sys.argv) < 2:
        print("Usage: review_queue.py <create|submit|reply|accept|close|status> [args...]")
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "status":
        print(json.dumps(queue_status(), indent=2, ensure_ascii=False))
    elif cmd == "create":
        if len(sys.argv) < 4:
            print("Usage: review_queue.py create <task_id> <evidence_pack_path> [notes]")
            sys.exit(1)
        create_ticket(sys.argv[2], sys.argv[3], sys.argv[4] if len(sys.argv) > 4 else "")
    elif cmd == "submit":
        if len(sys.argv) < 4:
            print("Usage: review_queue.py submit <ticket_id> <conversation_url>")
            sys.exit(1)
        submit_ticket(sys.argv[2], sys.argv[3])
    elif cmd == "reply":
        if len(sys.argv) < 5:
            print("Usage: review_queue.py reply <ticket_id> <verdict> <reply_path>")
            sys.exit(1)
        record_gpt_reply(sys.argv[2], sys.argv[3], sys.argv[4])
    elif cmd == "accept":
        if len(sys.argv) < 3:
            print("Usage: review_queue.py accept <ticket_id>")
            sys.exit(1)
        accept_ticket(sys.argv[2])
    elif cmd == "close":
        if len(sys.argv) < 3:
            print("Usage: review_queue.py close <ticket_id>")
            sys.exit(1)
        close_ticket(sys.argv[2])
    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)


if __name__ == "__main__":
    main()
