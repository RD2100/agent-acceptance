#!/usr/bin/env python3
"""Startup Conversation Health Check (A4 — Item 1.9).

Lightweight startup-read helper that checks conversation-health state
at agent startup without opening CDP. Reads existing evidence files
and writes auditable startup-read-latest.json.

Usage:
    python scripts/startup_conversation_health_check.py [--project-root PATH]

Exit codes (awareness only — never blocks startup):
    0 = check completed (any outcome — OK, degraded, or missing evidence)

Design principles:
    - Awareness only: the startup check never blocks agent execution.
      It produces auditable evidence about conversation-health state.
    - No CDP: reads existing files only, does not open a browser.
    - Reuses decision engine: imports check_handoff_v2() for threshold
      evaluation. Does not duplicate threshold logic.
    - Fail-graceful: missing current.json → UNKNOWN/WARNING evidence.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional, Tuple


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CURRENT_JSON = REPO_ROOT / ".ai" / "conversation" / "current.json"
DEFAULT_LATEST_JSON = REPO_ROOT / "_evidence" / "conversation-health" / "latest.json"
DEFAULT_POLICY = REPO_ROOT / "configs" / "conversation-health-policy.yaml"
DEFAULT_OUTPUT = REPO_ROOT / "_evidence" / "conversation-health" / "startup-read-latest.json"


# ---------------------------------------------------------------------------
# Core startup check
# ---------------------------------------------------------------------------

def run_startup_check(
    current_json_path: Optional[str] = None,
    latest_json_path: Optional[str] = None,
    policy_path: Optional[str] = None,
    output_path: Optional[str] = None,
    project_root: Optional[str] = None,
) -> Dict[str, Any]:
    """Run the startup conversation-health check.

    Reads current.json and latest.json, evaluates health state using
    check_handoff_v2(), and writes startup-read-latest.json evidence.

    Returns:
        A JSON-serializable dict with the startup check result.
    """
    repo = Path(project_root) if project_root else REPO_ROOT
    current_path = Path(current_json_path) if current_json_path else DEFAULT_CURRENT_JSON
    latest_path = Path(latest_json_path) if latest_json_path else DEFAULT_LATEST_JSON
    out_path = Path(output_path) if output_path else DEFAULT_OUTPUT

    result: Dict[str, Any] = {
        "schema_version": "startup-read-conversation-health.v1",
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "current_json_present": False,
        "latest_json_present": False,
        "source_files_read": [],
        "decision": "UNKNOWN",
        "severity": "WARNING",
        "recommended_action": "investigate",
        "metrics_source": "none",
        "metrics_freshness": "unknown",
        "last_nav_result": "unknown",
        "reasons": [],
    }

    # --- Read latest.json first (richer data, includes previous decision) ---
    latest_data = None
    if latest_path.exists():
        try:
            latest_data = json.loads(latest_path.read_text(encoding="utf-8"))
            result["latest_json_present"] = True
            result["source_files_read"].append(str(latest_path))
        except (json.JSONDecodeError, OSError):
            result["source_files_read"].append(f"{latest_path} (unreadable)")

    # --- Read current.json (live metrics) ---
    current_data = None
    if current_path.exists():
        try:
            current_data = json.loads(current_path.read_text(encoding="utf-8"))
            result["current_json_present"] = True
            result["source_files_read"].append(str(current_path))
        except (json.JSONDecodeError, OSError):
            result["source_files_read"].append(f"{current_path} (unreadable)")

    # --- If neither file is available → UNKNOWN/WARNING ---
    if current_data is None and latest_data is None:
        result["decision"] = "UNKNOWN"
        result["severity"] = "WARNING"
        result["reasons"].append({
            "code": "no_evidence_available",
            "actual": "neither current.json nor latest.json readable",
            "threshold": "at least one evidence source required for startup awareness",
            "policy": "awareness",
        })
        result["recommended_action"] = "run_pre_gpt_gate_to_refresh_metrics"
        _write_output(out_path, result)
        return result

    # --- Prefer current.json for fresh metrics, fall back to latest.json ---
    evidence_data = current_data if current_data is not None else latest_data

    # Extract metrics and metadata
    metrics = evidence_data.get("last_known_metrics", {})
    nav_result = evidence_data.get("last_nav_result", "unknown")
    metrics_source = evidence_data.get("metrics_source", "none")
    last_checked = evidence_data.get("last_checked_at", "")
    metrics_freshness = evidence_data.get("metrics_freshness", "unknown")

    result["metrics_source"] = metrics_source
    result["metrics_freshness"] = metrics_freshness
    result["last_nav_result"] = nav_result

    # --- Run decision engine ---
    try:
        scripts_dir = str(repo / "scripts")
        if scripts_dir not in sys.path:
            sys.path.insert(0, scripts_dir)
        from check_handoff_needed import check_handoff_v2

        decision_output = check_handoff_v2(
            metrics={
                "assistant_message_count": metrics.get("assistant_message_count"),
                "response_time_seconds": metrics.get("last_response_time_seconds")
                    or metrics.get("response_time_seconds"),
                "review_round_count": metrics.get("review_round_count"),
                "last_gpt_reply_bytes": metrics.get("last_gpt_reply_bytes"),
                "metrics_source": metrics_source,
                "nav_result": nav_result,
                "last_checked_at": last_checked,
            },
            mode="advisory",
            max_staleness_hours=12,
            composite=True,
            source_label="startup-read-check",
        )

        if isinstance(decision_output, dict):
            decision = decision_output.get("decision", "UNKNOWN")
            severity = decision_output.get("severity", "INFO")
            reasons = decision_output.get("reasons", [])
            recommended = decision_output.get("recommended_action", "continue")
        else:
            decision = "UNKNOWN"
            severity = "INFO"
            reasons = []
            recommended = "investigate"

        result["decision"] = decision
        result["severity"] = severity
        result["reasons"] = reasons
        result["recommended_action"] = recommended

    except ImportError as exc:
        result["decision"] = "UNKNOWN"
        result["severity"] = "WARNING"
        result["reasons"].append({
            "code": "decision_engine_unavailable",
            "actual": str(exc),
            "threshold": "check_handoff_needed import required",
            "policy": "awareness",
        })
        result["recommended_action"] = "decision_engine_not_available"

    except Exception as exc:
        result["decision"] = "UNKNOWN"
        result["severity"] = "WARNING"
        result["reasons"].append({
            "code": "startup_check_error",
            "actual": str(exc),
            "threshold": "no errors expected",
            "policy": "awareness",
        })
        result["recommended_action"] = "investigate"

    _write_output(out_path, result)
    return result


def _write_output(out_path: Path, result: Dict[str, Any]) -> None:
    """Write the startup-read evidence to disk."""
    try:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(
            json.dumps(result, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
    except OSError:
        pass  # Awareness only — write failure is not blocking


def format_startup_output(result: Dict[str, Any]) -> str:
    """Format startup check result for human-readable output."""
    lines = [
        "=== Startup Conversation Health Check (A4 Item 1.9) ===",
        f"Checked at: {result.get('checked_at', 'N/A')}",
        f"Decision: {result['decision']}",
        f"Severity: {result['severity']}",
        f"Recommended action: {result['recommended_action']}",
        "",
        f"current.json: {'present' if result.get('current_json_present') else 'missing'}",
        f"latest.json: {'present' if result.get('latest_json_present') else 'missing'}",
        f"Metrics source: {result.get('metrics_source', 'none')}",
        f"Metrics freshness: {result.get('metrics_freshness', 'unknown')}",
        f"Last nav result: {result.get('last_nav_result', 'unknown')}",
    ]

    if result.get("reasons"):
        lines.append("")
        lines.append("Reasons:")
        for r in result["reasons"]:
            if isinstance(r, dict):
                lines.append(f"  - [{r.get('code', '?')}] {r.get('actual', '?')} "
                           f"(policy: {r.get('policy', '?')})")
            else:
                lines.append(f"  - {r}")

    lines.append("")
    decision = result.get("decision", "UNKNOWN")
    if decision == "OK":
        lines.append("[STARTUP] Conversation health OK — proceed with task")
    elif decision in ("FORCE_HANDOFF", "HUMAN_REQUIRED"):
        lines.append(f"[STARTUP] ACTION REQUIRED: {decision} — "
                    f"{result.get('recommended_action', 'handoff recommended')}")
    elif decision == "SUGGEST_HANDOFF":
        lines.append("[STARTUP] SUGGESTION: consider switching conversation "
                    "before starting complex work")
    else:
        lines.append("[STARTUP] WARNING: conversation health unknown — "
                    "run Pre-GPT Gate to refresh metrics")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Startup Conversation Health Check (A4 Item 1.9)"
    )
    parser.add_argument("--project-root", default=None,
                       help="Project root directory (default: auto-detect)")
    parser.add_argument("--current-json", default=None,
                       help="Path to current.json")
    parser.add_argument("--latest-json", default=None,
                       help="Path to latest.json")
    parser.add_argument("--output", default=None,
                       help="Output path for startup-read-latest.json")
    args = parser.parse_args()

    result = run_startup_check(
        current_json_path=args.current_json,
        latest_json_path=args.latest_json,
        output_path=args.output,
        project_root=args.project_root,
    )
    print(format_startup_output(result))


if __name__ == "__main__":
    main()
