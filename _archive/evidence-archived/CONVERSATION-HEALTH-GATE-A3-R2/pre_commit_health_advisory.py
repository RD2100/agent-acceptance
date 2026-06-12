#!/usr/bin/env python3
"""Pre-Commit Conversation Health Advisory (A3 — Layer 4).

Advisory-only module called by pre-commit.governance.ps1 Stage 4.
Reads conversation-health evidence and produces a diagnostic summary.
NEVER blocks commits — exit code is logged but does not affect commit decision.

Usage:
    python scripts/pre_commit_health_advisory.py [--project-root PATH]

Exit codes (advisory — never block commit):
    0 = healthy / advisory ran successfully
    1 = degraded (FORCE_HANDOFF or HUMAN_REQUIRED detected — advisory warning)
    2 = evidence missing (no current.json — advisory warning)
    3 = module error (internal error — diagnostic code, hook still does not block)

Design principles:
    - Advisory only: the hook stage NEVER blocks, regardless of exit code.
      Non-zero exit codes are diagnostic signals, not block decisions.
      The hook's overall_result logic only checks sadp-audit and ai-guard for BLOCKING.
    - Reads existing evidence: does NOT open CDP browser or modify files
    - Reuses decision engine: imports check_handoff_v2() for threshold evaluation
    - Fail-graceful: ImportError → exit 0; other exceptions → exit 3 (diagnostic)
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

EXIT_HEALTHY = 0
EXIT_DEGRADED = 1
EXIT_EVIDENCE_MISSING = 2
EXIT_MODULE_ERROR = 3

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CURRENT_JSON = REPO_ROOT / ".ai" / "conversation" / "current.json"
DEFAULT_LATEST_JSON = REPO_ROOT / "_evidence" / "conversation-health" / "latest.json"
DEFAULT_POLICY = REPO_ROOT / "configs" / "conversation-health-policy.yaml"
DEFAULT_EVIDENCE_DIR = REPO_ROOT / "_evidence" / "hook-output"


# ---------------------------------------------------------------------------
# Core advisory logic
# ---------------------------------------------------------------------------

def run_advisory(
    current_json_path: Optional[str] = None,
    latest_json_path: Optional[str] = None,
    policy_path: Optional[str] = None,
    project_root: Optional[str] = None,
) -> Tuple[int, Dict[str, Any]]:
    """Run the conversation-health advisory check.

    Returns:
        (exit_code, advisory_result) where exit_code is advisory-only
        (never blocks commit) and advisory_result is a JSON-serializable dict.
    """
    repo = Path(project_root) if project_root else REPO_ROOT
    current_path = Path(current_json_path) if current_json_path else DEFAULT_CURRENT_JSON
    latest_path = Path(latest_json_path) if latest_json_path else DEFAULT_LATEST_JSON

    result: Dict[str, Any] = {
        "advisory_type": "conversation-health",
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "source_files": {},
        "decision": "UNKNOWN",
        "severity": "INFO",
        "reasons": [],
        "recommendation": "continue",
    }

    # --- Try latest.json first (richer data), then current.json ---
    evidence_data = None
    evidence_source = None

    if latest_path.exists():
        try:
            evidence_data = json.loads(latest_path.read_text(encoding="utf-8"))
            evidence_source = str(latest_path)
            result["source_files"]["latest_json"] = "present"
        except (json.JSONDecodeError, OSError) as exc:
            result["source_files"]["latest_json"] = f"unreadable: {exc}"
    else:
        result["source_files"]["latest_json"] = "missing"

    if evidence_data is None and current_path.exists():
        try:
            evidence_data = json.loads(current_path.read_text(encoding="utf-8"))
            evidence_source = str(current_path)
            result["source_files"]["current_json"] = "present"
        except (json.JSONDecodeError, OSError) as exc:
            result["source_files"]["current_json"] = f"unreadable: {exc}"
    elif current_path.exists():
        result["source_files"]["current_json"] = "present (skipped, latest.json used)"
    else:
        result["source_files"]["current_json"] = "missing"

    if evidence_data is None:
        result["decision"] = "UNKNOWN"
        result["severity"] = "INFO"
        result["reasons"].append({
            "code": "no_evidence_available",
            "actual": "neither latest.json nor current.json readable",
            "threshold": "at least one evidence source required",
            "policy": "advisory",
        })
        result["recommendation"] = "consider_running_pre_gpt_gate"
        return EXIT_EVIDENCE_MISSING, result

    result["evidence_source"] = evidence_source

    # --- Extract metrics from evidence data ---
    metrics = evidence_data.get("last_known_metrics", {})
    nav_result = evidence_data.get("last_nav_result", "unknown")
    metrics_source = evidence_data.get("metrics_source", "none")
    last_checked = evidence_data.get("last_checked_at", "")

    # --- Import and run decision engine ---
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
            source_label="pre-commit-advisory",
        )

        if isinstance(decision_output, dict):
            decision = decision_output.get("decision", "UNKNOWN")
            severity = decision_output.get("severity", "INFO")
            reasons = decision_output.get("reasons", [])
        elif isinstance(decision_output, str):
            decision = decision_output
            severity = "INFO"
            reasons = []
        else:
            decision = "UNKNOWN"
            severity = "INFO"
            reasons = []

        result["decision"] = decision
        result["severity"] = severity
        result["reasons"] = reasons

        # Map decision to recommendation
        decision_map = {
            "OK": "continue",
            "SUGGEST_HANDOFF": "consider_handoff",
            "FORCE_HANDOFF": "handoff_recommended",
            "HUMAN_REQUIRED": "human_intervention_needed",
            "UNKNOWN": "investigate",
        }
        result["recommendation"] = decision_map.get(decision, "continue")

        # Determine exit code (advisory)
        if decision in ("FORCE_HANDOFF", "HUMAN_REQUIRED"):
            return EXIT_DEGRADED, result
        return EXIT_HEALTHY, result

    except ImportError as exc:
        result["decision"] = "UNKNOWN"
        result["severity"] = "INFO"
        result["reasons"].append({
            "code": "decision_engine_unavailable",
            "actual": str(exc),
            "threshold": "check_handoff_needed import required",
            "policy": "advisory",
        })
        result["recommendation"] = "decision_engine_not_available"
        return EXIT_HEALTHY, result

    except Exception as exc:
        result["decision"] = "UNKNOWN"
        result["severity"] = "INFO"
        result["reasons"].append({
            "code": "advisory_error",
            "actual": str(exc),
            "threshold": "no errors expected",
            "policy": "advisory",
        })
        return EXIT_MODULE_ERROR, result


def format_advisory_output(exit_code: int, result: Dict[str, Any]) -> str:
    """Format advisory result for hook output consumption."""
    lines = [
        "=== Conversation Health Advisory (A3 Layer 4) ===",
        f"Checked at: {result.get('checked_at', 'N/A')}",
        f"Evidence source: {result.get('evidence_source', 'none')}",
        "",
        f"Decision: {result['decision']}",
        f"Severity: {result['severity']}",
        f"Recommendation: {result['recommendation']}",
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

    source_files = result.get("source_files", {})
    if source_files:
        lines.append("")
        lines.append("Source files:")
        for name, status in source_files.items():
            lines.append(f"  {name}: {status}")

    lines.append("")
    if exit_code == EXIT_HEALTHY:
        lines.append("[ADVISORY] Conversation health OK")
    elif exit_code == EXIT_DEGRADED:
        lines.append(f"[ADVISORY] WARNING: {result['decision']} detected — "
                    f"consider switching conversation before next task")
    elif exit_code == EXIT_EVIDENCE_MISSING:
        lines.append("[ADVISORY] No conversation-health evidence found — "
                    "run Pre-GPT Gate to refresh metrics")
    else:
        lines.append("[ADVISORY] Advisory check encountered an issue")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Pre-Commit Conversation Health Advisory (A3 Layer 4)"
    )
    parser.add_argument(
        "--project-root",
        default=None,
        help="Project root directory (default: auto-detect)"
    )
    parser.add_argument(
        "--current-json",
        default=None,
        help="Path to current.json (default: .ai/conversation/current.json)"
    )
    parser.add_argument(
        "--latest-json",
        default=None,
        help="Path to latest.json (default: _evidence/conversation-health/latest.json)"
    )
    parser.add_argument(
        "--json-output",
        default=None,
        help="Write JSON result to this path (optional)"
    )
    args = parser.parse_args()

    try:
        exit_code, result = run_advisory(
            current_json_path=args.current_json,
            latest_json_path=args.latest_json,
            project_root=args.project_root,
        )

        # Always print human-readable output
        print(format_advisory_output(exit_code, result))

        # Optionally write JSON
        if args.json_output:
            Path(args.json_output).parent.mkdir(parents=True, exist_ok=True)
            Path(args.json_output).write_text(
                json.dumps(result, indent=2, ensure_ascii=False),
                encoding="utf-8"
            )

        sys.exit(exit_code)

    except Exception as exc:
        # Fail-graceful: advisory never blocks
        print(f"[ADVISORY] Unexpected error: {exc}")
        sys.exit(EXIT_HEALTHY)


if __name__ == "__main__":
    main()
