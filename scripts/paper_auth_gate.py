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
    scope = gate.get("scope", "")
    allowed_scopes = {"synthetic_only", "metadata_only", "bounded_pilot", "dry_run"}
    forbidden_scopes = {"full pilot", "real_paper", "real_paper_full_text", "external_upload", "live_cdp", "memory_write"}
    if scope in forbidden_scopes:
        return {"authorized": False, "reason": f"scope '{scope}' is forbidden"}
    if scope not in allowed_scopes:
        return {"authorized": False, "reason": f"scope '{scope}' not in allowed scopes: {sorted(allowed_scopes)}"}
    return {"authorized": True, "reason": f"scope={scope}", "expires": gate.get("expires_at")}

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
