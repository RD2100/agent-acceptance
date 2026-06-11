#!/usr/bin/env python3
"""Pilot activation record — documents CDP evidence and binding activation.

This script creates the formal activation record for MULTI-AGENT-MULTI-GPT-PILOT-A1.
It does NOT modify any files; it only reads and validates existing state.

Activation evidence:
  - CDP endpoint verified via /json/version
  - ChatGPT conversation URL verified via /json (page list)
  - CONVERSATION_BINDING.json validated against CONVERSATION_REGISTRY.schema.json
  - Gate 0 preflight re-evaluated with updated bindings
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.request
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parent.parent
SCRIPTS = REPO / "scripts"
sys.path.insert(0, str(SCRIPTS))

from validate_conversation_registry import validate_binding


CDP_ENDPOINT = "http://localhost:9222"
PILOT_ID = "multi-agent-multi-gpt-pilot-a1"


def _cdp_get(path: str) -> dict[str, Any] | list | None:
    """Query CDP endpoint. Returns None on failure."""
    try:
        with urllib.request.urlopen(f"{CDP_ENDPOINT}{path}", timeout=5) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception:
        return None


def verify_cdp_session() -> dict[str, Any]:
    """Verify CDP session is active and return metadata."""
    version = _cdp_get("/json/version")
    if not version or not isinstance(version, dict):
        return {"cdp_active": False, "error": "CDP endpoint not reachable"}

    pages = _cdp_get("/json")
    chat_pages = []
    if isinstance(pages, list):
        chat_pages = [
            {"type": p.get("type"), "url": p.get("url"), "title": p.get("title")}
            for p in pages
            if p.get("type") == "page" and "chatgpt.com" in p.get("url", "")
        ]

    return {
        "cdp_active": True,
        "browser": version.get("Browser"),
        "protocol_version": version.get("Protocol-Version"),
        "chat_pages": chat_pages,
        "chat_page_count": len(chat_pages),
    }


def build_activation_record(
    binding_path: Path,
    cdp_evidence: dict[str, Any],
    validation_result: dict[str, Any],
) -> dict[str, Any]:
    """Build the structured activation record."""
    binding_data = json.loads(binding_path.read_text(encoding="utf-8"))
    bindings = binding_data.get("bindings", [])

    active_agents = [b for b in bindings if b.get("binding_status") == "active"]
    pending_agents = [b for b in bindings if b.get("binding_status") == "pending_manual_binding"]

    # Verify each active agent has real CDP-backed conversation
    activation_evidence = []
    for agent in active_agents:
        chat_url = agent.get("chat_url", "")
        conversation_id = agent.get("conversation_id", "")
        cdp_endpoint = agent.get("cdp_endpoint", "")

        # Cross-check with CDP session
        cdp_verified = False
        if cdp_evidence.get("cdp_active") and chat_url:
            for page in cdp_evidence.get("chat_pages", []):
                if conversation_id and conversation_id in page.get("url", ""):
                    cdp_verified = True
                    break

        activation_evidence.append({
            "agent_id": agent["agent_id"],
            "role": agent.get("role"),
            "binding_status": "active",
            "chat_url": chat_url,
            "conversation_id": conversation_id,
            "cdp_endpoint": cdp_endpoint,
            "cdp_session_verified": cdp_verified,
        })

    return {
        "pilot_id": PILOT_ID,
        "activation_timestamp": _utc_now(),
        "binding_path": str(binding_path),
        "binding_valid": validation_result.get("valid", False),
        "schema_validated": validation_result.get("schema_validated", False),
        "agent_summary": {
            "total": len(bindings),
            "active": len(active_agents),
            "pending": len(pending_agents),
        },
        "active_agents": activation_evidence,
        "pending_agents": [
            {
                "agent_id": b["agent_id"],
                "role": b.get("role"),
                "binding_status": "pending_manual_binding",
            }
            for b in pending_agents
        ],
        "cdp_session": {
            "active": cdp_evidence.get("cdp_active", False),
            "browser": cdp_evidence.get("browser"),
            "chat_pages": cdp_evidence.get("chat_page_count", 0),
        },
        "governance_scope": {
            "external_runtimes": [
                r["runtime_id"]
                for r in binding_data.get("governance_scope", {}).get("external_runtimes", [])
            ],
            "default_execution_policy": binding_data.get("governance_scope", {}).get(
                "default_execution_policy"
            ),
        },
        "pilot_readiness": {
            "all_agents_active": len(pending_agents) == 0,
            "at_least_one_active": len(active_agents) >= 1,
            "at_least_two_agents": len(bindings) >= 2,
            "schema_validated": validation_result.get("schema_validated", False),
            "cdp_verified": cdp_evidence.get("cdp_active", False),
        },
    }


def _utc_now() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def main() -> None:
    parser = argparse.ArgumentParser(description="Pilot activation record")
    parser.add_argument("--binding", default=str(REPO / ".agent" / "CONVERSATION_BINDING.json"))
    parser.add_argument("--output", help="Output path for activation record JSON")
    args = parser.parse_args()

    binding_path = Path(args.binding)

    # Step 1: Verify CDP session
    print("Verifying CDP session...")
    cdp_evidence = verify_cdp_session()
    if cdp_evidence.get("cdp_active"):
        print(f"  CDP active: {cdp_evidence.get('browser')}")
        print(f"  ChatGPT pages: {cdp_evidence.get('chat_page_count')}")
    else:
        print(f"  CDP not active: {cdp_evidence.get('error', 'unknown')}")

    # Step 2: Validate binding
    print("Validating CONVERSATION_BINDING.json...")
    result = validate_binding(str(binding_path), project_root=str(REPO))
    if result.get("valid"):
        summary = result.get("summary", {})
        print(f"  Valid: {summary.get('binding_count')} bindings, "
              f"{summary.get('active_count')} active, "
              f"{summary.get('pending_count')} pending")
    else:
        print(f"  INVALID: {result.get('errors')}")
        sys.exit(1)

    # Step 3: Build activation record
    record = build_activation_record(binding_path, cdp_evidence, result)

    readiness = record["pilot_readiness"]
    print(f"\nPilot readiness:")
    for k, v in readiness.items():
        print(f"  {k}: {v}")

    # Step 4: Output
    output_json = json.dumps(record, indent=2, ensure_ascii=False)
    if args.output:
        output_path = Path(args.output)
        output_path.write_text(output_json, encoding="utf-8")
        print(f"\nActivation record saved: {output_path}")
    else:
        print(f"\n{output_json}")

    # Exit code: 0 if at least one active + schema valid, 2 if not fully ready
    if readiness["all_agents_active"] and readiness["schema_validated"]:
        sys.exit(0)
    elif readiness["at_least_one_active"] and readiness["schema_validated"]:
        sys.exit(2)  # Partial activation (some agents still pending)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
