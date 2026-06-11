#!/usr/bin/env python3
"""Phase 6: Dry-Run Dispatch for all 10 registered projects.

Builds dispatch packets for every project in the registry, classifies each
packet by dispatchability, and produces a JSON report.  NO packets are sent.

Classifications (v2 fail-closed):
  dispatchable                    - resolved target, packet built, tab resolved, no blocking issues
  non_dispatchable_pending        - binding_status is pending_manual_binding
  non_dispatchable_collision      - resolved but has isolation issues (conversation collision)
  blocked_ambiguous_tab           - tab_match_status is ambiguous (multiple tabs match)
  human_required_tab_unresolved   - tab not resolved (no_match, cdp_unreachable, etc.)
  human_required_missing_target_id - target_id missing despite resolution
  human_required                  - needs human approval for other reasons

Usage:
    python scripts/dry_run_dispatch_10.py
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# ── Path setup ────────────────────────────────────────────────────────
REPO = Path(__file__).resolve().parent.parent
SCRIPTS = REPO / "scripts"
sys.path.insert(0, str(SCRIPTS))

from multi_project_router import (  # noqa: E402
    build_dispatch_packet,
    load_registry,
    resolve_all,
    resolve_target,
    verify_isolation,
)

REPORT_DIR = REPO / "_reports" / "multi-project-batch-init-a1"
REPORT_PATH = REPORT_DIR / "DRY_RUN_DISPATCH_10.json"


# ── Helpers ───────────────────────────────────────────────────────────

def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _build_test_task_spec(project_id: str) -> dict:
    """Build a dry-run task spec for a given project."""
    return {
        "task_id": f"DRYRUN-{project_id.upper()}-001",
        "description": f"Dry-run dispatch test for {project_id}",
        "dry_run": True,
        "scope": "gated_capture_only",
    }


def _build_test_message(project_id: str) -> str:
    """Build the dry-run message text for a given project."""
    return f"AWSP dry-run test for project {project_id}. Do not process."


def _redact_conv_id(conv_id: str | None) -> str | None:
    """Redact conversation ID for reports: show first 8 chars only (F3)."""
    if conv_id is None:
        return None
    if len(conv_id) <= 8:
        return conv_id
    return conv_id[:8] + "..."


# ── Classification ────────────────────────────────────────────────────

def _classify_packet(
    project_id: str,
    project_info: dict,
    target: dict,
    packet: dict,
    collision_projects: set[str],
) -> str:
    """Classify a dispatch packet into one of seven categories.

    Priority order:
      1. non_dispatchable_pending  — registry says pending_manual_binding
      2. non_dispatchable_collision — resolved but isolation violation detected
      3. blocked_ambiguous_tab     — tab_match_status is ambiguous
      4. human_required_tab_unresolved — tab not resolved (no_match, cdp_unreachable, etc.)
      5. human_required_missing_target_id — target_id missing despite match
      6. human_required            — packet not dispatchable for other reasons
      7. dispatchable              — everything OK

    v2 FAIL-CLOSED: tab_match_status MUST be exact_match and target_id
    MUST be present for a packet to be dispatchable.
    """
    binding_status = project_info.get("binding_status", "")

    # 1. Pending manual binding — cannot dispatch regardless
    if binding_status == "pending_manual_binding":
        return "non_dispatchable_pending"

    # 2. Resolved but involved in a collision
    if target.get("resolved") and project_id in collision_projects:
        return "non_dispatchable_collision"

    # 3-5. v2 fail-closed: tab_match_status and target_id checks
    # Use target as authoritative source; only fall back to packet when key missing (C-003)
    tab_status = target.get("tab_match_status") if "tab_match_status" in target else packet.get("tab_match_status")
    target_id = target.get("target_id") if "target_id" in target else packet.get("target_id")

    if tab_status and tab_status != "exact_match":
        if tab_status == "ambiguous":
            return "blocked_ambiguous_tab"
        return "human_required_tab_unresolved"

    if target.get("resolved") and not target_id:
        return "human_required_missing_target_id"

    # 6. Active binding status but packet build failed for other reasons
    if not packet.get("dispatchable"):
        return "human_required"

    # 7. All clear
    return "dispatchable"


# ── Collision Detection ───────────────────────────────────────────────

def _find_collision_projects(targets: list[dict]) -> set[str]:
    """Identify projects involved in isolation collisions (v2 rules).

    In v2 shared-CDP architecture, ONLY conversation_id collisions matter.
    Shared CDP endpoints and shared profiles are EXPECTED.
    """
    collision_projects: set[str] = set()

    conv_ids: dict[str, list[str]] = {}

    for t in targets:
        if not t.get("resolved"):
            continue
        pid = t["project_id"]

        # Conversation — the only isolation boundary in v2
        conv = t.get("conversation_id")
        if conv:
            conv_ids.setdefault(conv, []).append(pid)

    # Collect projects sharing a conversation
    for _key, pids in conv_ids.items():
        if len(pids) > 1:
            collision_projects.update(pids)

    return collision_projects


# ── Core ──────────────────────────────────────────────────────────────

def build_all_dispatch_packets() -> list[dict]:
    """Build dispatch packets for all 10 registered projects.

    Returns a list of dicts, one per project, each containing:
      project_id, dispatchable, classification, cdp_endpoint,
      conversation_id, error, and the full packet payload.
    """
    registry = load_registry()
    projects: dict[str, Any] = registry.get("projects", {})

    # Phase A: resolve all targets
    targets: list[dict] = []
    target_map: dict[str, dict] = {}
    for project_id, info in projects.items():
        root = info.get("project_root")
        target = resolve_target(project_id, root)
        targets.append(target)
        target_map[project_id] = target

    # Phase B: detect collisions across resolved targets
    collision_projects = _find_collision_projects(targets)

    # Phase C: also run the formal verify_isolation for the report
    isolation_report = verify_isolation(targets)

    # Phase D: build packets and classify
    results: list[dict] = []
    for project_id, info in projects.items():
        target = target_map[project_id]
        task_spec = _build_test_task_spec(project_id)
        message_text = _build_test_message(project_id)

        # Build the raw packet via the router
        packet = build_dispatch_packet(target, task_spec, message_text)

        # Classify
        classification = _classify_packet(
            project_id, info, target, packet, collision_projects,
        )

        dispatchable = classification == "dispatchable"

        # Determine error reason if not dispatchable
        error: str | None = None
        if not dispatchable:
            if classification == "non_dispatchable_pending":
                error = (
                    f"Project '{project_id}' has binding_status=pending_manual_binding; "
                    "manual binding required before dispatch"
                )
            elif classification == "non_dispatchable_collision":
                error = (
                    f"Project '{project_id}' resolved but has isolation collisions; "
                    "see isolation report for details"
                )
            elif classification == "blocked_ambiguous_tab":
                error = (
                    f"Project '{project_id}' has ambiguous tab_match_status; "
                    "multiple CDP tabs match the chat_url"
                )
            elif classification == "human_required_tab_unresolved":
                error = (
                    f"Project '{project_id}' tab not resolved: "
                    f"tab_match_status={target.get('tab_match_status')!r}; "
                    "open the chat_url in the shared Chrome"
                )
            elif classification == "human_required_missing_target_id":
                error = (
                    f"Project '{project_id}' resolved but target_id is missing"
                )
            elif classification == "human_required":
                error = packet.get("error") or target.get(
                    "error", "Unknown resolution failure; human review needed"
                )

        results.append({
            "project_id": project_id,
            "dispatchable": dispatchable,
            "classification": classification,
            "cdp_endpoint": target.get("cdp_endpoint"),
            "target_id": target.get("target_id"),
            "tab_match_status": target.get("tab_match_status"),
            "binding_status": info.get("binding_status"),
            "conversation_id": _redact_conv_id(target.get("conversation_id")),
            "error": error,
            "packet": packet if dispatchable else None,
        })

    return results


# ── Report ────────────────────────────────────────────────────────────

def generate_report() -> dict:
    """Generate the full dry-run dispatch report."""
    packets = build_all_dispatch_packets()

    # Summary counts
    total = len(packets)
    dispatchable_count = sum(
        1 for p in packets if p["classification"] == "dispatchable"
    )
    pending_count = sum(
        1 for p in packets if p["classification"] == "non_dispatchable_pending"
    )
    collision_count = sum(
        1 for p in packets if p["classification"] == "non_dispatchable_collision"
    )
    blocked_tab_count = sum(
        1 for p in packets if p["classification"] == "blocked_ambiguous_tab"
    )
    tab_unresolved_count = sum(
        1 for p in packets if p["classification"] == "human_required_tab_unresolved"
    )
    missing_target_id_count = sum(
        1 for p in packets if p["classification"] == "human_required_missing_target_id"
    )
    human_required_count = sum(
        1 for p in packets if p["classification"] == "human_required"
    )

    report = {
        "report_id": "DRY_RUN_DISPATCH_10",
        "phase": "MULTI-PROJECT-GPT-REVIEW-DRY-RUN-10-A1",
        "generated_at": _utc_now(),
        "sent": False,
        "packets": packets,
        "summary": {
            "total": total,
            "dispatchable_count": dispatchable_count,
            "pending_count": pending_count,
            "collision_count": collision_count,
            "blocked_tab_count": blocked_tab_count,
            "tab_unresolved_count": tab_unresolved_count,
            "missing_target_id_count": missing_target_id_count,
            "human_required_count": human_required_count,
        },
    }
    return report


# ── CLI ───────────────────────────────────────────────────────────────

def main() -> None:
    report = generate_report()

    # Ensure output directory exists
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    # Write report
    REPORT_PATH.write_text(
        json.dumps(report, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    # Also print to stdout
    print(json.dumps(report, indent=2, ensure_ascii=False))

    # Print summary line
    s = report["summary"]
    print(
        f"\n--- DRY-RUN SUMMARY ---\n"
        f"  Total projects:         {s['total']}\n"
        f"  Dispatchable:           {s['dispatchable_count']}\n"
        f"  Pending (binding):      {s['pending_count']}\n"
        f"  Collision:              {s['collision_count']}\n"
        f"  Blocked (ambiguous tab):{s.get('blocked_tab_count', 0)}\n"
        f"  Tab unresolved:         {s.get('tab_unresolved_count', 0)}\n"
        f"  Missing target_id:      {s.get('missing_target_id_count', 0)}\n"
        f"  Human required:         {s['human_required_count']}\n"
        f"  Sent:                   {report['sent']}\n"
        f"  Report saved to:        {REPORT_PATH}"
    )


if __name__ == "__main__":
    main()
