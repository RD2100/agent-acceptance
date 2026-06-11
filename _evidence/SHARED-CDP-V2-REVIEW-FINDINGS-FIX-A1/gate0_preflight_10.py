#!/usr/bin/env python3
"""Gate0 Preflight Check v2 — Shared CDP Architecture.

v2 classification rules (replaces v1 profile/port collision model):
  - active:                binding_status=active, CDP healthy, unique conversation,
                           tab target resolved
  - pending_manual_binding: binding_status=pending_binding, no real conversation
  - conversation_collision: active but shares conversation_id with another project
  - tab_unresolved:        active with valid conversation but no matching CDP tab
  - stale:                 was active but shared CDP not responding
  - blocked:               hard blocker (unknown status, duplicate chat_url, etc.)

Overall verdict:
  - PASS:         all active projects have unique conversations + resolved tabs
  - PARTIAL_PASS: active projects exist but have unresolved tabs or other issues
  - BLOCKED:      no active projects or critical errors

v2 key differences from v1:
  - Shared CDP endpoint is EXPECTED (not a collision)
  - Shared browser profile is EXPECTED (not a collision)
  - Isolation is via conversation_id + tab target_id (not profile + port)

Usage:
  python gate0_preflight_10.py
  python gate0_preflight_10.py --report-path custom/path.json
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.request
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parent.parent
SCRIPTS = REPO / "scripts"
sys.path.insert(0, str(SCRIPTS))

REGISTRY_PATH = REPO / ".agent" / "PROJECT_REGISTRY.json"
DEFAULT_REPORT_DIR = REPO / "_reports" / "multi-project-batch-init-a1"
DEFAULT_REPORT_NAME = "GATE0_PREFLIGHT_10.json"

# Import canonical tab resolver (v2 architecture requirement)
from tab_target_resolver import (  # noqa: E402
    resolve_tab_target as _canonical_resolve_tab_target,
    list_cdp_pages as _canonical_list_cdp_pages,
    validate_cdp_endpoint as _canonical_validate_cdp_endpoint,
)


# -- Utilities ---------------------------------------------------------------


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def load_registry() -> dict:
    """Load global project registry."""
    if REGISTRY_PATH.exists():
        return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    return {"projects": {}}


def load_binding(project_root: Path) -> dict:
    """Load a project's CONVERSATION_BINDING.json (returns {} if missing)."""
    binding_path = project_root / ".agent" / "CONVERSATION_BINDING.json"
    if not binding_path.exists():
        return {}
    return json.loads(binding_path.read_text(encoding="utf-8"))


def check_cdp_health(cdp_endpoint: str) -> bool:
    """Check whether the shared CDP endpoint is reachable (localhost only)."""
    valid, _ = _canonical_validate_cdp_endpoint(cdp_endpoint)
    if not valid:
        return False
    try:
        with urllib.request.urlopen(
            f"{cdp_endpoint}/json/version", timeout=3
        ) as resp:
            return resp.status == 200
    except Exception:
        return False


def is_valid_conv_id(conv_id: str | None) -> bool:
    """A valid conversation ID is non-None and not a pending-* placeholder."""
    if conv_id is None:
        return False
    if conv_id.startswith("pending-"):
        return False
    if not conv_id.strip():
        return False
    return True


# -- Per-project evaluation (v2) --------------------------------------------


def _evaluate_project_v2(
    project_id: str,
    reg_info: dict,
    binding: dict,
    cdp_healthy: bool,
    conv_id_duplicates: set[str],
    chat_url_duplicates: set[str],
    cdp_pages: list[dict],
) -> dict:
    """Evaluate a single project under v2 rules.

    v2 does NOT check profile_dup or port_dup — shared CDP/profile is expected.
    Instead, it checks:
      - conversation_id uniqueness
      - chat_url uniqueness
      - tab target resolution
    """
    bindings_list = binding.get("bindings", [])
    has_binding = len(bindings_list) > 0
    reg_status = reg_info.get("binding_status", "unknown")

    # Extract conversation data from active agents
    active_agents = [
        b for b in bindings_list
        if b.get("binding_status") == "active"
    ]
    conv_ids = [b.get("conversation_id") for b in active_agents]
    chat_urls = [b.get("chat_url") for b in active_agents]
    any_valid_conv = any(is_valid_conv_id(c) for c in conv_ids)

    # The primary chat_url and conversation_id (first active agent)
    primary_conv_id = conv_ids[0] if conv_ids else None
    primary_chat_url = chat_urls[0] if chat_urls else None

    issues: list[str] = []
    tab_result: dict = {}

    # ---- classify ----
    if reg_status == "active":
        if not cdp_healthy:
            status = "stale"
            issues.append("Shared CDP endpoint not responding")
        elif not has_binding:
            status = "blocked"
            issues.append("No CONVERSATION_BINDING.json found")
        elif not any_valid_conv:
            status = "stale"
            issues.append("Active in registry but no real conversation bound")
        elif primary_conv_id and primary_conv_id in conv_id_duplicates:
            status = "conversation_collision"
            issues.append(
                f"conversation_id '{primary_conv_id}' is shared with another project"
            )
        elif primary_chat_url and primary_chat_url in chat_url_duplicates:
            status = "blocked"
            issues.append(
                f"chat_url '{primary_chat_url}' is shared with another project"
            )
        else:
            # Attempt tab target resolution via canonical resolver
            tab_result = _canonical_resolve_tab_target(primary_chat_url, cdp_pages)

            if tab_result["match_status"] == "exact_match":
                status = "active"
            elif tab_result["match_status"] == "no_match":
                status = "tab_unresolved"
                issues.extend(tab_result.get("issues", []))
            elif tab_result["match_status"] == "ambiguous":
                status = "blocked"
                issues.extend(tab_result.get("issues", []))
            else:
                status = "tab_unresolved"
                issues.extend(tab_result.get("issues", []))

    elif reg_status in ("pending_manual_binding", "pending", "pending_binding"):
        status = "pending_manual_binding"
        if any_valid_conv:
            issues.append("Has real conversation but registry still shows pending")
    else:
        status = "blocked"
        issues.append(f"Unknown or missing binding_status: {reg_status!r}")

    return {
        "project_id": project_id,
        "status": status,
        "cdp_healthy": cdp_healthy,
        "conv_id_valid": any_valid_conv,
        "conv_id": primary_conv_id,
        "chat_url": primary_chat_url,
        "has_binding": has_binding,
        "binding_count": len(bindings_list),
        "tab_target_id": tab_result.get("target_id"),
        "tab_match_status": tab_result.get("match_status", "skipped"),
        "issues": issues,
    }


# -- Main preflight (v2) -----------------------------------------------------


def run_preflight() -> dict:
    """Run Gate0 preflight v2 for all registered projects.

    Returns a structured report with per-project status and overall verdict.
    """
    registry = load_registry()
    projects: dict[str, dict] = registry.get("projects", {})
    cdp_endpoint = registry.get("shared_cdp_endpoint", "http://localhost:9222")

    if not projects:
        return {
            "schema_version": "2.0.0",
            "generated_at": _utc_now(),
            "total_projects": 0,
            "per_project": [],
            "overall": {"verdict": "BLOCKED"},
            "active_count": 0,
            "pending_count": 0,
            "collision_count": 0,
            "tab_unresolved_count": 0,
            "stale_count": 0,
            "blocked_count": 0,
            "recommendation": "No projects registered in PROJECT_REGISTRY.json",
        }

    # ---- Shared infrastructure checks (once for all projects) ----
    cdp_healthy = check_cdp_health(cdp_endpoint)
    cdp_pages = _canonical_list_cdp_pages(cdp_endpoint) if cdp_healthy else []

    # ---- First pass: gather collision data across active projects ----
    binding_cache: dict[str, dict] = {}
    conv_id_map: dict[str, list[str]] = defaultdict(list)  # conv_id -> [project_ids]
    chat_url_map: dict[str, list[str]] = defaultdict(list)  # chat_url -> [project_ids]

    for pid, info in projects.items():
        root = Path(info.get("project_root", "."))
        binding = load_binding(root)
        binding_cache[pid] = binding

        # Only track collisions for active projects
        if info.get("binding_status") == "active":
            for b in binding.get("bindings", []):
                if b.get("binding_status") == "active":
                    cid = b.get("conversation_id")
                    curl = b.get("chat_url")
                    if is_valid_conv_id(cid):
                        conv_id_map[cid].append(pid)
                    if curl:
                        chat_url_map[curl].append(pid)

    # Identify duplicates
    conv_id_duplicates = {k for k, v in conv_id_map.items() if len(set(v)) > 1}
    chat_url_duplicates = {k for k, v in chat_url_map.items() if len(set(v)) > 1}

    # ---- Second pass: evaluate each project ----
    results: list[dict] = []
    for pid, info in projects.items():
        binding = binding_cache[pid]
        results.append(
            _evaluate_project_v2(
                pid, info, binding,
                cdp_healthy,
                conv_id_duplicates,
                chat_url_duplicates,
                cdp_pages,
            )
        )

    # ---- Counts ----
    counts: dict[str, int] = Counter(r["status"] for r in results)
    active_count = counts.get("active", 0)
    pending_count = counts.get("pending_manual_binding", 0)
    collision_count = counts.get("conversation_collision", 0)
    tab_unresolved_count = counts.get("tab_unresolved", 0)
    stale_count = counts.get("stale", 0)
    blocked_count = counts.get("blocked", 0)

    # ---- Verdict (v2) ----
    has_critical = blocked_count > 0 or collision_count > 0
    has_unresolved = tab_unresolved_count > 0 or stale_count > 0

    if active_count == 0 and pending_count == 0:
        verdict = "BLOCKED"
    elif active_count == 0:
        verdict = "BLOCKED"
    elif has_critical or has_unresolved:
        verdict = "PARTIAL_PASS"
    else:
        verdict = "PASS"

    # ---- Recommendation ----
    recommendation = _build_recommendation_v2(
        verdict, results, collision_count, tab_unresolved_count,
        stale_count, blocked_count, pending_count,
    )

    return {
        "schema_version": "2.0.0",
        "task_id": "SHARED-CDP-GATE0-PREFLIGHT-V2-A1",
        "architecture_version": "2.0.0",
        "cdp_mode": "shared_single_chrome",
        "generated_at": _utc_now(),
        "cdp_endpoint": cdp_endpoint,
        "cdp_healthy": cdp_healthy,
        "cdp_pages_total": len(cdp_pages),
        "total_projects": len(projects),
        "per_project": results,
        "overall": {
            "verdict": verdict,
            "details": (
                f"{active_count} active, {pending_count} pending, "
                f"{collision_count} conversation collisions, "
                f"{tab_unresolved_count} tab unresolved, "
                f"{stale_count} stale, {blocked_count} blocked"
            ),
        },
        "active_count": active_count,
        "pending_count": pending_count,
        "collision_count": collision_count,
        "tab_unresolved_count": tab_unresolved_count,
        "stale_count": stale_count,
        "blocked_count": blocked_count,
        "recommendation": recommendation,
    }


def _build_recommendation_v2(
    verdict: str,
    results: list[dict],
    collision_count: int,
    tab_unresolved_count: int,
    stale_count: int,
    blocked_count: int,
    pending_count: int,
) -> str:
    """Build a human-readable recommendation string (v2)."""
    if verdict == "PASS":
        return "All v2 checks passed. Conversation isolation + tab targets verified."

    parts: list[str] = []

    if collision_count > 0:
        colliding = [
            r["project_id"] for r in results
            if r["status"] == "conversation_collision"
        ]
        parts.append(
            f"Resolve conversation_id collisions for: {', '.join(colliding)}. "
            f"Each active project must have a unique conversation."
        )

    if tab_unresolved_count > 0:
        unresolved = [
            r["project_id"] for r in results
            if r["status"] == "tab_unresolved"
        ]
        parts.append(
            f"Open matching conversation tabs for: {', '.join(unresolved)}. "
            f"Each active project's chat_url must be open in the shared Chrome."
        )

    if stale_count > 0:
        stale = [r["project_id"] for r in results if r["status"] == "stale"]
        parts.append(
            f"Restart shared Chrome or bind conversations for: {', '.join(stale)}."
        )

    if blocked_count > 0:
        blocked = [r["project_id"] for r in results if r["status"] == "blocked"]
        parts.append(
            f"Investigate blockers for: {', '.join(blocked)}."
        )

    if pending_count > 0:
        parts.append(
            f"{pending_count} project(s) awaiting manual conversation binding."
        )

    parts.append("Re-run preflight after fixes to reach PASS.")
    return " ".join(parts)


# -- CLI ---------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Gate0 Preflight v2 — Shared CDP Architecture"
    )
    parser.add_argument(
        "--report-path",
        default=str(DEFAULT_REPORT_DIR / DEFAULT_REPORT_NAME),
        help="Output path for JSON report",
    )
    parser.add_argument(
        "--verbose", action="store_true",
        help="Print detailed per-project info to stderr",
    )
    args = parser.parse_args()

    report = run_preflight()

    # Write report to disk
    report_path = Path(args.report_path)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    # JSON to stdout
    print(json.dumps(report, indent=2, ensure_ascii=False))

    # Human-readable summary to stderr
    sys.stderr.write(
        f"\n--- Gate0 Preflight v2 Summary ---\n"
        f"Verdict:       {report['overall']['verdict']}\n"
        f"CDP healthy:   {report['cdp_healthy']}\n"
        f"Active:        {report['active_count']}\n"
        f"Pending:       {report['pending_count']}\n"
        f"Conv collision:{report['collision_count']}\n"
        f"Tab unresolved:{report['tab_unresolved_count']}\n"
        f"Stale:         {report['stale_count']}\n"
        f"Blocked:       {report['blocked_count']}\n"
        f"Recommendation:{report['recommendation']}\n"
        f"Report:        {report_path}\n"
    )


if __name__ == "__main__":
    main()
