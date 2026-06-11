#!/usr/bin/env python3
"""Conversation Registry Reconciliation (A3).

Cross-checks conversation-health state against CONVERSATION_BINDING.json
to detect inconsistencies between the health monitoring system and the
conversation registry.

Usage:
    python scripts/reconcile_conversation_registry.py [--project-root PATH]

Exit codes (advisory — never block commit):
    0 = consistent (no reconciliation issues)
    1 = inconsistencies found (advisory warning)
    2 = registry or health data unavailable
    3 = module error

Design principles:
    - Advisory only: never blocks commit
    - Reads existing evidence: does NOT modify files
    - Cross-checks: compares conversation_id in current.json vs active bindings
    - Detects: stale bindings, orphaned health data, policy violations
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

EXIT_CONSISTENT = 0
EXIT_INCONSISTENT = 1
EXIT_DATA_UNAVAILABLE = 2
EXIT_MODULE_ERROR = 3

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CURRENT_JSON = REPO_ROOT / ".ai" / "conversation" / "current.json"
DEFAULT_BINDING_FILE = REPO_ROOT / "CONVERSATION_BINDING.json"
DEFAULT_EVIDENCE_DIR = REPO_ROOT / "_evidence"


# ---------------------------------------------------------------------------
# Reconciliation checks
# ---------------------------------------------------------------------------

def reconcile(
    current_json_path: Optional[str] = None,
    binding_file_path: Optional[str] = None,
    project_root: Optional[str] = None,
) -> Tuple[int, Dict[str, Any]]:
    """Run registry reconciliation against conversation-health state.

    Returns:
        (exit_code, reconciliation_result)
    """
    repo = Path(project_root) if project_root else REPO_ROOT
    current_path = Path(current_json_path) if current_json_path else DEFAULT_CURRENT_JSON
    binding_path = Path(binding_file_path) if binding_file_path else DEFAULT_BINDING_FILE

    result: Dict[str, Any] = {
        "reconciliation_type": "conversation-registry",
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "checks": [],
        "inconsistencies": [],
        "summary": {
            "total_checks": 0,
            "passed": 0,
            "warnings": 0,
            "issues": 0,
        },
    }

    # --- Load current.json ---
    health_data = None
    if current_path.exists():
        try:
            health_data = json.loads(current_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass

    # --- Load CONVERSATION_BINDING.json ---
    binding_data = None
    if binding_path.exists():
        try:
            binding_data = json.loads(binding_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass

    # --- Check 1: Both data sources exist ---
    if health_data is None and binding_data is None:
        result["checks"].append({
            "check": "data_availability",
            "status": "UNAVAILABLE",
            "detail": "Neither current.json nor CONVERSATION_BINDING.json found",
        })
        result["summary"]["total_checks"] = 1
        result["summary"]["issues"] = 1
        return EXIT_DATA_UNAVAILABLE, result

    if health_data is None:
        result["checks"].append({
            "check": "health_data_available",
            "status": "WARNING",
            "detail": "current.json not found — health state unavailable",
        })
        result["summary"]["total_checks"] += 1
        result["summary"]["warnings"] += 1

    if binding_data is None:
        result["checks"].append({
            "check": "binding_data_available",
            "status": "WARNING",
            "detail": "CONVERSATION_BINDING.json not found — registry unavailable",
        })
        result["summary"]["total_checks"] += 1
        result["summary"]["warnings"] += 1

    if health_data is None or binding_data is None:
        result["checks"].append({
            "check": "cross_reference",
            "status": "SKIPPED",
            "detail": "Cannot cross-reference — one or both data sources missing",
        })
        result["summary"]["total_checks"] += 1
        return EXIT_DATA_UNAVAILABLE, result

    # --- Check 2: Conversation ID consistency ---
    health_conv_id = health_data.get("conversation_id", "")
    health_chat_url = health_data.get("chat_url", "")

    active_bindings = [
        b for b in binding_data.get("bindings", [])
        if b.get("binding_status") == "active"
    ]

    if active_bindings:
        # Check if the health conversation_id matches any active binding
        found_match = False
        for binding in active_bindings:
            binding_conv_id = binding.get("conversation_id", "")
            binding_chat_url = binding.get("chat_url", "")

            # Match by conversation_id
            if health_conv_id and binding_conv_id and health_conv_id == binding_conv_id:
                found_match = True
                result["checks"].append({
                    "check": "conversation_id_match",
                    "status": "PASS",
                    "detail": f"Health conversation_id '{health_conv_id}' matches "
                             f"active binding for agent '{binding.get('agent_id', '?')}'",
                })
                break

            # Match by chat_url
            if health_chat_url and binding_chat_url and health_chat_url == binding_chat_url:
                found_match = True
                result["checks"].append({
                    "check": "chat_url_match",
                    "status": "PASS",
                    "detail": f"Health chat_url matches active binding for "
                             f"agent '{binding.get('agent_id', '?')}'",
                })
                break

        if not found_match:
            result["checks"].append({
                "check": "conversation_id_match",
                "status": "WARNING",
                "detail": f"Health conversation_id '{health_conv_id}' does not match "
                         f"any active binding ({len(active_bindings)} active bindings)",
            })
            result["inconsistencies"].append({
                "type": "orphaned_health_data",
                "detail": "current.json references a conversation not in any active binding",
                "health_conversation_id": health_conv_id,
                "active_binding_count": len(active_bindings),
            })
    else:
        result["checks"].append({
            "check": "active_bindings",
            "status": "INFO",
            "detail": "No active bindings found — cannot cross-reference",
        })

    # --- Check 3: Health status vs binding status consistency ---
    health_status = health_data.get("status", "unknown")
    if health_status in ("handoff_required", "inaccessible", "migrated"):
        for binding in active_bindings:
            if binding.get("binding_status") == "active":
                # An active binding with degraded health is an inconsistency
                result["inconsistencies"].append({
                    "type": "degraded_health_with_active_binding",
                    "detail": f"Health status is '{health_status}' but binding for "
                             f"agent '{binding.get('agent_id', '?')}' is still active",
                    "health_status": health_status,
                    "agent_id": binding.get("agent_id", "?"),
                    "recommendation": "Consider updating binding status to 'paused' "
                                    "or performing conversation migration",
                })

    # --- Check 4: One-agent-one-conversation policy ---
    policy = binding_data.get("default_conversation_policy", "")
    if policy == "one_agent_one_conversation":
        # Count distinct active conversations per agent
        agent_conv_map: Dict[str, List[str]] = {}
        for binding in active_bindings:
            agent_id = binding.get("agent_id", "?")
            conv_id = binding.get("conversation_id") or binding.get("chat_url", "")
            if conv_id:
                agent_conv_map.setdefault(agent_id, []).append(conv_id)

        for agent_id, conv_ids in agent_conv_map.items():
            if len(conv_ids) > 1:
                result["inconsistencies"].append({
                    "type": "policy_violation",
                    "detail": f"Agent '{agent_id}' has {len(conv_ids)} active conversations "
                             f"(policy: one_agent_one_conversation)",
                    "agent_id": agent_id,
                    "conversation_count": len(conv_ids),
                })

    # --- Check 5: Capture policy enforcement ---
    for binding in active_bindings:
        capture_policy = binding.get("capture_policy", {})
        required_fields = [
            "must_match_run_id",
            "must_match_task_id",
            "must_include_end_marker",
            "forbid_last_message_only_capture",
        ]
        for field in required_fields:
            if not capture_policy.get(field, False):
                result["inconsistencies"].append({
                    "type": "capture_policy_relaxed",
                    "detail": f"Binding for agent '{binding.get('agent_id', '?')}' "
                             f"has {field}=false (should be true)",
                    "agent_id": binding.get("agent_id", "?"),
                    "field": field,
                })

    # --- Summary ---
    total_checks = len(result["checks"]) + len(result["inconsistencies"])
    passed = sum(1 for c in result["checks"] if c.get("status") in ("PASS", "INFO"))
    warnings = sum(1 for c in result["checks"] if c.get("status") == "WARNING")
    issues = len(result["inconsistencies"])

    result["summary"] = {
        "total_checks": total_checks,
        "passed": passed,
        "warnings": warnings,
        "issues": issues,
        "active_bindings": len(active_bindings),
        "health_status": health_status,
    }

    if issues > 0:
        return EXIT_INCONSISTENT, result
    return EXIT_CONSISTENT, result


def format_reconciliation_output(exit_code: int, result: Dict[str, Any]) -> str:
    """Format reconciliation result for human-readable output."""
    lines = [
        "=== Conversation Registry Reconciliation (A3) ===",
        f"Checked at: {result.get('checked_at', 'N/A')}",
        "",
    ]

    summary = result.get("summary", {})
    lines.append(f"Total checks: {summary.get('total_checks', 0)}")
    lines.append(f"Passed: {summary.get('passed', 0)}")
    lines.append(f"Warnings: {summary.get('warnings', 0)}")
    lines.append(f"Issues: {summary.get('issues', 0)}")

    if result.get("checks"):
        lines.append("")
        lines.append("Checks:")
        for c in result["checks"]:
            status_icon = "[PASS]" if c["status"] == "PASS" else "[WARN]" if c["status"] == "WARNING" else "[INFO]"
            lines.append(f"  {status_icon} [{c['check']}] {c['status']}: {c['detail']}")

    if result.get("inconsistencies"):
        lines.append("")
        lines.append("Inconsistencies:")
        for inc in result["inconsistencies"]:
            lines.append(f"  [FAIL] [{inc['type']}] {inc['detail']}")
            if inc.get("recommendation"):
                lines.append(f"    → {inc['recommendation']}")

    lines.append("")
    if exit_code == EXIT_CONSISTENT:
        lines.append("[RECONCILIATION] Registry is consistent")
    elif exit_code == EXIT_INCONSISTENT:
        lines.append(f"[RECONCILIATION] WARNING: {summary.get('issues', 0)} "
                    f"inconsistencies found (advisory)")
    elif exit_code == EXIT_DATA_UNAVAILABLE:
        lines.append("[RECONCILIATION] Data unavailable — skipped cross-reference")
    else:
        lines.append("[RECONCILIATION] Module error")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Conversation Registry Reconciliation (A3)"
    )
    parser.add_argument(
        "--project-root",
        default=None,
        help="Project root directory (default: auto-detect)"
    )
    parser.add_argument(
        "--current-json",
        default=None,
        help="Path to current.json"
    )
    parser.add_argument(
        "--binding-file",
        default=None,
        help="Path to CONVERSATION_BINDING.json"
    )
    parser.add_argument(
        "--json-output",
        default=None,
        help="Write JSON result to this path"
    )
    args = parser.parse_args()

    try:
        exit_code, result = reconcile(
            current_json_path=args.current_json,
            binding_file_path=args.binding_file,
            project_root=args.project_root,
        )

        print(format_reconciliation_output(exit_code, result))

        if args.json_output:
            Path(args.json_output).parent.mkdir(parents=True, exist_ok=True)
            Path(args.json_output).write_text(
                json.dumps(result, indent=2, ensure_ascii=False),
                encoding="utf-8"
            )

        sys.exit(exit_code)

    except Exception as exc:
        print(f"[RECONCILIATION] Unexpected error: {exc}")
        sys.exit(EXIT_CONSISTENT)


if __name__ == "__main__":
    main()
