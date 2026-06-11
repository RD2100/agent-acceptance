#!/usr/bin/env python3
"""Tab Target Resolver — v2 Shared CDP tab-level target resolution.

In the shared-CDP architecture, all projects share ONE Chrome instance.
Each project is bound to a distinct ChatGPT conversation URL.

This module resolves the **exact browser tab** (CDP page target) for each
active project by matching the project's chat_url against the Chrome
DevTools Protocol /json page list.

Rules (v2 baseline):
  1. Exact conversation URL match to a CDP page target
  2. No match -> human_required (tab not found)
  3. Multiple matches -> blocked (ambiguous target)
  4. Non-ChatGPT pages cannot be bound
  5. No fallback to "last tab" or "current active tab"
  6. target_id MUST be included in dispatch packet and capture evidence

Usage:
  python scripts/tab_target_resolver.py
  python scripts/tab_target_resolver.py --project agent-acceptance
  python scripts/tab_target_resolver.py --cdp-endpoint http://localhost:9222
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from urllib.parse import urlparse

REPO = Path(__file__).resolve().parent.parent
SCRIPTS = REPO / "scripts"
sys.path.insert(0, str(SCRIPTS))

REGISTRY_PATH = REPO / ".agent" / "PROJECT_REGISTRY.json"
DEFAULT_CDP_ENDPOINT = "http://localhost:9222"


# ── Utilities ─────────────────────────────────────────────────────────


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


ALLOWED_CDP_PORTS = range(9222, 9232)  # 9222-9231 (10 ports for 10-project plan)


def validate_cdp_endpoint(endpoint: str) -> tuple[bool, str | None]:
    """Validate that a CDP endpoint is safe (localhost only, known port range).

    Only localhost, 127.0.0.1, and ::1 are allowed to prevent accidental
    connection to remote Chrome instances which could leak CDP credentials.
    Port must be in the known CDP range (9222-9231) to avoid probing
    unrelated local services. Both http and https schemes are accepted.

    Returns (is_valid, error_reason).
    """
    try:
        parsed = urlparse(endpoint)
    except Exception:
        return False, "cdp_endpoint_parse_failed"
    if parsed.scheme not in ("http", "https"):
        return False, "cdp_endpoint_must_use_http_or_https"
    if parsed.hostname not in ("localhost", "127.0.0.1", "::1"):
        return False, "cdp_endpoint_must_be_localhost"
    if parsed.port is None:
        return False, "cdp_endpoint_missing_port"
    if parsed.port not in ALLOWED_CDP_PORTS:
        return False, "cdp_endpoint_port_out_of_range"
    return True, None


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


# ── CDP Page Discovery ────────────────────────────────────────────────


def list_cdp_pages(cdp_endpoint: str = DEFAULT_CDP_ENDPOINT) -> list[dict]:
    """Fetch the CDP /json page list from the shared Chrome instance.

    Returns a list of page target dicts from Chrome DevTools Protocol,
    each containing: id, type, title, url, webSocketDebuggerUrl, etc.

    Returns an empty list if the endpoint is unreachable or not localhost.
    """
    valid, _ = validate_cdp_endpoint(cdp_endpoint)
    if not valid:
        return []
    try:
        with urllib.request.urlopen(f"{cdp_endpoint}/json", timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            # Filter to "page" type targets only (exclude service workers, etc.)
            return [t for t in data if t.get("type") == "page"]
    except Exception:
        return []


CHATGPT_DOMAINS = {"chatgpt.com", "chat.openai.com"}


def is_chatgpt_page(page: dict) -> bool:
    """Check if a CDP page target is a ChatGPT page (hostname-based)."""
    url = page.get("url", "")
    try:
        parsed = urlparse(url)
        return parsed.hostname in CHATGPT_DOMAINS
    except Exception:
        return False


def is_chatgpt_conversation_page(page: dict) -> bool:
    """Check if a CDP page target is a ChatGPT conversation page."""
    url = page.get("url", "")
    try:
        parsed = urlparse(url)
        if parsed.hostname not in CHATGPT_DOMAINS:
            return False
        return parsed.path.startswith("/c/")
    except Exception:
        return False


# ── Target Resolution ─────────────────────────────────────────────────


def _normalize_url(url: str) -> str:
    """Normalize a URL for matching: strip query params, fragments, then trailing slash."""
    return url.split("?")[0].split("#")[0].rstrip("/")


def resolve_tab_target(
    chat_url: str,
    cdp_pages: list[dict],
) -> dict:
    """Resolve a single conversation URL to an exact CDP tab target.

    Automatically filters cdp_pages to ChatGPT conversation pages only.
    Non-ChatGPT pages are excluded from matching (security: F8/F9).

    Args:
        chat_url: The project's bound chat_url (e.g. https://chatgpt.com/c/abc123)
        cdp_pages: The CDP /json page list (may include non-ChatGPT pages)

    Returns:
        A structured dict with target_id, target_url, match_status, and issues.
    """
    if not chat_url:
        return {
            "target_id": None,
            "target_url": None,
            "match_status": "no_chat_url",
            "issues": ["No chat_url bound for this project"],
        }

    if not cdp_pages:
        return {
            "target_id": None,
            "target_url": None,
            "match_status": "cdp_unreachable",
            "issues": ["CDP page list is empty or endpoint unreachable"],
        }

    # Filter to ChatGPT conversation pages only (security: prevents non-ChatGPT match)
    chatgpt_pages = [p for p in cdp_pages if is_chatgpt_conversation_page(p)]

    # Structural validation: chat_url must be a ChatGPT conversation URL (F7)
    try:
        parsed_chat = urlparse(chat_url)
        if parsed_chat.hostname not in CHATGPT_DOMAINS:
            return {
                "target_id": None,
                "target_url": None,
                "match_status": "invalid_chat_url",
                "issues": [f"chat_url domain {parsed_chat.hostname!r} is not a known ChatGPT domain"],
            }
        if not parsed_chat.path.startswith("/c/"):
            return {
                "target_id": None,
                "target_url": None,
                "match_status": "invalid_chat_url",
                "issues": [f"chat_url path {parsed_chat.path!r} is not a conversation path (/c/...)"],
            }
    except Exception:
        return {
            "target_id": None,
            "target_url": None,
            "match_status": "invalid_chat_url",
            "issues": ["chat_url could not be parsed"],
        }

    # Normalize chat_url for matching (F6: strips fragments, query params, trailing slashes)
    normalized_chat = _normalize_url(chat_url)

    # Find matching pages
    matches = []
    for page in chatgpt_pages:
        page_url = page.get("url", "")
        normalized_page = _normalize_url(page_url)

        # Exact match on conversation URL
        if normalized_page == normalized_chat:
            matches.append(page)

    if len(matches) == 0:
        return {
            "target_id": None,
            "target_url": None,
            "match_status": "no_match",
            "issues": [
                f"No CDP tab found matching {chat_url}",
                "human_required: open this conversation URL in the shared Chrome",
            ],
        }

    if len(matches) > 1:
        # F5: Redact raw CDP target IDs — expose count only
        return {
            "target_id": None,
            "target_url": None,
            "match_status": "ambiguous",
            "issues": [
                f"Multiple CDP tabs ({len(matches)}) match {chat_url}",
                "blocked: cannot determine unique target",
            ],
        }

    # Exactly one match — success
    matched = matches[0]
    ws_url = matched.get("webSocketDebuggerUrl")
    return {
        "target_id": matched.get("id"),
        "target_url": matched.get("url"),
        "target_title": matched.get("title"),
        # Redact: expose presence only, never the full URL (security)
        "webSocketDebuggerUrl": "[REDACTED]" if ws_url else None,
        "has_webSocketDebuggerUrl": ws_url is not None,
        "match_status": "exact_match",
        "issues": [],
    }


# ── Batch Resolution ──────────────────────────────────────────────────


def resolve_all_targets(
    cdp_endpoint: str = DEFAULT_CDP_ENDPOINT,
) -> dict:
    """Resolve tab targets for ALL active projects in the registry.

    Returns a structured report with per-project resolution results.
    """
    registry = load_registry()
    projects = registry.get("projects", {})
    cdp_endpoint = registry.get("shared_cdp_endpoint", cdp_endpoint)

    # Fetch CDP page list once
    cdp_pages = list_cdp_pages(cdp_endpoint)
    cdp_healthy = len(cdp_pages) > 0

    # Only consider ChatGPT pages for matching
    chatgpt_pages = [p for p in cdp_pages if is_chatgpt_page(p)]

    results: list[dict] = []
    active_count = 0
    resolved_count = 0
    human_required_count = 0
    blocked_count = 0

    for project_id, info in projects.items():
        root = Path(info.get("project_root", "."))
        binding = load_binding(root)
        reg_status = info.get("binding_status", "unknown")

        # Only resolve active projects
        if reg_status != "active":
            results.append({
                "project_id": project_id,
                "binding_status": reg_status,
                "skip_reason": "not_active",
                "target_id": None,
                "match_status": "skipped",
            })
            continue

        active_count += 1

        # Find active agent in binding
        active_agents = [
            b for b in binding.get("bindings", [])
            if b.get("binding_status") == "active"
        ]

        if not active_agents:
            results.append({
                "project_id": project_id,
                "binding_status": reg_status,
                "target_id": None,
                "match_status": "no_active_agent",
                "issues": ["Registry says active but no active agent in binding"],
            })
            human_required_count += 1
            continue

        agent = active_agents[0]
        chat_url = agent.get("chat_url", "")
        conversation_id = agent.get("conversation_id", "")

        # Resolve tab target
        tab_result = resolve_tab_target(chat_url, chatgpt_pages)

        entry = {
            "project_id": project_id,
            "agent_id": agent.get("agent_id"),
            "agent_role": agent.get("role"),
            "binding_status": reg_status,
            "conversation_id": conversation_id,
            "chat_url": chat_url,
            "cdp_endpoint": cdp_endpoint,
            **tab_result,
        }
        results.append(entry)

        if tab_result["match_status"] == "exact_match":
            resolved_count += 1
        elif tab_result["match_status"] in ("no_match", "cdp_unreachable", "no_chat_url"):
            human_required_count += 1
        elif tab_result["match_status"] == "ambiguous":
            blocked_count += 1

    return {
        "schema_version": "2.0.0",
        "task_id": "SHARED-CDP-TAB-TARGET-RESOLVER-A1",
        "generated_at": _utc_now(),
        "cdp_endpoint": cdp_endpoint,
        "cdp_healthy": cdp_healthy,
        "total_cdp_pages": len(cdp_pages),
        "chatgpt_pages": len(chatgpt_pages),
        "total_projects": len(projects),
        "active_projects": active_count,
        "resolved_targets": resolved_count,
        "human_required": human_required_count,
        "blocked": blocked_count,
        "results": results,
    }


def resolve_project_target(
    project_id: str,
    cdp_endpoint: str = DEFAULT_CDP_ENDPOINT,
) -> dict:
    """Resolve tab target for a single project."""
    registry = load_registry()
    projects = registry.get("projects", {})
    cdp_endpoint = registry.get("shared_cdp_endpoint", cdp_endpoint)

    info = projects.get(project_id)
    if not info:
        return {
            "project_id": project_id,
            "resolved": False,
            "error": f"Project '{project_id}' not found in registry",
        }

    root = Path(info.get("project_root", "."))
    binding = load_binding(root)

    # Fetch CDP pages
    cdp_pages = list_cdp_pages(cdp_endpoint)
    chatgpt_pages = [p for p in cdp_pages if is_chatgpt_page(p)]

    # Find active agent
    active_agents = [
        b for b in binding.get("bindings", [])
        if b.get("binding_status") == "active"
    ]

    if not active_agents:
        return {
            "project_id": project_id,
            "resolved": False,
            "cdp_endpoint": cdp_endpoint,
            "binding_status": info.get("binding_status"),
            "error": "No active agent in binding",
        }

    agent = active_agents[0]
    chat_url = agent.get("chat_url", "")

    tab_result = resolve_tab_target(chat_url, chatgpt_pages)

    resolved = tab_result["match_status"] == "exact_match"
    return {
        "project_id": project_id,
        "resolved": resolved,
        "agent_id": agent.get("agent_id"),
        "agent_role": agent.get("role"),
        "binding_status": info.get("binding_status"),
        "conversation_id": agent.get("conversation_id"),
        "chat_url": chat_url,
        "cdp_endpoint": cdp_endpoint,
        **tab_result,
    }


# ── CLI ───────────────────────────────────────────────────────────────


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Tab Target Resolver — v2 Shared CDP target resolution"
    )
    parser.add_argument(
        "--project",
        help="Resolve a single project (default: resolve all)",
    )
    parser.add_argument(
        "--cdp-endpoint",
        default=DEFAULT_CDP_ENDPOINT,
        help=f"CDP endpoint URL (default: {DEFAULT_CDP_ENDPOINT})",
    )
    args = parser.parse_args()

    if args.project:
        result = resolve_project_target(args.project, args.cdp_endpoint)
    else:
        result = resolve_all_targets(args.cdp_endpoint)

    print(json.dumps(result, indent=2, ensure_ascii=False))

    # Exit code: 0 = all resolved, 1 = issues found
    if args.project:
        sys.exit(0 if result.get("resolved") else 1)
    else:
        all_ok = (
            result.get("human_required", 0) == 0
            and result.get("blocked", 0) == 0
        )
        sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
