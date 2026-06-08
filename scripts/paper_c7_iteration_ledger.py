#!/usr/bin/env python3
"""
paper_c7_iteration_ledger.py — Track module-level issues across iteration rounds.
Prevents infinite loops: novelty guard, round budget, issue hash dedup.
"""
import json, hashlib, sys
from pathlib import Path
from datetime import datetime, timezone

REPO = Path(__file__).resolve().parent.parent
LEDGER_DIR = REPO / ".ai" / "module_ledger"
MAX_ROUNDS = 3

def _ledger_path(module_id: str) -> Path:
    LEDGER_DIR.mkdir(parents=True, exist_ok=True)
    return LEDGER_DIR / f"{module_id}.json"


def load(module_id: str) -> dict:
    fp = _ledger_path(module_id)
    if not fp.exists():
        return {"module_id": module_id, "rounds": [], "status": "new", "created_at": datetime.now(timezone.utc).isoformat()}
    return json.loads(fp.read_text(encoding="utf-8"))


def save(ledger: dict):
    _ledger_path(ledger["module_id"]).write_text(json.dumps(ledger, indent=2, ensure_ascii=False), encoding="utf-8")


def start_round(module_id: str, round_num: int, context: dict = None) -> dict:
    ledger = load(module_id)
    if ledger["status"] in ("accepted", "accepted_with_limitation", "blocked", "human_required"):
        return {"allowed": False, "reason": f"module already {ledger['status']}", "ledger": ledger}
    if round_num > MAX_ROUNDS:
        ledger["status"] = "human_required"
        ledger["stop_reason"] = f"exceeded {MAX_ROUNDS} rounds"
        save(ledger)
        return {"allowed": False, "reason": ledger["stop_reason"], "ledger": ledger}

    now = datetime.now(timezone.utc).isoformat()
    new_round = {"round": round_num, "started_at": now, "issues": [], "status": "in_progress"}
    ledger["rounds"].append(new_round)
    ledger["status"] = "in_progress"
    save(ledger)
    return {"allowed": True, "ledger": ledger}


def add_issue(module_id: str, round_num: int, issue: dict) -> dict:
    """Add issue with dedup check."""
    ledger = load(module_id)
    current_round = None
    for r in ledger["rounds"]:
        if r["round"] == round_num:
            current_round = r
            break
    if not current_round:
        return {"error": "round not found"}

    # Novelty check: same issue_id in any previous round?
    issue_id = issue.get("issue_id", "")
    for r in ledger["rounds"]:
        for i in r.get("issues", []):
            if i.get("issue_id") == issue_id and i.get("status") in ("resolved", "accepted_limitation"):
                return {"duplicate": True, "reason": f"issue {issue_id} already resolved in round {r['round']}"}

    current_round.setdefault("issues", []).append(issue)
    save(ledger)
    return {"ok": True}


def close_round(module_id: str, round_num: int, verdict: str, reason: str = "") -> dict:
    """Close a round with verdict. Check loop hash for dedup."""
    ledger = load(module_id)
    for r in ledger["rounds"]:
        if r["round"] == round_num:
            r["status"] = verdict
            r["ended_at"] = datetime.now(timezone.utc).isoformat()
            r["verdict_reason"] = reason

            # Loop hash check
            prev_issues = []
            for pr in ledger["rounds"]:
                for pi in pr.get("issues", []):
                    prev_issues.append(f"{pi.get('issue_id','')}:{pi.get('severity','')}")
            current_hash = hashlib.sha256('\n'.join(sorted(prev_issues)).encode()).hexdigest()
            if ledger.get("last_issue_hash") == current_hash:
                ledger["status"] = "human_required"
                ledger["stop_reason"] = "loop detected: same issue set as previous round"
            ledger["last_issue_hash"] = current_hash

            # P0 check
            p0_issues = [i for i in r.get("issues", []) if i.get("severity") == "P0"]
            if p0_issues:
                ledger["status"] = "blocked"
                ledger["stop_reason"] = f"P0 issues unresolved: {[i['issue_id'] for i in p0_issues]}"
            elif verdict == "pass":
                ledger["status"] = "accepted"
            elif verdict == "pass_with_limitation":
                ledger["status"] = "accepted_with_limitation"

            save(ledger)
            return {"ok": True, "ledger": ledger}

    return {"error": "round not found"}


def module_status(module_id: str) -> dict:
    ledger = load(module_id)
    total_issues = sum(len(r.get("issues", [])) for r in ledger["rounds"])
    return {
        "module_id": module_id,
        "status": ledger["status"],
        "rounds_completed": len([r for r in ledger["rounds"] if r.get("status") not in ("in_progress",)]),
        "total_issues": total_issues,
        "max_rounds": MAX_ROUNDS,
        "remaining_rounds": MAX_ROUNDS - len(ledger["rounds"]),
    }
