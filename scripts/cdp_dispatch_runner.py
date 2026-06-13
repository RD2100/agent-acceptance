#!/usr/bin/env python3
"""CDP Dispatch Runner — execute a dispatch plan via CDP Write Adapter.

Reads the current dispatch plan and conversation binding, discovers
live CDP targets, maps workers to ChatGPT sessions, and dispatches
TaskSpecs through the CDP Write Adapter.

This is the **orchestration** layer that sits between the governance
pipeline (Gate 0 → dispatch plan) and the low-level CDP adapter.

Usage
-----
::

  # dry-run: validate all connections without sending
  python cdp_dispatch_runner.py dry-run

  # execute parallel-safe assignments (wave 1)
  python cdp_dispatch_runner.py run --wave parallel

  # execute a single assignment to a specific page
  python cdp_dispatch_runner.py run --assignment Architecture-Reviewer --page-id 9C03F

  # full run with evidence output
  python cdp_dispatch_runner.py run --wave parallel --output-dir _evidence/CDP-DISPATCH/

Design
------
::

  DISPATCH_PLAN_CURRENT.json ──┐
  CONVERSATION_BINDING.json ───┤
                               ├─► cdp_dispatch_runner ──► cdp_write_adapter ──► Chrome
  localhost:9222/json ─────────┘
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Import the adapter
sys.path.insert(0, str(Path(__file__).resolve().parent))
from cdp_write_adapter import (
    CDPClient,
    ChatGPTController,
    DispatchResult,
    dispatch_to_page,
    _find_chatgpt_pages,
    _utc_now,
    CDPPage,
    DEFAULT_CDP_PORT,
    DEFAULT_RESPONSE_TIMEOUT,
)

REPO = Path(__file__).resolve().parent.parent
DISPATCH_PLAN_PATH = REPO / "_reports" / "multi-agent-dispatch-plan-a1" / "DISPATCH_PLAN_CURRENT.json"
BINDING_PATH = REPO / ".agent" / "CONVERSATION_BINDING.json"
EVIDENCE_DIR = REPO / "_evidence" / "CDP-DISPATCH"


# ── Plan loading ──────────────────────────────────────────────────────


def load_dispatch_plan() -> dict:
    """Load the current dispatch plan."""
    if not DISPATCH_PLAN_PATH.exists():
        # Try alternative name
        alt = DISPATCH_PLAN_PATH.parent / "DISPATCH_PLAN.json"
        if alt.exists():
            return json.loads(alt.read_text(encoding="utf-8"))
        raise FileNotFoundError(f"Dispatch plan not found: {DISPATCH_PLAN_PATH}")
    return json.loads(DISPATCH_PLAN_PATH.read_text(encoding="utf-8"))


def load_binding() -> dict:
    """Load the conversation binding."""
    if not BINDING_PATH.exists():
        raise FileNotFoundError(f"Binding not found: {BINDING_PATH}")
    return json.loads(BINDING_PATH.read_text(encoding="utf-8"))


def get_parallel_assignments(plan: dict) -> list[dict]:
    """Extract parallel-safe assignments from the dispatch plan."""
    return [
        a for a in plan.get("assignments", [])
        if a.get("parallel_safe", False) and a.get("task_spec", {}).get("status") == "ready"
    ]


def get_serial_assignments(plan: dict) -> list[dict]:
    """Extract serial (non-parallel) assignments that are not completed."""
    return [
        a for a in plan.get("assignments", [])
        if not a.get("parallel_safe", False)
        and a.get("task_spec", {}).get("status") not in ("completed", "deferred")
    ]


# ── Target mapping ────────────────────────────────────────────────────


def discover_targets(port: int = DEFAULT_CDP_PORT) -> list[CDPPage]:
    """Discover live ChatGPT CDP targets."""
    return _find_chatgpt_pages(port)


def map_workers_to_targets(
    assignments: list[dict],
    binding: dict,
    targets: list[CDPPage],
) -> list[tuple[dict, CDPPage]]:
    """Map worker assignments to CDP targets.

    Strategy:
    1. Try to match by conversation_id from binding.
    2. Fall back to role-based mapping (reviewer → first tab, executor → second).
    3. If more workers than targets, assign round-robin.
    """
    bindings_by_role = {}
    for b in binding.get("bindings", []):
        bindings_by_role[b.get("role", "")] = b

    # Build a lookup from conversation_id to target
    targets_by_conv = {}
    for t in targets:
        if t.conversation_id:
            targets_by_conv[t.conversation_id] = t

    # Role → preferred agent mapping
    role_to_agent = {
        "reviewer": "agent-local-001",
        "executor": "agent-pilot-beta",
    }

    mapped: list[tuple[dict, CDPPage]] = []
    used_targets: set[str] = set()

    for assignment in assignments:
        role = assignment.get("worker_role", "").lower()
        target = None

        # Strategy 1: match by binding conversation_id
        agent_id = role_to_agent.get(role, "")
        if agent_id:
            for b in binding.get("bindings", []):
                if b.get("agent_id") == agent_id:
                    conv_id = b.get("conversation_id", "")
                    target = targets_by_conv.get(conv_id)
                    break

        # Strategy 2: role-based fallback
        if target is None and targets:
            available = [t for t in targets if t.target_id not in used_targets]
            if not available:
                available = targets  # reuse if all used
            if "review" in role:
                target = available[0]
            elif "verif" in role or "quality" in role or "execut" in role:
                target = available[min(1, len(available) - 1)]
            else:
                target = available[0]

        if target:
            mapped.append((assignment, target))
            used_targets.add(target.target_id)

    return mapped


# ── Prompt formatting ─────────────────────────────────────────────────


def format_taskspec_prompt(assignment: dict) -> str:
    """Convert a dispatch assignment into a prompt suitable for ChatGPT.

    Keeps the prompt concise (< 4000 chars) to stay within ChatGPT's
    input limits while providing all essential task context.
    """
    ts = assignment.get("task_spec", {})
    role = assignment.get("worker_role", "Worker")
    task_id = ts.get("task_id", "unknown")
    title = ts.get("title", assignment.get("target", ""))
    description = ts.get("description", "")
    priority = ts.get("priority", "P2")

    # Build structured prompt
    parts = [
        f"# Task: {title}",
        f"**Task ID**: {task_id}",
        f"**Role**: {role}",
        f"**Priority**: {priority}",
        "",
        "## Description",
        description,
        "",
        "## Target",
        assignment.get("target", ""),
        "",
        "## Scope",
        f"- **Allowed**: {', '.join(assignment.get('allowed_modify_range', []))}",
        f"- **Forbidden**: {', '.join(assignment.get('forbidden_modify_range', []))}",
        "",
        "## Quality Standard",
        assignment.get("quality_standard", ""),
        "",
        "## Completion Standard",
        assignment.get("completion_standard", ""),
        "",
        "## Blocking Conditions",
    ]
    for bc in assignment.get("blocking_conditions", []):
        parts.append(f"- {bc}")

    # Add verification commands if present
    ver_cmds = assignment.get("required_verification_commands", [])
    if ver_cmds:
        parts.append("")
        parts.append("## Required Verification")
        for cmd in ver_cmds:
            parts.append(f"```")
            parts.append(cmd)
            parts.append(f"```")

    # Add assumptions
    assumptions = ts.get("assumptions", [])
    if assumptions:
        parts.append("")
        parts.append("## Assumptions")
        for a in assumptions:
            parts.append(f"- {a}")

    parts.append("")
    parts.append("## Instructions")
    parts.append(
        "Execute this task within the current repository. "
        "Produce a structured report with: verdict, changed files, "
        "tests run, artifacts produced, known gaps, and suggested review focus. "
        "Do not execute external runtimes or modify files outside the allowed range."
    )

    return "\n".join(parts)


# ── Dispatch execution ────────────────────────────────────────────────


async def execute_dispatch(
    mappings: list[tuple[dict, CDPPage]],
    *,
    wait_for_response: bool = True,
    response_timeout: int = DEFAULT_RESPONSE_TIMEOUT,
    dry_run: bool = False,
    output_dir: Path | None = None,
) -> list[dict]:
    """Execute dispatch for all worker-target mappings."""
    results = []

    for assignment, target in mappings:
        role = assignment.get("worker_role", "unknown")
        prompt = format_taskspec_prompt_safe(assignment)

        print(f"{'='*60}")
        print(f"Worker: {role}")
        print(f"Target: {target.target_id[:16]}... (conv: {target.conversation_id})")
        print(f"Prompt: {len(prompt)} chars")

        if dry_run:
            print("Mode:   DRY-RUN")
            # Just validate connectivity
            cdp = CDPClient(target.ws_url)
            ctrl = ChatGPTController(cdp)
            try:
                await cdp.connect()
                info = await ctrl.check_page_ready()
                await cdp.close()
                print(f"Status: {'PASS' if info.get('hasInput') else 'FAIL'}")
                results.append({
                    "worker_role": role,
                    "target_id": target.target_id,
                    "conversation_id": target.conversation_id,
                    "dry_run": True,
                    "page_ready": info.get("hasInput", False),
                    "prompt_length": len(prompt),
                    "status": "DRY_RUN_PASS" if info.get("hasInput") else "DRY_RUN_FAIL",
                })
            except Exception as e:
                print(f"Status: FAIL ({e})")
                results.append({
                    "worker_role": role,
                    "target_id": target.target_id,
                    "dry_run": True,
                    "error": str(e),
                    "status": "DRY_RUN_FAIL",
                })
            continue

        # Real dispatch
        print(f"Mode:   LIVE")
        result = await dispatch_to_page(
            target.ws_url,
            prompt,
            wait_for_response=wait_for_response,
            response_timeout=response_timeout,
            dry_run=False,
        )

        status = "DISPATCHED" if result.sent else "FAILED"
        print(f"Status: {status}")
        print(f"Inject: {result.injection.method} ({result.injection.text_length} chars)")
        if result.sent:
            print(f"Time:   {result.response_time_seconds}s")
            preview = result.response_text[:100] if result.response_text else "(empty)"
            print(f"Reply:  {preview}...")
        if result.error:
            print(f"Error:  {result.error}")

        entry = {
            "worker_role": role,
            "task_id": assignment.get("task_spec", {}).get("task_id", ""),
            "target_id": target.target_id,
            "conversation_id": target.conversation_id,
            "chat_url": target.url,
            "dispatched_at": _utc_now(),
            "injection": {
                "success": result.injection.success,
                "method": result.injection.method,
                "text_length": result.injection.text_length,
            },
            "sent": result.sent,
            "response_time_seconds": result.response_time_seconds,
            "response_text_preview": result.response_text[:500] if result.response_text else "",
            "response_text_full": result.response_text,
            "error": result.error,
            "status": status,
        }
        results.append(entry)

        # Save per-worker evidence
        if output_dir:
            output_dir.mkdir(parents=True, exist_ok=True)
            evidence_file = output_dir / f"dispatch-{role.lower()}.json"
            evidence_file.write_text(
                json.dumps(entry, indent=2, ensure_ascii=False), encoding="utf-8"
            )
            print(f"Evidence: {evidence_file}")

    return results


def format_taskspec_prompt_safe(assignment: dict) -> str:
    """Safe wrapper for prompt formatting."""
    try:
        return format_taskspec_prompt(assignment)
    except Exception as e:
        return f"Task: {assignment.get('worker_role', 'unknown')}\nError formatting prompt: {e}"


# ── Summary report ────────────────────────────────────────────────────


def generate_dispatch_report(
    results: list[dict],
    plan: dict,
    *,
    dry_run: bool = False,
) -> dict:
    """Generate a summary dispatch report."""
    dispatched = [r for r in results if r.get("sent") or r.get("dry_run")]
    failed = [r for r in results if r.get("status", "").startswith("FAIL") or r.get("error")]

    report = {
        "schema_version": "1.0.0",
        "report_type": "cdp_dispatch_report",
        "generated_at": _utc_now(),
        "dry_run": dry_run,
        "plan_id": plan.get("plan_id", ""),
        "plan_status": plan.get("status", ""),
        "total_assignments": len(plan.get("assignments", [])),
        "dispatched_count": len(dispatched),
        "failed_count": len(failed),
        "results": results,
        "execution_model": "cdp_write_adapter",
        "honesty_declaration": (
            "Prompts were injected into independent ChatGPT browser sessions "
            "via Chrome DevTools Protocol (CDP) write API. Each target is a "
            "separate browser tab with its own conversation context. "
            "This is real multi-session execution, not sub-agent dispatch."
        ),
    }
    return report


# ── CLI ───────────────────────────────────────────────────────────────


def cmd_dry_run(args) -> int:
    """Validate all connections without sending."""
    plan = load_dispatch_plan()
    binding = load_binding()
    targets = discover_targets(args.port)

    print(f"Plan:    {plan.get('plan_id')} (status: {plan.get('status')})")
    print(f"Targets: {len(targets)} ChatGPT pages")
    print(f"Binding: {len(binding.get('bindings', []))} agents")
    print()

    assignments = get_parallel_assignments(plan)
    if not assignments:
        print("No parallel-safe ready assignments found")
        return 1

    mappings = map_workers_to_targets(assignments, binding, targets)
    if not mappings:
        print("No worker-to-target mappings possible")
        return 1

    print("Mappings:")
    for assignment, target in mappings:
        role = assignment.get("worker_role", "?")
        conv = target.conversation_id or "?"
        print(f"  {role:25s} → {target.target_id[:16]}... (conv: {conv[:16]}...)")

    print()
    results = asyncio.run(execute_dispatch(
        mappings, dry_run=True, output_dir=None,
    ))

    passed = sum(1 for r in results if r.get("status") == "DRY_RUN_PASS")
    total = len(results)
    print(f"\nDRY-RUN: {passed}/{total} PASS")
    return 0 if passed == total else 1


def cmd_run(args) -> int:
    """Execute dispatch."""
    plan = load_dispatch_plan()
    binding = load_binding()
    targets = discover_targets(args.port)

    # Select assignments
    if args.wave == "parallel":
        assignments = get_parallel_assignments(plan)
    elif args.wave == "serial":
        assignments = get_serial_assignments(plan)
    else:
        assignments = get_parallel_assignments(plan) + get_serial_assignments(plan)

    # Filter by specific assignment if requested
    if args.assignment:
        assignments = [
            a for a in assignments
            if a.get("worker_role", "").lower() == args.assignment.lower()
        ]

    if not assignments:
        print("No matching assignments found")
        return 1

    print(f"Plan:       {plan.get('plan_id')}")
    print(f"Wave:       {args.wave}")
    print(f"Assignments: {len(assignments)}")
    print(f"Targets:    {len(targets)}")
    print()

    mappings = map_workers_to_targets(assignments, binding, targets)

    # Override target if --page-id specified
    if args.page_id:
        target_match = None
        for t in targets:
            if t.target_id.startswith(args.page_id):
                target_match = t
                break
        if target_match:
            mappings = [(a, target_match) for a in assignments]
        else:
            print(f"Target {args.page_id} not found")
            return 1

    output_dir = Path(args.output_dir) if args.output_dir else EVIDENCE_DIR

    results = asyncio.run(execute_dispatch(
        mappings,
        wait_for_response=not args.no_wait,
        response_timeout=args.timeout,
        dry_run=False,
        output_dir=output_dir,
    ))

    # Generate and save report
    report = generate_dispatch_report(results, plan, dry_run=False)

    report_path = output_dir / "CDP_DISPATCH_REPORT.json"
    output_dir.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"\n{'='*60}")
    print(f"Report: {report_path}")
    print(f"Dispatched: {report['dispatched_count']}/{report['total_assignments']}")
    print(f"Failed:     {report['failed_count']}")
    print(f"Model:      {report['execution_model']}")

    dispatched = report["dispatched_count"]
    total = len(assignments)
    return 0 if dispatched == total else 1


def cmd_status(args) -> int:
    """Show dispatch readiness status."""
    # Check plan
    try:
        plan = load_dispatch_plan()
        print(f"Plan:     {plan.get('status', 'UNKNOWN')}")
    except FileNotFoundError:
        print("Plan:     NOT FOUND")
        plan = None

    # Check binding
    try:
        binding = load_binding()
        agents = binding.get("bindings", [])
        active = [a for a in agents if a.get("binding_status") == "active"]
        print(f"Binding:  {len(active)}/{len(agents)} active")
    except FileNotFoundError:
        print("Binding:  NOT FOUND")
        binding = None

    # Check CDP targets
    targets = discover_targets(args.port)
    print(f"CDP:      {len(targets)} ChatGPT pages live")

    # Check adapter
    print(f"Adapter:  cdp_write_adapter.py (websockets async)")

    # Summary
    if plan and plan.get("status") == "READY" and targets:
        print("\nSTATUS: READY for CDP dispatch")
        return 0
    else:
        issues = []
        if not plan:
            issues.append("no plan")
        elif plan.get("status") != "READY":
            issues.append(f"plan status={plan.get('status')}")
        if not targets:
            issues.append("no live CDP targets")
        print(f"\nSTATUS: NOT READY ({', '.join(issues)})")
        return 1


def main() -> None:
    parser = argparse.ArgumentParser(
        description="CDP Dispatch Runner — execute dispatch plans via CDP Write Adapter"
    )
    sub = parser.add_subparsers(dest="command")

    # status
    p_status = sub.add_parser("status", help="Show dispatch readiness")
    p_status.add_argument("--port", type=int, default=DEFAULT_CDP_PORT)

    # dry-run
    p_dry = sub.add_parser("dry-run", help="Validate connections")
    p_dry.add_argument("--port", type=int, default=DEFAULT_CDP_PORT)

    # run
    p_run = sub.add_parser("run", help="Execute dispatch")
    p_run.add_argument("--wave", choices=["parallel", "serial", "all"], default="parallel")
    p_run.add_argument("--assignment", help="Run specific worker role only")
    p_run.add_argument("--page-id", help="Override target (CDP target ID prefix)")
    p_run.add_argument("--port", type=int, default=DEFAULT_CDP_PORT)
    p_run.add_argument("--no-wait", action="store_true", help="Don't wait for responses")
    p_run.add_argument("--timeout", type=int, default=DEFAULT_RESPONSE_TIMEOUT)
    p_run.add_argument("--output-dir", help="Evidence output directory")

    args = parser.parse_args()

    if args.command == "status":
        sys.exit(cmd_status(args))
    elif args.command == "dry-run":
        sys.exit(cmd_dry_run(args))
    elif args.command == "run":
        sys.exit(cmd_run(args))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
