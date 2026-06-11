#!/usr/bin/env python3
"""paper_auth_gate.py — Human authorization gate for paper pilot. Fail-closed until authorized."""
import json, sys, hashlib
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
GATE_FILE = REPO / ".ai" / "paper_authorization.json"

def check():
    if not GATE_FILE.exists():
        return {"authorized": False, "reason": "no authorization file", "action": "create .ai/paper_authorization.json with valid token"}
    try:
        gate = json.loads(GATE_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"authorized": False, "reason": "invalid authorization JSON"}
    if not gate.get("authorized"):
        return {"authorized": False, "reason": "authorization set to false"}
    if gate.get("expires_at", "") < datetime.now(timezone.utc).isoformat():
        return {"authorized": False, "reason": "authorization expired"}
    if not gate.get("token") or len(gate.get("token", "")) < 16:
        return {"authorized": False, "reason": "invalid authorization token"}
    return {"authorized": True, "reason": gate.get("scope", "full pilot"), "expires": gate.get("expires_at")}

def main():
    result = check()
    result["checked_at"] = datetime.now(timezone.utc).isoformat()
    print(json.dumps(result, indent=2, ensure_ascii=False))
    if not result["authorized"]:
        print("\nGATE CLOSED: real-paper pilot is NOT authorized.")
        print("To authorize: create .ai/paper_authorization.json with {\"authorized\": true, \"token\": \"...\", \"expires_at\": \"...\"}")
    sys.exit(0 if result["authorized"] else 1)

if __name__ == "__main__":
    main()
