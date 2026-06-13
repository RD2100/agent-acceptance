#!/usr/bin/env python3
"""Agent-facing API for CDP review dispatch.

This module provides a simple synchronous API that agents (QoderWork,
Codex, or any Python-capable agent) can import and call directly.

The agent produces execution reports, then calls ``send_for_review()``
to deliver them to independent GPT sessions for review.

Usage from agent code::

    from scripts.cdp_review_api import send_for_review, check_review_readiness

    # Check if ready
    status = check_review_readiness()
    if status["ready"]:
        # Send all available reports
        result = send_for_review()
        print(result["summary"])

    # Or send a specific report
    result = send_for_review(report_filter="ARCHITECTURE")
"""
from __future__ import annotations

import asyncio
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Ensure scripts directory is importable
_SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(_SCRIPTS))

from cdp_write_adapter import (
    CDPClient,
    ChatGPTController,
    dispatch_to_page,
    _find_chatgpt_pages,
    _utc_now,
    DEFAULT_CDP_PORT,
    DEFAULT_RESPONSE_TIMEOUT,
)
from cdp_dispatch_runner import (
    discover_reports,
    discover_targets,
    load_binding,
    map_reports_to_reviewers,
    resolve_reviewer_target,
    format_review_prompt_safe,
    EVIDENCE_DIR,
)


def check_review_readiness(port: int = DEFAULT_CDP_PORT) -> dict:
    """Check if the review dispatch pipeline is ready.

    Returns
    -------
    dict with keys:
        ready (bool): True if reports exist and GPT sessions are live
        reports (list): Available reports with role, file, verdict, size
        targets (int): Number of live ChatGPT pages
        binding_active (int): Number of active agent bindings
        issues (list): Any problems preventing dispatch
    """
    issues = []

    # Reports
    reports = discover_reports()
    if not reports:
        issues.append("no reports found — run agent pipeline first")

    report_info = [
        {
            "role": r["role"],
            "file": r["file"],
            "verdict": r["verdict"],
            "size": r["content_length"],
        }
        for r in reports
    ]

    # Binding — require active reviewer binding (fail-closed)
    binding = {"bindings": []}
    try:
        binding = load_binding()
        active = sum(1 for b in binding.get("bindings", []) if b.get("binding_status") == "active")
        reviewer_binding = any(
            b.get("role") == "reviewer"
            and b.get("binding_status") == "active"
            and b.get("conversation_id")
            for b in binding.get("bindings", [])
        )
    except FileNotFoundError:
        active = 0
        reviewer_binding = False
        issues.append("binding file not found")

    # CDP targets
    targets = discover_targets(port)
    if not targets:
        issues.append("no live ChatGPT pages on CDP port")

    # Verify reviewer binding matches a live target
    if reviewer_binding and targets:
        reviewer_conv = next(
            (b["conversation_id"] for b in binding.get("bindings", [])
             if b.get("role") == "reviewer" and b.get("binding_status") == "active"),
            None,
        )
        target_match = any(t.conversation_id == reviewer_conv for t in targets)
        if not target_match:
            reviewer_binding = False
            issues.append(f"reviewer binding conversation_id {reviewer_conv!r} not found in live CDP targets")
    elif not reviewer_binding:
        issues.append("no active reviewer binding — dispatch will fail-closed")

    reviewer_target, reviewer_error = resolve_reviewer_target(binding, targets)
    reviewer_binding = reviewer_target is not None
    if reviewer_error and not any(reviewer_error in issue for issue in issues):
        issues.append(f"reviewer binding unavailable: {reviewer_error}")

    return {
        "ready": bool(reports) and bool(targets) and bool(reviewer_binding),
        "reports": report_info,
        "targets": len(targets),
        "binding_active": active,
        "reviewer_binding": bool(reviewer_binding),
        "issues": issues,
    }


def send_for_review(
    *,
    report_filter: str | None = None,
    wait_for_response: bool = True,
    response_timeout: int = DEFAULT_RESPONSE_TIMEOUT,
    dry_run: bool = False,
    output_dir: str | Path | None = None,
    port: int = DEFAULT_CDP_PORT,
) -> dict:
    """Send agent reports to GPT sessions for independent review.

    Parameters
    ----------
    report_filter : str, optional
        Substring to filter reports by filename (case-insensitive).
        If None, sends all available reports.
    wait_for_response : bool
        Whether to wait for GPT's review opinion (default True).
    response_timeout : int
        Max seconds to wait for response (default 300).
    dry_run : bool
        If True, validate connections without sending (default False).
    output_dir : str or Path, optional
        Directory for review evidence JSON files.
    port : int
        CDP port (default 9222).

    Returns
    -------
    dict with keys:
        success (bool): True if all reports dispatched successfully
        dispatched (int): Number of reports sent
        failed (int): Number of reports that failed
        results (list): Per-report dispatch results
        evidence_dir (str): Path where evidence was saved (if output_dir set)
    """
    # Discover
    reports = discover_reports()
    if report_filter:
        reports = [r for r in reports if report_filter.lower() in r["file"].lower()]

    if not reports:
        return {
            "success": False,
            "dispatched": 0,
            "failed": 0,
            "results": [],
            "error": f"No reports found" + (f" matching '{report_filter}'" if report_filter else ""),
        }

    binding = load_binding()
    targets = discover_targets(port)
    if not targets:
        return {
            "success": False,
            "dispatched": 0,
            "failed": len(reports),
            "results": [],
            "error": "No live ChatGPT targets on CDP port",
        }

    mappings = map_reports_to_reviewers(reports, binding, targets)
    if not mappings:
        _, reason = resolve_reviewer_target(binding, targets)
        return {
            "success": False,
            "dispatched": 0,
            "failed": len(reports),
            "total": 0,
            "results": [],
            "error": f"Reviewer mapping unavailable: {reason}",
        }
    evidence_path = Path(output_dir) if output_dir else EVIDENCE_DIR

    # Dispatch via async runner
    from cdp_dispatch_runner import dispatch_review
    results = asyncio.run(dispatch_review(
        mappings,
        wait_for_response=wait_for_response,
        response_timeout=response_timeout,
        dry_run=dry_run,
        output_dir=evidence_path,
    ))

    dispatched = sum(1 for r in results if r.get("sent") or r.get("dry_run"))
    failed = sum(1 for r in results if r.get("error"))

    return {
        "success": dispatched == len(mappings) and failed == 0,
        "dispatched": dispatched,
        "failed": failed,
        "total": len(mappings),
        "results": results,
        "evidence_dir": str(evidence_path),
        "dry_run": dry_run,
    }


def capture_review_response(
    page_id_prefix: str,
    port: int = DEFAULT_CDP_PORT,
    output_path: str | Path | None = None,
) -> dict:
    """Capture the latest GPT review response from a specific page.

    Useful when ``send_for_review`` was called with ``wait_for_response=False``
    and you want to collect the response later.

    Parameters
    ----------
    page_id_prefix : str
        Prefix of the CDP target ID (e.g., "9C03F").
    port : int
        CDP port.
    output_path : str or Path, optional
        Save the captured response to this file.
    """
    targets = discover_targets(port)
    target = None
    for t in targets:
        if t.target_id.startswith(page_id_prefix):
            target = t
            break

    if not target:
        return {"success": False, "error": f"Target '{page_id_prefix}' not found"}

    async def _capture():
        cdp = CDPClient(target.ws_url)
        ctrl = ChatGPTController(cdp)
        await cdp.connect()
        text = await ctrl.capture_last_response()
        title = await ctrl.get_page_title()
        await cdp.close()
        return text, title

    text, title = asyncio.run(_capture())

    result = {
        "success": True,
        "target_id": target.target_id,
        "conversation_id": target.conversation_id,
        "title": title,
        "review_response": text,
        "captured_at": _utc_now(),
    }

    if output_path:
        p = Path(output_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")

    return result


# ── CLI shortcut (for agents that prefer shell invocation) ────────────


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Agent API for CDP review dispatch")
    parser.add_argument("action", choices=["check", "send", "capture"],
                        help="check readiness, send reports, or capture response")
    parser.add_argument("--filter", help="Filter reports by filename substring")
    parser.add_argument("--page-id", help="CDP target ID prefix (for capture)")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--no-wait", action="store_true")
    parser.add_argument("--output", help="Output file path")
    args = parser.parse_args()

    if args.action == "check":
        result = check_review_readiness()
    elif args.action == "send":
        result = send_for_review(
            report_filter=args.filter,
            wait_for_response=not args.no_wait,
            dry_run=args.dry_run,
        )
    elif args.action == "capture":
        if not args.page_id:
            print("ERROR: --page-id required for capture", file=sys.stderr)
            sys.exit(1)
        result = capture_review_response(args.page_id, output_path=args.output)
    else:
        parser.print_help()
        sys.exit(1)

    print(json.dumps(result, indent=2, ensure_ascii=False))
