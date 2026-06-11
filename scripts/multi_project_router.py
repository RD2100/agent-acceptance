#!/usr/bin/env python3
"""Multi-Project Task Router v2 — dispatches tasks via shared CDP + tab target.

All projects share a single Chrome instance (one CDP endpoint).
Isolation is through **distinct ChatGPT conversation IDs** and
**tab-level target resolution** (v2 architecture).

Given a task with a target project_id, the router:
1. Looks up the project in the global registry
2. Reads the project's CONVERSATION_BINDING.json to find the active agent
3. Checks the shared CDP connection is live
4. Resolves the exact tab target via CDP /json page list
5. Returns the dispatch target (cdp_endpoint, conversation_id, chat_url, target_id)

This does NOT actually send messages — it resolves WHERE to send them.
The actual CDP message delivery navigates to the correct conversation tab.
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SCRIPTS = REPO / "scripts"
sys.path.insert(0, str(SCRIPTS))

# Import canonical tab resolver (v2 architecture requirement)
from tab_target_resolver import (  # noqa: E402
    resolve_tab_target as _canonical_resolve_tab_target,
    list_cdp_pages as _canonical_list_cdp_pages,
    validate_cdp_endpoint as _canonical_validate_cdp_endpoint,
)

REGISTRY_PATH = REPO / ".agent" / "PROJECT_REGISTRY.json"


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def validate_cdp_endpoint(endpoint: str) -> tuple[bool, str | None]:
    """Validate CDP endpoint — delegates to canonical implementation in tab_target_resolver."""
    return _canonical_validate_cdp_endpoint(endpoint)


def _check_cdp(endpoint: str) -> bool:
    """Check if a CDP endpoint is reachable (localhost only, 3s timeout)."""
    valid, _ = validate_cdp_endpoint(endpoint)
    if not valid:
        return False
    try:
        with urllib.request.urlopen(f"{endpoint}/json/version", timeout=3) as resp:
            return resp.status == 200
    except Exception:
        return False


def load_registry() -> dict:
    """Load global project registry."""
    if REGISTRY_PATH.exists():
        return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    return {"projects": {}}


def load_binding(project_root: Path) -> dict:
    """Load a project's CONVERSATION_BINDING.json."""
    binding_path = project_root / ".agent" / "CONVERSATION_BINDING.json"
    if not binding_path.exists():
        return {}
    return json.loads(binding_path.read_text(encoding="utf-8"))


# ── Router Core ────────────────────────────────────────────────────────


def resolve_target(project_id: str, project_root: str | None = None) -> dict:
    """Resolve the dispatch target for a given project (v2 with tab target).

    Returns a structured dict with all info needed to dispatch a task:
    - cdp_endpoint  (shared Chrome — same for all projects)
    - conversation_id  (unique per project — the isolation mechanism)
    - chat_url  (the URL to navigate to in the shared Chrome)
    - target_id  (the CDP page target identifier — v2)
    - target_url  (the exact page URL at resolution time — v2)
    - agent_id / agent_role
    - binding_status
    - capture_policy
    """
    registry = load_registry()
    project = registry.get("projects", {}).get(project_id)

    if not project:
        return {
            "project_id": project_id,
            "resolved": False,
            "error": f"Project '{project_id}' not found in registry",
        }

    # Shared CDP endpoint for all projects (F10: fail explicitly if missing)
    cdp_endpoint = registry.get("shared_cdp_endpoint")
    if not cdp_endpoint:
        return {
            "project_id": project_id,
            "resolved": False,
            "error": "shared_cdp_endpoint missing from PROJECT_REGISTRY.json",
        }
    cdp_active = _check_cdp(cdp_endpoint)

    # Fetch CDP page list using canonical resolver (v2)
    cdp_pages = _canonical_list_cdp_pages(cdp_endpoint) if cdp_active else []

    # Find the project's binding file
    root = Path(project_root) if project_root else Path(project.get("project_root", "."))
    binding = load_binding(root)

    if not binding:
        return {
            "project_id": project_id,
            "resolved": False,
            "error": f"CONVERSATION_BINDING.json not found at {root / '.agent'}",
            "cdp_endpoint": cdp_endpoint,
            "cdp_active": cdp_active,
        }

    # Find first active agent
    active_agents = [
        b for b in binding.get("bindings", [])
        if b.get("binding_status") == "active"
    ]

    if not active_agents:
        return {
            "project_id": project_id,
            "resolved": False,
            "error": "No active agent found in binding",
            "cdp_endpoint": cdp_endpoint,
            "cdp_active": cdp_active,
            "binding_count": len(binding.get("bindings", [])),
        }

    agent = active_agents[0]
    chat_url = agent.get("chat_url")

    # Resolve tab target using canonical resolver (v2, C-004: always delegate)
    tab_result = _canonical_resolve_tab_target(chat_url, cdp_pages)

    return {
        "project_id": project_id,
        "resolved": True,
        "cdp_endpoint": cdp_endpoint,
        "cdp_active": cdp_active,
        "conversation_id": agent.get("conversation_id"),
        "chat_url": chat_url,
        "target_id": tab_result.get("target_id"),
        "target_url": tab_result.get("target_url"),
        "tab_match_status": tab_result.get("match_status"),
        "agent_id": agent.get("agent_id"),
        "agent_role": agent.get("role"),
        "binding_status": agent.get("binding_status"),
        "capture_policy": binding.get("capture_policy", agent.get("capture_policy")),
        "resolved_at": _utc_now(),
    }


def resolve_all() -> list[dict]:
    """Resolve targets for all registered projects."""
    registry = load_registry()
    results = []
    for project_id, info in registry.get("projects", {}).items():
        root = info.get("project_root")
        results.append(resolve_target(project_id, root))
    return results


# ── Dispatch Packet Builder (v2) ──────────────────────────────────────────


def build_dispatch_packet(
    target: dict,
    task_spec: dict,
    message_text: str,
    dispatch_mode: str = "dry_run",
) -> dict:
    """Build a v2 dispatch packet ready for CDP submission.

    v2 packet includes tab target resolution, capture policy, and
    isolation model metadata.

    FAIL-CLOSED: If target_id is missing or tab_match_status is not
    exact_match, the packet is NOT dispatchable. This enforces the
    v2 architecture rule: "No dispatch without tab target_id resolution".

    Args:
        target: Resolved target from resolve_target()
        task_spec: Task specification dict
        message_text: The message to send
        dispatch_mode: 'dry_run' or 'human_gated_live'
    """
    if not target.get("resolved"):
        return {"dispatchable": False, "error": target.get("error")}

    # ── v2 FAIL-CLOSED gates ──────────────────────────────────────────
    tab_status = target.get("tab_match_status")
    target_id = target.get("target_id")
    target_url = target.get("target_url")

    if tab_status != "exact_match":
        return {
            "dispatchable": False,
            "blocked_reason": "tab_match_status_not_exact",
            "tab_match_status": tab_status,
            "target_id": target_id,
            "error": f"Cannot dispatch: tab_match_status={tab_status!r} (expected exact_match)",
        }

    if not target_id:
        return {
            "dispatchable": False,
            "blocked_reason": "missing_target_id",
            "tab_match_status": tab_status,
            "error": "Cannot dispatch: target_id is missing",
        }

    if not target_url:
        return {
            "dispatchable": False,
            "blocked_reason": "missing_target_url",
            "tab_match_status": tab_status,
            "target_id": target_id,
            "error": "Cannot dispatch: target_url is missing",
        }

    # ── All gates passed — build packet ─────────────────────────────

    # Extract capture policy from target
    capture_policy = target.get("capture_policy", {})
    if isinstance(capture_policy, dict):
        policy_dict = capture_policy
    else:
        policy_dict = {}

    return {
        # Core dispatch fields
        "dispatchable": True,
        "project_id": target["project_id"],
        "cdp_endpoint": target["cdp_endpoint"],
        "cdp_active": target["cdp_active"],
        "conversation_id": target["conversation_id"],
        "chat_url": target["chat_url"],
        "agent_id": target["agent_id"],
        "agent_role": target["agent_role"],
        # v2: Tab target resolution
        "target_id": target.get("target_id"),
        "target_url": target.get("target_url"),
        "tab_match_status": target.get("tab_match_status"),
        # v2: Capture policy (mandatory)
        "capture_policy": {
            "must_match_run_id": policy_dict.get("must_match_run_id", True),
            "must_match_task_id": policy_dict.get("must_match_task_id", True),
            "must_include_end_marker": policy_dict.get("must_include_end_marker", True),
            "forbid_last_message_only_capture": policy_dict.get(
                "forbid_last_message_only_capture", True
            ),
        },
        # v2: Expected response identifiers
        "expected_run_id": task_spec.get("run_id"),
        "expected_task_id": task_spec.get("task_id"),
        "expected_end_marker": "END_OF_GPT_RESPONSE",
        "forbid_last_message_only_capture": True,
        # v2: Architecture metadata
        "dispatch_mode": dispatch_mode,
        "cdp_mode": "shared_single_chrome",
        "isolation_model": "conversation_target_bound",
        # Task and message
        "task_spec": task_spec,
        "message_text": message_text,
        "message_length": len(message_text),
        "built_at": _utc_now(),
    }


# ── Isolation Verification ────────────────────────────────────────────


def verify_isolation(targets: list[dict]) -> dict:
    """Verify that multiple project targets are properly isolated.

    In the shared-Chrome architecture, isolation is through **distinct
    conversation IDs**.  Port and profile collisions are expected because
    all projects share one Chrome instance.

    Checks:
    - No two projects share the same conversation_id
    """
    issues = []
    conv_ids = {}

    for t in targets:
        if not t.get("resolved"):
            continue

        pid = t["project_id"]

        # Check conversation isolation — the only isolation mechanism
        conv = t.get("conversation_id")
        if conv:
            if conv in conv_ids:
                issues.append(
                    f"Conversation collision: {pid} and {conv_ids[conv]} share {conv}"
                )
            conv_ids[conv] = pid

    return {
        "isolated": len(issues) == 0,
        "total_projects": len([t for t in targets if t.get("resolved")]),
        "unique_conversations": len(conv_ids),
        "issues": issues,
        "checked_at": _utc_now(),
    }


# ── CLI ────────────────────────────────────────────────────────────────


def main() -> None:
    parser = argparse.ArgumentParser(description="Multi-Project Task Router")
    sub = parser.add_subparsers(dest="command")

    p_resolve = sub.add_parser("resolve", help="Resolve dispatch target")
    p_resolve.add_argument("--project", required=True, help="Project ID")
    p_resolve.add_argument("--project-root", default=None)

    sub.add_parser("resolve-all", help="Resolve all project targets")

    sub.add_parser("verify-isolation", help="Verify multi-project isolation")

    args = parser.parse_args()

    if args.command == "resolve":
        result = resolve_target(args.project, args.project_root)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        sys.exit(0 if result.get("resolved") else 1)

    elif args.command == "resolve-all":
        results = resolve_all()
        print(json.dumps(results, indent=2, ensure_ascii=False))
        resolved = sum(1 for r in results if r.get("resolved"))
        print(f"\n{resolved}/{len(results)} resolved")

    elif args.command == "verify-isolation":
        targets = resolve_all()
        result = verify_isolation(targets)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        sys.exit(0 if result["isolated"] else 1)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
