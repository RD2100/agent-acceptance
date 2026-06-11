"""Pre-GPT Gate for Conversation Health -- CONVERSATION-HEALTH-GATE-A2.

Provides a unified gate module that all GPT/CDP submission scripts must call
before interacting with ChatGPT.  Connects the A1 decision engine
(``check_handoff_needed.check_handoff_v2``) to real GPT/CDP workflows.

Public API (for legacy script integration)
------------------------------------------
    from pre_gpt_gate import check_pre_gpt_gate

    exit_code, decision, message = check_pre_gpt_gate()
    if exit_code != 0:
        print(f"BLOCKED: {message}")
        sys.exit(exit_code)

CLI
---
    # Pre-submit check (reads current.json, writes latest.json)
    python pre_gpt_gate.py check

    # Refresh current.json with new metrics
    python pre_gpt_gate.py refresh --metrics '{"assistant_message_count": 15, ...}'

    # Full gate: check + optional refresh
    python pre_gpt_gate.py gate --metrics-file metrics.json

    # Record navigation result
    python pre_gpt_gate.py nav-result --result access_denied

Exit Codes
----------
    0 -- OK or SUGGEST (submission allowed)
    1 -- FORCE_HANDOFF (submission blocked)
    2 -- HUMAN_REQUIRED (submission blocked, human intervention needed)
    3 -- Missing current.json with no refresh path (submission blocked)
    4 -- Stale metrics with failed refresh (submission blocked or warning)
"""

import argparse
import json
import os
import sys
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

REPO = Path(__file__).resolve().parent.parent
CURRENT_JSON = REPO / ".ai" / "conversation" / "current.json"
POLICY_YAML = REPO / "configs" / "conversation-health-policy.yaml"
EVIDENCE_DIR = REPO / "_evidence" / "conversation-health"
LATEST_JSON = EVIDENCE_DIR / "latest.json"
SNAPSHOT_JSON = EVIDENCE_DIR / "current-snapshot.json"
MIGRATION_DIR = EVIDENCE_DIR / "migration-records"

# Exit codes
EXIT_OK = 0
EXIT_SUGGEST = 0          # SUGGEST still allows submission
EXIT_FORCE = 1
EXIT_HUMAN_REQUIRED = 2
EXIT_MISSING_BLOCKED = 3
EXIT_STALE_BLOCKED = 4


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _now_iso():
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def _load_current_json(path=None):
    """Load .ai/conversation/current.json.

    Returns (data_dict, error_string_or_None).
    """
    p = Path(path) if path else CURRENT_JSON
    if not p.is_file():
        return None, f"current.json not found: {p}"
    try:
        text = p.read_text(encoding="utf-8")
        data = json.loads(text)
        if not isinstance(data, dict):
            return None, f"current.json must contain a JSON object"
        return data, None
    except json.JSONDecodeError as exc:
        return None, f"Invalid JSON in current.json: {exc}"
    except OSError as exc:
        return None, f"Cannot read current.json: {exc}"


def _write_json(path, data):
    """Write a dict as formatted JSON."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n",
                 encoding="utf-8")


def _import_decision_engine():
    """Import check_handoff_v2 and load_policy from check_handoff_needed.

    Returns (check_handoff_v2, load_policy, error_string_or_None).
    """
    scripts_dir = str(REPO / "scripts")
    added = False
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
        added = True
    try:
        from check_handoff_needed import check_handoff_v2, load_policy  # type: ignore
        return check_handoff_v2, load_policy, None
    except ImportError as exc:
        return None, None, f"Cannot import decision engine: {exc}"
    finally:
        if added and scripts_dir in sys.path:
            sys.path.remove(scripts_dir)


def _flatten_metrics(current_data):
    """Extract a flat metrics dict from current.json data for check_handoff_v2.

    Handles the field name mapping: schema uses last_response_time_seconds,
    decision engine uses response_time_seconds.
    """
    lkm = current_data.get("last_known_metrics", {})
    metrics = {
        "assistant_message_count": lkm.get("assistant_message_count"),
        "response_time_seconds": lkm.get("last_response_time_seconds"),
        "review_round_count": lkm.get("review_round_count"),
        "last_gpt_reply_bytes": lkm.get("last_gpt_reply_bytes"),
        "metrics_source": current_data.get("metrics_source", "none"),
        "nav_result": current_data.get("last_nav_result", "unknown"),
        "last_checked_at": current_data.get("last_checked_at"),
    }
    return metrics


def _decision_to_exit_code(decision):
    """Map a decision string to an exit code."""
    d = decision.get("decision", "UNKNOWN") if isinstance(decision, dict) else str(decision)
    if d == "FORCE_HANDOFF":
        return EXIT_FORCE
    elif d == "HUMAN_REQUIRED":
        return EXIT_HUMAN_REQUIRED
    elif d == "UNKNOWN":
        # UNKNOWN with BLOCKING severity -> block
        sev = decision.get("severity", "") if isinstance(decision, dict) else ""
        if sev == "BLOCKING":
            return EXIT_MISSING_BLOCKED
        return EXIT_OK
    else:
        # OK, SUGGEST_HANDOFF
        return EXIT_OK


def _decision_to_message(decision):
    """Build a human-readable message from a decision."""
    d = decision.get("decision", "UNKNOWN") if isinstance(decision, dict) else "UNKNOWN"
    reasons = decision.get("reasons", []) if isinstance(decision, dict) else []
    reason_strs = []
    for r in reasons:
        if isinstance(r, dict):
            reason_strs.append(f"{r.get('code', '?')}: {r.get('actual', '?')} "
                               f"(threshold: {r.get('threshold', '?')}, "
                               f"policy: {r.get('policy', '?')})")
        else:
            reason_strs.append(str(r))
    if reason_strs:
        return f"{d}: {'; '.join(reason_strs)}"
    return d


# ---------------------------------------------------------------------------
# Core API: check_pre_gpt_gate()
# ---------------------------------------------------------------------------

def check_pre_gpt_gate(current_json_path=None, policy_path=None, evidence_dir=None,
                       *, allow_init=False):
    """Run the Pre-GPT gate check.

    This is the primary entry point for legacy script integration.

    Parameters
    ----------
    current_json_path : str or Path, optional
        Path to current.json. Defaults to .ai/conversation/current.json.
    policy_path : str or Path, optional
        Path to policy YAML. Defaults to configs/conversation-health-policy.yaml.
    evidence_dir : str or Path, optional
        Directory for evidence output. Defaults to _evidence/conversation-health/.
    allow_init : bool
        If True and current.json is missing, initialize it from template.

    Returns
    -------
    (exit_code, decision, message) : tuple[int, dict, str]
        exit_code: 0=OK/SUGGEST (proceed), 1=FORCE (blocked),
                   2=HUMAN_REQUIRED (blocked), 3=missing (blocked)
        decision: v2 decision dict from check_handoff_v2
        message: human-readable summary
    """
    c_path = Path(current_json_path) if current_json_path else CURRENT_JSON
    p_path = Path(policy_path) if policy_path else POLICY_YAML
    e_dir = Path(evidence_dir) if evidence_dir else EVIDENCE_DIR

    # 1. Load current.json
    current_data, load_err = _load_current_json(c_path)
    if current_data is None:
        if allow_init:
            # Try to initialize from template
            current_data = _init_current_json(c_path)
            if current_data is None:
                return (EXIT_MISSING_BLOCKED,
                        {"decision": "UNKNOWN", "severity": "BLOCKING",
                         "reasons": [{"code": "init_failed", "actual": "none",
                                      "threshold": "current.json", "policy": "force"}]},
                        f"BLOCKED: Cannot initialize current.json: {load_err}")
        else:
            return (EXIT_MISSING_BLOCKED,
                    {"decision": "UNKNOWN", "severity": "BLOCKING",
                     "reasons": [{"code": "missing_current_json", "actual": "none",
                                  "threshold": "current.json", "policy": "force"}]},
                    f"BLOCKED: {load_err}")

    # 2. Import decision engine
    check_v2, load_policy_fn, import_err = _import_decision_engine()
    if check_v2 is None:
        return (EXIT_MISSING_BLOCKED,
                {"decision": "UNKNOWN", "severity": "BLOCKING",
                 "reasons": [{"code": "engine_import_failed", "actual": "error",
                              "threshold": "check_handoff_needed", "policy": "force"}]},
                f"BLOCKED: {import_err}")

    # 3. Load policy
    policy = None
    if p_path.is_file():
        try:
            policy = load_policy_fn(str(p_path))
        except Exception:
            policy = None  # Will fall back to DEFAULT_POLICY

    # 4. Flatten metrics
    metrics = _flatten_metrics(current_data)

    # 5. Run decision engine
    decision = check_v2(
        metrics=metrics,
        policy=policy,
        mode="pre-gpt",
        max_staleness_hours=None,  # Use policy default
        composite=True,
        source_label="pre_gpt_gate",
    )

    # 6. Write evidence files
    _write_latest_json(e_dir, current_data, decision)
    _write_snapshot_json(e_dir, current_data)

    # 7. Map to exit code
    exit_code = _decision_to_exit_code(decision)
    message = _decision_to_message(decision)

    if exit_code == EXIT_OK:
        d = decision.get("decision", "OK")
        if d == "SUGGEST_HANDOFF":
            message = f"SUGGEST (proceed with caution): {message}"
        else:
            message = f"OK: {message}" if message else "OK"

    return exit_code, decision, message


# ---------------------------------------------------------------------------
# Core API: update_metrics()
# ---------------------------------------------------------------------------

def update_metrics(current_json_path=None, new_metrics=None, nav_result=None,
                   source=None):
    """Update current.json with new metrics.

    Parameters
    ----------
    current_json_path : str or Path, optional
        Path to current.json. Defaults to .ai/conversation/current.json.
    new_metrics : dict, optional
        New metrics to merge. Keys should use schema field names:
        assistant_message_count, review_round_count,
        last_response_time_seconds, last_gpt_reply_bytes.
    nav_result : str, optional
        Navigation result: ok, access_denied, not_found, timeout,
        auth_required, cdp_unavailable, unknown.
    source : str, optional
        Metrics source label: cdp_dom_count, wrapper_counter,
        manual_estimate, none.

    Returns
    -------
    (updated_data, error_string_or_None) : tuple[dict, str or None]
    """
    c_path = Path(current_json_path) if current_json_path else CURRENT_JSON

    current_data, load_err = _load_current_json(c_path)
    if current_data is None:
        # Initialize if missing
        current_data = _init_current_json(c_path)
        if current_data is None:
            return None, load_err

    data = deepcopy(current_data)

    # Update metrics
    if new_metrics:
        lkm = data.setdefault("last_known_metrics", {})
        for key in ("assistant_message_count", "review_round_count",
                     "last_response_time_seconds", "last_gpt_reply_bytes"):
            if key in new_metrics and new_metrics[key] is not None:
                lkm[key] = new_metrics[key]

    # Update nav result
    if nav_result is not None:
        data["last_nav_result"] = nav_result

    # Update source
    if source is not None:
        data["metrics_source"] = source

    # Update timestamp and freshness
    data["last_checked_at"] = _now_iso()
    data["metrics_freshness"] = "fresh"

    # Write back
    _write_json(c_path, data)

    return data, None


# ---------------------------------------------------------------------------
# Core API: record_nav_result()
# ---------------------------------------------------------------------------

def record_nav_result(nav_result, current_json_path=None, evidence_dir=None):
    """Record a navigation result and update evidence.

    Used when CDP navigation fails (access_denied, auth_required, etc.)
    even if no full metrics refresh was possible.

    Returns (exit_code, decision, message) tuple.
    """
    c_path = Path(current_json_path) if current_json_path else CURRENT_JSON
    e_dir = Path(evidence_dir) if evidence_dir else EVIDENCE_DIR

    # Update current.json with nav result
    updated, err = update_metrics(c_path, nav_result=nav_result)
    if err:
        return EXIT_MISSING_BLOCKED, {"decision": "UNKNOWN"}, f"NAV RECORD FAILED: {err}"

    # Re-run gate check to get updated decision
    return check_pre_gpt_gate(c_path, evidence_dir=e_dir)


# ---------------------------------------------------------------------------
# Core API: capture_cdp_metrics()
# ---------------------------------------------------------------------------

async def capture_cdp_metrics(page, chat_url=None):
    """Capture conversation metrics from a ChatGPT CDP page.

    Parameters
    ----------
    page : playwright Page
        The browser page with ChatGPT loaded.
    chat_url : str, optional
        Expected chat URL for conversation ID extraction.

    Returns
    -------
    dict with keys: assistant_message_count, last_gpt_reply_bytes,
                    last_response_time_seconds, nav_result, source.
    """
    metrics = {
        "assistant_message_count": None,
        "last_gpt_reply_bytes": None,
        "last_response_time_seconds": None,
        "nav_result": "ok",
        "source": "cdp_dom_count",
    }

    try:
        # Count assistant messages
        assistant_msgs = page.locator('div[data-message-author-role="assistant"]')
        msg_count = await assistant_msgs.count()
        metrics["assistant_message_count"] = msg_count

        # Get last reply size
        if msg_count > 0:
            last_reply_text = await assistant_msgs.last.inner_text()
            metrics["last_gpt_reply_bytes"] = len(last_reply_text.encode("utf-8"))

    except Exception as exc:
        metrics["nav_result"] = "cdp_unavailable"
        metrics["source"] = "none"

    return metrics


# ---------------------------------------------------------------------------
# Internal: init current.json
# ---------------------------------------------------------------------------

def _init_current_json(path=None):
    """Initialize current.json from the example template.

    Returns the initialized data dict, or None on failure.
    """
    p = Path(path) if path else CURRENT_JSON
    example = REPO / ".ai" / "conversation" / "current.json.example"

    if example.is_file():
        try:
            data = json.loads(example.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            data = None
    else:
        data = None

    if data is None:
        # Fallback minimal template
        data = {
            "schema_version": "conversation-health.v1",
            "conversation_id": "unknown",
            "chat_url": "https://chatgpt.com/",
            "status": "active",
            "last_known_metrics": {
                "assistant_message_count": 0,
                "review_round_count": 0,
                "last_response_time_seconds": 0,
                "last_gpt_reply_bytes": 0,
            },
            "last_nav_result": "unknown",
            "last_checked_at": _now_iso(),
            "metrics_source": "none",
            "metrics_freshness": "unknown",
        }
    else:
        data["last_checked_at"] = _now_iso()

    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        _write_json(p, data)
        return data
    except OSError:
        return None


# ---------------------------------------------------------------------------
# Internal: write evidence files
# ---------------------------------------------------------------------------

def _write_latest_json(e_dir, current_data, decision):
    """Write _evidence/conversation-health/latest.json.

    Combines current.json state with the decision output so that
    build_evidence_pack.py can find both ``last_health_decision`` and
    ``decision`` fields.
    """
    e_path = Path(e_dir)
    e_path.mkdir(parents=True, exist_ok=True)

    # Start from current data, add decision fields
    output = deepcopy(current_data)
    output["last_health_decision"] = decision.get("decision", "UNKNOWN")
    output["last_health_reasons"] = [
        r.get("code", str(r)) if isinstance(r, dict) else str(r)
        for r in decision.get("reasons", [])
    ]
    output["last_health_severity"] = decision.get("severity", "INFO")
    output["last_health_checked_at"] = decision.get("checked_at", _now_iso())

    _write_json(e_path / "latest.json", output)


def _write_snapshot_json(e_dir, current_data):
    """Write _evidence/conversation-health/current-snapshot.json.

    A point-in-time copy of current.json for evidence trail.
    """
    e_path = Path(e_dir)
    e_path.mkdir(parents=True, exist_ok=True)

    snapshot = deepcopy(current_data)
    snapshot["_snapshot_at"] = _now_iso()
    snapshot["_snapshot_source"] = "pre_gpt_gate"

    _write_json(e_path / "current-snapshot.json", snapshot)


# ---------------------------------------------------------------------------
# Internal: write migration record
# ---------------------------------------------------------------------------

def write_migration_record(old_conversation_id, new_conversation_id,
                           reason="manual", evidence_dir=None):
    """Record a conversation switch event.

    Writes a YAML file to _evidence/conversation-health/migration-records/.
    """
    e_dir = Path(evidence_dir) if evidence_dir else MIGRATION_DIR
    e_dir.mkdir(parents=True, exist_ok=True)

    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    record = {
        "timestamp": _now_iso(),
        "old_conversation_id": old_conversation_id,
        "new_conversation_id": new_conversation_id,
        "reason": reason,
    }

    # Write as simple YAML (no dependency on PyYAML)
    lines = [
        f"timestamp: \"{record['timestamp']}\"",
        f"old_conversation_id: \"{record['old_conversation_id']}\"",
        f"new_conversation_id: \"{record['new_conversation_id']}\"",
        f"reason: \"{record['reason']}\"",
    ]
    (e_dir / f"{ts}.yaml").write_text("\n".join(lines) + "\n", encoding="utf-8")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _build_parser():
    parser = argparse.ArgumentParser(
        description="Pre-GPT Gate for Conversation Health (A2)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(dest="command", help="Available commands")

    # check
    chk = sub.add_parser("check", help="Pre-submit gate check")
    chk.add_argument("--input", default=str(CURRENT_JSON),
                     help="Path to current.json")
    chk.add_argument("--policy", default=str(POLICY_YAML),
                     help="Path to policy YAML")
    chk.add_argument("--evidence-dir", default=str(EVIDENCE_DIR),
                     help="Evidence output directory")
    chk.add_argument("--allow-init", action="store_true",
                     help="Initialize current.json if missing")
    chk.add_argument("--json", action="store_true", dest="json_output",
                     help="Output decision as JSON")

    # refresh
    ref = sub.add_parser("refresh", help="Refresh current.json with new metrics")
    ref.add_argument("--input", default=str(CURRENT_JSON),
                     help="Path to current.json")
    ref.add_argument("--metrics", help="JSON string of new metrics")
    ref.add_argument("--metrics-file", help="JSON file with new metrics")
    ref.add_argument("--nav-result", help="Navigation result string")
    ref.add_argument("--source", help="Metrics source label")

    # gate (combined check + refresh)
    gate = sub.add_parser("gate", help="Full gate: refresh then check")
    gate.add_argument("--input", default=str(CURRENT_JSON),
                      help="Path to current.json")
    gate.add_argument("--policy", default=str(POLICY_YAML),
                      help="Path to policy YAML")
    gate.add_argument("--evidence-dir", default=str(EVIDENCE_DIR),
                      help="Evidence output directory")
    gate.add_argument("--metrics", help="JSON string of new metrics")
    gate.add_argument("--metrics-file", help="JSON file with new metrics")
    gate.add_argument("--nav-result", help="Navigation result string")
    gate.add_argument("--source", help="Metrics source label")
    gate.add_argument("--allow-init", action="store_true",
                      help="Initialize current.json if missing")
    gate.add_argument("--json", action="store_true", dest="json_output",
                      help="Output decision as JSON")

    # nav-result
    nav = sub.add_parser("nav-result", help="Record a navigation result")
    nav.add_argument("--input", default=str(CURRENT_JSON),
                     help="Path to current.json")
    nav.add_argument("--evidence-dir", default=str(EVIDENCE_DIR),
                     help="Evidence output directory")
    nav.add_argument("--result", required=True,
                     help="Navigation result: ok, access_denied, auth_required, etc.")
    nav.add_argument("--json", action="store_true", dest="json_output",
                     help="Output decision as JSON")

    return parser


def _load_metrics_arg(args):
    """Load metrics from --metrics or --metrics-file."""
    new_metrics = None
    if hasattr(args, "metrics_file") and args.metrics_file:
        try:
            new_metrics = json.loads(Path(args.metrics_file).read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            print(f"ERROR: Cannot load metrics file: {exc}", file=sys.stderr)
            sys.exit(2)
    elif hasattr(args, "metrics") and args.metrics:
        try:
            new_metrics = json.loads(args.metrics)
        except json.JSONDecodeError as exc:
            print(f"ERROR: Invalid metrics JSON: {exc}", file=sys.stderr)
            sys.exit(2)
    return new_metrics


def _output_result(exit_code, decision, message, json_output=False):
    """Print and exit with the result."""
    if json_output:
        output = {
            "exit_code": exit_code,
            "decision": decision,
            "message": message,
        }
        print(json.dumps(output, indent=2, ensure_ascii=False))
    else:
        print(message)
    sys.exit(exit_code)


def main():
    parser = _build_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    if args.command == "check":
        exit_code, decision, message = check_pre_gpt_gate(
            current_json_path=args.input,
            policy_path=args.policy,
            evidence_dir=args.evidence_dir,
            allow_init=args.allow_init,
        )
        _output_result(exit_code, decision, message, args.json_output)

    elif args.command == "refresh":
        new_metrics = _load_metrics_arg(args)
        nav_result = getattr(args, "nav_result", None)
        source = getattr(args, "source", None)
        updated, err = update_metrics(
            current_json_path=args.input,
            new_metrics=new_metrics,
            nav_result=nav_result,
            source=source,
        )
        if err:
            print(f"ERROR: {err}", file=sys.stderr)
            sys.exit(2)
        print(f"current.json updated: {json.dumps(updated.get('last_known_metrics', {}))}")
        sys.exit(0)

    elif args.command == "gate":
        # Step 1: Refresh if metrics provided
        new_metrics = _load_metrics_arg(args)
        nav_result = getattr(args, "nav_result", None)
        source = getattr(args, "source", None)

        if new_metrics or nav_result or source:
            updated, err = update_metrics(
                current_json_path=args.input,
                new_metrics=new_metrics,
                nav_result=nav_result,
                source=source,
            )
            if err:
                print(f"WARNING: Metrics refresh failed: {err}", file=sys.stderr)
                # Continue with check even if refresh fails

        # Step 2: Check
        exit_code, decision, message = check_pre_gpt_gate(
            current_json_path=args.input,
            policy_path=args.policy,
            evidence_dir=args.evidence_dir,
            allow_init=args.allow_init,
        )
        _output_result(exit_code, decision, message, args.json_output)

    elif args.command == "nav-result":
        exit_code, decision, message = record_nav_result(
            nav_result=args.result,
            current_json_path=args.input,
            evidence_dir=args.evidence_dir,
        )
        _output_result(exit_code, decision, message, args.json_output)


if __name__ == "__main__":
    main()
