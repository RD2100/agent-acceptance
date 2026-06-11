#!/usr/bin/env python3
"""Lazy Launch Manager — on-demand Chrome CDP instance management.

Provides lazy-launch semantics for multi-project CDP isolation:
- Only launch Chrome when a project actually needs it
- Enforce resource policy limits (max warm instances, max active reviews)
- Track project lifecycle: registered -> warm -> active -> stale

Usage:
  python lazy_launch_manager.py status
  python lazy_launch_manager.py launch --project <project_id>
  python lazy_launch_manager.py health-check
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Reuse constants and functions from the existing launcher
REPO = Path(__file__).resolve().parent.parent
REGISTRY_PATH = REPO / ".agent" / "PROJECT_REGISTRY.json"
POLICY_PATH = REPO / ".agent" / "MULTI_PROJECT_RESOURCE_POLICY.json"

# ── Status Constants ──────────────────────────────────────────────────

STATUS_REGISTERED = "registered"   # In registry but Chrome not started
STATUS_WARM = "warm"               # Chrome running, no GPT review active
STATUS_ACTIVE = "active"           # Chrome running and GPT review in progress
STATUS_STALE = "stale"             # Chrome was running but /json/version not responding
STATUS_NOT_STARTED = "not_started"  # Alias for registered (used in health-check)


# ── Utility ───────────────────────────────────────────────────────────


def _utc_now() -> str:
    """Return current UTC time as ISO-8601 string."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _get_version(port: int) -> dict | None:
    """Get CDP version info from a port, or None if unreachable."""
    try:
        with urllib.request.urlopen(
            f"http://localhost:{port}/json/version", timeout=3
        ) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception:
        return None


def _get_pages(port: int) -> list[dict]:
    """Get list of open pages (tabs) from CDP, or empty list on failure."""
    try:
        with urllib.request.urlopen(
            f"http://localhost:{port}/json", timeout=3
        ) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data if isinstance(data, list) else []
    except Exception:
        return []


def _has_gpt_review(pages: list[dict]) -> bool:
    """Check whether any open page indicates an active GPT review session."""
    for page in pages:
        if not isinstance(page, dict):
            continue
        url = page.get("url", "")
        if "chatgpt.com" in url or "chat.openai.com" in url:
            return True
    return False


# ── Registry Access ───────────────────────────────────────────────────


def load_registry() -> dict:
    """Load the global project registry."""
    if REGISTRY_PATH.exists():
        return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    return {
        "schema_version": "1.0.0",
        "awsp_version": "1.3.0",
        "generated_at": _utc_now(),
        "projects": {},
    }


def save_registry(registry: dict) -> None:
    """Save the global project registry."""
    REGISTRY_PATH.parent.mkdir(parents=True, exist_ok=True)
    registry["updated_at"] = _utc_now()
    REGISTRY_PATH.write_text(
        json.dumps(registry, indent=2, ensure_ascii=False), encoding="utf-8"
    )


# ── Resource Policy ───────────────────────────────────────────────────


def load_resource_policy() -> dict:
    """Load MULTI_PROJECT_RESOURCE_POLICY.json.

    Returns the parsed policy dict.  Falls back to sensible defaults
    if the file is missing.
    """
    if POLICY_PATH.exists():
        return json.loads(POLICY_PATH.read_text(encoding="utf-8"))
    return {
        "schema_version": "1.0.0",
        "max_warm_cdp_instances": 4,
        "max_active_gpt_reviews": 2,
        "lazy_launch": True,
    }


# ── Core Functions ────────────────────────────────────────────────────


def _get_shared_port() -> int:
    """Get the shared CDP port from the v2 registry."""
    registry = load_registry()
    return registry.get("shared_cdp_port", 9222)


def count_warm_instances() -> int:
    """Count whether the shared Chrome instance is running.

    In v2 (shared Chrome), this returns 0 or 1 — there is only one Chrome.
    """
    port = _get_shared_port()
    if _get_version(port) is not None:
        return 1
    return 0


def get_project_status(project_id: str) -> dict:
    """Check the lifecycle status of a project's CDP instance.

    Returns a dict with keys:
      - project_id: str
      - status: one of registered, warm, active, stale
      - port: int
      - cdp_responsive: bool
      - gpt_review_active: bool
      - detail: str  (human-readable explanation)
    """
    registry = load_registry()
    projects = registry.get("projects", {})

    if project_id not in projects:
        return {
            "project_id": project_id,
            "status": STATUS_REGISTERED,
            "port": 0,
            "cdp_responsive": False,
            "gpt_review_active": False,
            "detail": "Project not found in registry",
        }

    info = projects[project_id]
    port = _get_shared_port()
    binding_status = info.get("binding_status", "")

    # If binding_status is explicitly 'stale', honour that
    if binding_status == STATUS_STALE:
        return {
            "project_id": project_id,
            "status": STATUS_STALE,
            "port": port,
            "cdp_responsive": False,
            "gpt_review_active": False,
            "detail": "Marked stale in registry",
        }

    # Check CDP responsiveness
    version = _get_version(port)
    cdp_responsive = version is not None

    if not cdp_responsive:
        # Not responding — was it ever started?
        # If binding_status implies it was running before, it's stale
        if binding_status in ("active", "warm"):
            return {
                "project_id": project_id,
                "status": STATUS_STALE,
                "port": port,
                "cdp_responsive": False,
                "gpt_review_active": False,
                "detail": "Chrome was running but /json/version not responding",
            }
        # Otherwise just registered / never started
        return {
            "project_id": project_id,
            "status": STATUS_REGISTERED,
            "port": port,
            "cdp_responsive": False,
            "gpt_review_active": False,
            "detail": "Registered but Chrome not started",
        }

    # CDP is responsive — check for active GPT review
    pages = _get_pages(port)
    gpt_active = _has_gpt_review(pages)

    if gpt_active:
        status = STATUS_ACTIVE
        detail = "Chrome running and GPT review in progress"
    else:
        status = STATUS_WARM
        detail = "Chrome running, no GPT review active"

    return {
        "project_id": project_id,
        "status": status,
        "port": port,
        "cdp_responsive": True,
        "gpt_review_active": gpt_active,
        "browser": version.get("Browser", "unknown"),
        "total_pages": len(pages),
        "detail": detail,
    }


def lazy_launch(project_id: str) -> dict:
    """Launch Chrome for a project only if needed.

    Logic:
      1. If the project CDP is already active/warm -> return existing status.
      2. Check resource policy: count warm instances; fail if >= max_warm.
      3. Launch Chrome on the project's assigned port.
      4. Verify /json/version responds.
      5. Return launch result.
    """
    # Import launch_chrome lazily to avoid circular issues at module level
    from multi_cdp_launcher import launch_chrome as _launch_chrome

    status = get_project_status(project_id)

    # Already running?
    if status["status"] in (STATUS_WARM, STATUS_ACTIVE):
        return {
            "project_id": project_id,
            "action": "noop",
            "reason": f"Already {status['status']}",
            "port": status["port"],
            "cdp_endpoint": f"http://localhost:{status['port']}",
            "status": status["status"],
        }

    # Load policy and registry
    policy = load_resource_policy()
    registry = load_registry()
    projects = registry.get("projects", {})

    if project_id not in projects:
        return {
            "project_id": project_id,
            "action": "error",
            "error": f"Project '{project_id}' not found in registry",
        }

    # Enforce warm instance limit
    max_warm = policy.get("max_warm_cdp_instances", 4)
    warm_count = count_warm_instances()

    if warm_count >= max_warm:
        return {
            "project_id": project_id,
            "action": "error",
            "error": (
                f"Resource limit reached: {warm_count}/{max_warm} warm instances. "
                f"Stop an existing instance before launching '{project_id}'."
            ),
            "warm_count": warm_count,
            "max_warm": max_warm,
        }

    # Launch shared Chrome (v2: all projects use the same instance)
    port = _get_shared_port()

    result = _launch_chrome(port=port)

    if result.get("launched") or result.get("already_active"):
        # Update registry binding_status
        projects[project_id]["binding_status"] = "warm"
        save_registry(registry)

        return {
            "project_id": project_id,
            "action": "launched",
            "port": port,
            "cdp_endpoint": f"http://localhost:{port}",
            "pid": result.get("pid"),
            "launched": result.get("launched", False),
            "already_active": result.get("already_active", False),
            "status": "warm",
        }

    return {
        "project_id": project_id,
        "action": "error",
        "error": result.get("error", "Launch failed for unknown reason"),
        "port": port,
    }


def mark_stale(project_id: str) -> dict:
    """Mark a project as stale in the registry.

    Use this when a Chrome instance was running but is no longer responsive.
    """
    registry = load_registry()
    projects = registry.get("projects", {})

    if project_id not in projects:
        return {
            "project_id": project_id,
            "action": "error",
            "error": f"Project '{project_id}' not found in registry",
        }

    projects[project_id]["binding_status"] = STATUS_STALE
    projects[project_id]["stale_at"] = _utc_now()
    save_registry(registry)

    return {
        "project_id": project_id,
        "action": "marked_stale",
        "binding_status": STATUS_STALE,
        "stale_at": projects[project_id]["stale_at"],
    }


def health_check_all() -> dict:
    """Check health of all registered projects.

    Returns a summary dict with:
      - total: int
      - active: list[str]   (project IDs)
      - warm: list[str]
      - stale: list[str]
      - not_started: list[str]
      - details: dict[str, dict]  (per-project status)
    """
    registry = load_registry()
    projects = registry.get("projects", {})

    active = []
    warm = []
    stale = []
    not_started = []
    details: dict[str, dict] = {}

    for pid in projects:
        info = get_project_status(pid)
        details[pid] = info
        status = info["status"]

        if status == STATUS_ACTIVE:
            active.append(pid)
        elif status == STATUS_WARM:
            warm.append(pid)
        elif status == STATUS_STALE:
            stale.append(pid)
        else:
            not_started.append(pid)

    return {
        "total": len(projects),
        "active": active,
        "warm": warm,
        "stale": stale,
        "not_started": not_started,
        "details": details,
    }


# ── CLI ───────────────────────────────────────────────────────────────


def cmd_status(args) -> int:
    """Show status of a single project or all projects."""
    if args.project:
        info = get_project_status(args.project)
        print(json.dumps(info, indent=2, ensure_ascii=False))
        return 0

    # No specific project — show all
    summary = health_check_all()
    print(f"{'Project':<25} {'Port':<6} {'Status':<12} {'GPT Active':<12} {'Detail'}")
    print("-" * 90)

    for pid, info in summary["details"].items():
        port = info.get("port", 0)
        status = info["status"]
        gpt = "YES" if info.get("gpt_review_active") else "NO"
        detail = info.get("detail", "")
        print(f"{pid:<25} {port:<6} {status:<12} {gpt:<12} {detail}")

    print(f"\nTotal: {summary['total']} | "
          f"Active: {len(summary['active'])} | "
          f"Warm: {len(summary['warm'])} | "
          f"Stale: {len(summary['stale'])} | "
          f"Not started: {len(summary['not_started'])}")
    return 0


def cmd_launch(args) -> int:
    """Lazy-launch a Chrome instance for a project."""
    if not args.project:
        print("Error: --project is required for launch", file=sys.stderr)
        return 1

    result = lazy_launch(args.project)
    print(json.dumps(result, indent=2, ensure_ascii=False))

    if result.get("action") == "error":
        return 1
    return 0


def cmd_health_check(args) -> int:
    """Run a full health check and print summary."""
    summary = health_check_all()
    print(json.dumps(summary, indent=2, ensure_ascii=False, default=str))
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Lazy Launch Manager — on-demand CDP instance management"
    )
    sub = parser.add_subparsers(dest="command")

    p_status = sub.add_parser("status", help="Show project CDP status")
    p_status.add_argument("--project", default=None, help="Project ID (omit for all)")

    p_launch = sub.add_parser("launch", help="Lazy-launch Chrome for a project")
    p_launch.add_argument("--project", required=True, help="Project ID to launch")

    sub.add_parser("health-check", help="Full health check of all projects")

    args = parser.parse_args()

    if args.command == "status":
        sys.exit(cmd_status(args))
    elif args.command == "launch":
        sys.exit(cmd_launch(args))
    elif args.command == "health-check":
        sys.exit(cmd_health_check(args))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
