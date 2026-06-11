"""Check if conversation handoff is needed based on thresholds.

CONVERSATION-HEALTH-GATE-A1 -- v2 upgrade with full CLI interface.

Backward-compatible with v1:
    Old CLI:  check_handoff_needed.py messages=42 response_time=30 rounds=2 reply_bytes=5000
    Old API:  check_handoff(assistant_message_count, response_time_seconds,
                           review_round_count, last_gpt_reply_bytes) -> dict

New CLI (v2):
    check_handoff_needed.py --input .ai/conversation/current.json \\
        --write _evidence/conversation-health/latest.json \\
        --fail-on-force --mode pre-task --max-staleness-hours 12 \\
        --composite --json --policy configs/conversation-health-policy.yaml

Decision schema (v2):
    {
        "schema_version": "conversation-health-decision.v1",
        "decision": "OK|FORCE_HANDOFF|SUGGEST_HANDOFF|UNKNOWN|HUMAN_REQUIRED",
        "severity": "INFO|WARNING|BLOCKING",
        "reasons": [
            {"code": "review_round_count_exceeded", "actual": 3,
             "threshold": 3, "policy": "force"}
        ],
        "recommended_action": "continue|suggest_handoff|generate_handoff|human_review",
        "checked_at": "ISO-8601",
        "source": "path or cli_args"
    }

Exit codes:
    0 - OK, SUGGEST, or FORCE without --fail-on-force
    1 - FORCE_HANDOFF when --fail-on-force is set
    2 - Invalid input / schema error
    3 - Missing required metrics in strict mode (pre-gpt with no current.json)

Thresholds (defaults, overridable via policy YAML):
    - assistant_message_count >= 60: force handoff
    - review_round_count >= 3: force handoff
    - response_time_seconds >= 60: suggest handoff (alone)
    - last_gpt_reply_bytes < 2000: suggest handoff (alone)
    - composite (slow + short + rounds): force handoff
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path


# ---------------------------------------------------------------------------
# Default policy (hardcoded, used when no YAML policy file is found)
# ---------------------------------------------------------------------------

DEFAULT_POLICY = {
    "thresholds": {
        "force": {
            "assistant_message_count": 60,
            "review_round_count": 3,
        },
        "suggest": {
            "assistant_message_count": 45,
            "response_time_seconds": 60,
            "last_gpt_reply_bytes_low": 2000,
        },
    },
    "composite": {
        "response_time_seconds": 60,
        "last_gpt_reply_bytes_high": 2000,
        "review_round_count": 2,
    },
    "staleness_hours": 12,
    "nav_result_map": {
        "access_denied": "FORCE_HANDOFF",
        "not_found": "FORCE_HANDOFF",
        "auth_required": "HUMAN_REQUIRED",
    },
}


# ---------------------------------------------------------------------------
# Minimal YAML parser (stdlib only -- no PyYAML dependency)
# ---------------------------------------------------------------------------

def _parse_simple_yaml(text):
    """Parse a simple YAML-like structure into nested dicts.

    Supports:
        - Top-level and nested key: value pairs (indentation-based nesting)
        - Integer, float, string, and boolean values
        - Comments (lines starting with #)
        - Blank lines

    Does NOT support:
        - Lists (not needed for policy files)
        - Multi-line values
        - Anchors / aliases
        - Quoted strings (quotes are stripped)

    Returns a nested dict.
    """
    result = {}
    stack = [(result, -1)]  # (current_dict, indent_level)

    for raw_line in text.splitlines():
        # Strip comments and blank lines
        line = raw_line.split("#")[0].rstrip()
        if not line.strip():
            continue

        # Measure indentation
        stripped = line.lstrip()
        indent = len(line) - len(stripped)

        if ":" not in stripped:
            continue

        key, _, val = stripped.partition(":")
        key = key.strip()
        val = val.strip()

        # Pop stack to find parent at correct indent level
        while len(stack) > 1 and stack[-1][1] >= indent:
            stack.pop()

        parent = stack[-1][0]

        if val == "" or val is None:
            # This key introduces a nested dict
            new_dict = {}
            parent[key] = new_dict
            stack.append((new_dict, indent))
        else:
            # Parse the scalar value
            parent[key] = _yaml_scalar(val)

    return result


def _yaml_scalar(val):
    """Convert a YAML scalar string to a Python value."""
    # Strip surrounding quotes
    if (val.startswith('"') and val.endswith('"')) or \
       (val.startswith("'") and val.endswith("'")):
        return val[1:-1]

    lower = val.lower()
    if lower in ("true", "yes", "on"):
        return True
    if lower in ("false", "no", "off"):
        return False
    if lower in ("null", "~", ""):
        return None

    # Try int, then float
    try:
        return int(val)
    except ValueError:
        pass
    try:
        return float(val)
    except ValueError:
        pass

    return val


def load_policy(policy_path):
    """Load policy from a YAML file, falling back to DEFAULT_POLICY.

    Merges loaded values on top of defaults so missing keys don't crash.
    Returns a policy dict with the same structure as DEFAULT_POLICY.
    """
    path = Path(policy_path)
    if not path.is_file():
        return _deep_copy_dict(DEFAULT_POLICY)

    try:
        text = path.read_text(encoding="utf-8")
        loaded = _parse_simple_yaml(text)
    except Exception:
        return _deep_copy_dict(DEFAULT_POLICY)

    # Merge loaded on top of defaults
    merged = _deep_copy_dict(DEFAULT_POLICY)
    _deep_merge(merged, loaded)
    return merged


def _deep_copy_dict(d):
    """Simple deep copy for dicts containing only primitive types."""
    out = {}
    for k, v in d.items():
        if isinstance(v, dict):
            out[k] = _deep_copy_dict(v)
        else:
            out[k] = v
    return out


def _deep_merge(base, override):
    """Recursively merge *override* into *base* in place."""
    for k, v in override.items():
        if isinstance(v, dict) and isinstance(base.get(k), dict):
            _deep_merge(base[k], v)
        else:
            base[k] = v


# ---------------------------------------------------------------------------
# v1 backward-compatible function
# ---------------------------------------------------------------------------

def check_handoff(
    assistant_message_count: int = 0,
    response_time_seconds: int = 0,
    review_round_count: int = 0,
    last_gpt_reply_bytes: int = 0,
) -> dict:
    """Original v1 check -- kept for backward compatibility.

    Returns a dict with keys:
        handoff_needed (bool), force_handoff (bool), suggested_only (bool),
        reasons (list[str]), recommended_action (str)
    """
    force_reasons = []
    suggest_reasons = []

    if assistant_message_count >= 60:
        force_reasons.append(f"assistant_message_count={assistant_message_count} >= 60")
    elif assistant_message_count >= 45:
        suggest_reasons.append(f"assistant_message_count={assistant_message_count} >= 45 (suggested)")
    if response_time_seconds >= 60:
        suggest_reasons.append(f"response_time_seconds={response_time_seconds}s >= 60 (suggested)")
    if review_round_count >= 3:
        force_reasons.append(f"review_round_count={review_round_count} >= 3")
    if 0 < last_gpt_reply_bytes < 2000:
        suggest_reasons.append(f"last_gpt_reply_bytes={last_gpt_reply_bytes} < 2000 (suggested)")

    all_reasons = force_reasons + suggest_reasons
    return {
        "handoff_needed": len(force_reasons) > 0,
        "force_handoff": len(force_reasons) > 0,
        "suggested_only": len(all_reasons) > 0 and len(force_reasons) == 0,
        "reasons": all_reasons,
        "recommended_action": "generate_handoff" if len(force_reasons) > 0 else ("suggest_handoff" if suggest_reasons else "continue"),
    }


# ---------------------------------------------------------------------------
# v2 decision engine
# ---------------------------------------------------------------------------

def _now_iso():
    """Return current UTC time as ISO-8601 string."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _build_decision(decision, severity, reasons, recommended_action, source):
    """Build a v2 decision JSON object."""
    return {
        "schema_version": "conversation-health-decision.v1",
        "decision": decision,
        "severity": severity,
        "reasons": reasons,
        "recommended_action": recommended_action,
        "checked_at": _now_iso(),
        "source": source,
    }


def _reason(code, actual, threshold, policy_level):
    """Build a single reason entry."""
    return {
        "code": code,
        "actual": actual,
        "threshold": threshold,
        "policy": policy_level,
    }


def check_handoff_v2(metrics, policy=None, *, mode=None, max_staleness_hours=None,
                     composite=False, source_label="cli_args"):
    """Run the full v2 conversation-health check.

    Parameters
    ----------
    metrics : dict
        Must contain some of: assistant_message_count, response_time_seconds,
        review_round_count, last_gpt_reply_bytes.
        Optional: metrics_source, last_checked_at, nav_result.
    policy : dict or None
        Policy dict (see DEFAULT_POLICY).  If None, defaults are used.
    mode : str or None
        One of: pre-task, pre-gpt, evidence-pack, advisory.
    max_staleness_hours : int or None
        Override policy staleness threshold.
    composite : bool
        Enable composite force checks.
    source_label : str
        Label for the ``source`` field in the decision.

    Returns
    -------
    dict  -- v2 decision object.
    """
    if policy is None:
        policy = _deep_copy_dict(DEFAULT_POLICY)

    thresholds = policy.get("thresholds", DEFAULT_POLICY["thresholds"])
    force_th = thresholds.get("force", DEFAULT_POLICY["thresholds"]["force"])
    suggest_th = thresholds.get("suggest", DEFAULT_POLICY["thresholds"]["suggest"])

    if max_staleness_hours is None:
        max_staleness_hours = policy.get("staleness_hours",
                                         DEFAULT_POLICY["staleness_hours"])

    metrics_source = metrics.get("metrics_source", "none")
    nav_result = metrics.get("nav_result", None)

    # Determine if this source can trigger FORCE
    can_force = metrics_source in ("cdp_dom_count", "wrapper_counter")
    # manual_estimate caps severity at SUGGEST (unless nav_result overrides)
    cap_at_suggest = (metrics_source == "manual_estimate")
    # none source -> UNKNOWN
    is_unknown_source = (metrics_source == "none")

    force_reasons = []
    suggest_reasons = []
    human_reasons = []

    # --- nav_result checks (always evaluated, can override source caps) ---
    nav_map = policy.get("nav_result_map", DEFAULT_POLICY["nav_result_map"])
    if nav_result and nav_result in nav_map:
        nav_decision = nav_map[nav_result]
        if nav_decision == "HUMAN_REQUIRED":
            human_reasons.append(_reason(
                "nav_result_" + nav_result, nav_result, "auth_required", "human"))
        else:
            # FORCE from nav_result bypasses source cap
            force_reasons.append(_reason(
                "nav_result_" + nav_result, nav_result, "access_denied_or_not_found", "force"))

    # --- If source is "none" and no nav_result triggered, return UNKNOWN ---
    if is_unknown_source and not force_reasons and not human_reasons:
        return _build_decision(
            "UNKNOWN", "WARNING",
            [_reason("no_metrics_source", "none", "cdp_dom_count|wrapper_counter", "info")],
            "suggest_handoff",
            source_label,
        )

    # --- Standard threshold checks ---
    msg_count = metrics.get("assistant_message_count", 0)
    resp_time = metrics.get("response_time_seconds", 0)
    rounds = metrics.get("review_round_count", 0)
    reply_bytes = metrics.get("last_gpt_reply_bytes", 0)

    # Message count
    force_msg = force_th.get("assistant_message_count", 60)
    suggest_msg = suggest_th.get("assistant_message_count", 45)
    if msg_count >= force_msg:
        force_reasons.append(_reason(
            "assistant_message_count_exceeded", msg_count, force_msg, "force"))
    elif msg_count >= suggest_msg:
        suggest_reasons.append(_reason(
            "assistant_message_count_elevated", msg_count, suggest_msg, "suggest"))

    # Response time — single metric only triggers SUGGEST (consensus: R1 review)
    suggest_rt = suggest_th.get("response_time_seconds", 60)
    if resp_time >= suggest_rt:
        suggest_reasons.append(_reason(
            "response_time_elevated", resp_time, suggest_rt, "suggest"))

    # Review rounds
    force_rr = force_th.get("review_round_count", 3)
    if rounds >= force_rr:
        force_reasons.append(_reason(
            "review_round_count_exceeded", rounds, force_rr, "force"))

    # Reply bytes — single metric only triggers SUGGEST (consensus: R1 review)
    suggest_bytes_low = suggest_th.get("last_gpt_reply_bytes_low", 2000)
    if 0 < reply_bytes < suggest_bytes_low:
        suggest_reasons.append(_reason(
            "last_gpt_reply_bytes_low", reply_bytes, suggest_bytes_low, "suggest"))

    # --- Composite force check ---
    if composite:
        comp_th = policy.get("composite", DEFAULT_POLICY["composite"])
        comp_rt = comp_th.get("response_time_seconds", 60)
        comp_bytes = comp_th.get("last_gpt_reply_bytes_high", 2000)
        comp_rr = comp_th.get("review_round_count", 2)

        all_composite_met = (
            resp_time >= comp_rt
            and 0 < reply_bytes < comp_bytes
            and rounds >= comp_rr
            and metrics_source != "manual_estimate"
        )
        if all_composite_met:
            force_reasons.append(_reason(
                "composite_degradation",
                f"rt={resp_time},bytes={reply_bytes},rounds={rounds}",
                f"rt>={comp_rt}&bytes<{comp_bytes}&rounds>={comp_rr}",
                "force_composite",
            ))

    # --- Staleness check ---
    last_checked = metrics.get("last_checked_at")
    if last_checked:
        try:
            if isinstance(last_checked, str):
                # Support both with and without timezone info
                ts = last_checked.replace("Z", "+00:00")
                checked_dt = datetime.fromisoformat(ts)
                if checked_dt.tzinfo is None:
                    checked_dt = checked_dt.replace(tzinfo=timezone.utc)
            else:
                checked_dt = None

            if checked_dt is not None:
                now = datetime.now(timezone.utc)
                age_hours = (now - checked_dt).total_seconds() / 3600
                if age_hours > max_staleness_hours:
                    suggest_reasons.append(_reason(
                        "metrics_stale",
                        round(age_hours, 1),
                        max_staleness_hours,
                        "suggest",
                    ))
        except (ValueError, TypeError):
            suggest_reasons.append(_reason(
                "metrics_staleness_unparseable", last_checked, "iso-8601", "suggest"))

    # --- Apply source cap: manual_estimate cannot FORCE (unless nav_result) ---
    if cap_at_suggest and force_reasons:
        # Move non-nav force reasons to suggest
        nav_forces = [r for r in force_reasons if r["code"].startswith("nav_result_")]
        non_nav_forces = [r for r in force_reasons if not r["code"].startswith("nav_result_")]
        for r in non_nav_forces:
            r["policy"] = "suggest_capped"
            suggest_reasons.append(r)
        force_reasons = nav_forces

    # --- Human required takes priority ---
    if human_reasons:
        return _build_decision(
            "HUMAN_REQUIRED", "BLOCKING", human_reasons, "human_review", source_label)

    # --- Determine decision ---
    if force_reasons:
        all_reasons = force_reasons + suggest_reasons
        return _build_decision(
            "FORCE_HANDOFF", "BLOCKING", all_reasons, "generate_handoff", source_label)

    if suggest_reasons:
        return _build_decision(
            "SUGGEST_HANDOFF", "WARNING", suggest_reasons, "suggest_handoff", source_label)

    return _build_decision("OK", "INFO", [], "continue", source_label)


# ---------------------------------------------------------------------------
# Metrics file loading
# ---------------------------------------------------------------------------

def load_metrics(input_path):
    """Load metrics from a JSON file.

    Returns (metrics_dict, error_string_or_None).
    """
    path = Path(input_path)
    if not path.is_file():
        return None, f"Metrics file not found: {input_path}"
    try:
        text = path.read_text(encoding="utf-8")
        data = json.loads(text)
        if not isinstance(data, dict):
            return None, f"Metrics file must contain a JSON object, got {type(data).__name__}"
        return data, None
    except json.JSONDecodeError as exc:
        return None, f"Invalid JSON in metrics file: {exc}"


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _is_legacy_cli(argv):
    """Detect if the user is using the old key=value CLI style.

    Returns True if ALL non-empty args contain '=' and look like key=int.
    """
    if not argv:
        return False
    for arg in argv:
        if not arg:
            continue
        if arg.startswith("-"):
            return False
        if "=" not in arg:
            return False
        _, _, v = arg.partition("=")
        try:
            int(v)
        except ValueError:
            return False
    return True


def _run_legacy(argv):
    """Run the old v1 CLI interface (key=value args)."""
    stats = {}
    for arg in argv:
        if "=" in arg:
            k, v = arg.split("=", 1)
            stats[k] = int(v)

    result = check_handoff(
        assistant_message_count=stats.get("messages", 0),
        response_time_seconds=stats.get("response_time", 0),
        review_round_count=stats.get("rounds", 0),
        last_gpt_reply_bytes=stats.get("reply_bytes", 0),
    )

    print("HANDOFF_NEEDED:")
    print(f"  handoff_needed: {result['handoff_needed']}")
    print(f"  force_handoff: {result['force_handoff']}")
    print("  reasons:")
    for r in result["reasons"]:
        print(f"    - {r}")
    if not result["reasons"]:
        print("    []")
    print(f"  recommended_action: {result['recommended_action']}")

    return 0 if not result["force_handoff"] else 1


def _build_parser():
    """Build the argparse parser for the v2 CLI."""
    parser = argparse.ArgumentParser(
        prog="check_handoff_needed",
        description="CONVERSATION-HEALTH-GATE-A1: Check if conversation handoff is needed.",
    )
    parser.add_argument(
        "--input", dest="input_path", default=None,
        help="Read metrics from a JSON file (e.g. .ai/conversation/current.json)")
    parser.add_argument(
        "--write", dest="write_path", default=None,
        help="Write decision JSON to file (e.g. _evidence/conversation-health/latest.json)")
    parser.add_argument(
        "--fail-on-force", dest="fail_on_force", action="store_true", default=False,
        help="Exit code 1 on FORCE_HANDOFF (default: exit 0 always)")
    parser.add_argument(
        "--mode", dest="mode", default=None,
        choices=["pre-task", "pre-gpt", "evidence-pack", "advisory"],
        help="Gate mode: pre-task, pre-gpt, evidence-pack, advisory")
    parser.add_argument(
        "--max-staleness-hours", dest="max_staleness_hours", type=int, default=None,
        help="Metrics older than N hours trigger SUGGEST_HANDOFF (default: 12)")
    parser.add_argument(
        "--composite", dest="composite", action="store_true", default=False,
        help="Enable composite force checks")
    parser.add_argument(
        "--json", dest="json_output", action="store_true", default=False,
        help="Output decision as JSON to stdout")
    parser.add_argument(
        "--policy", dest="policy_path", default="configs/conversation-health-policy.yaml",
        help="Path to policy YAML (default: configs/conversation-health-policy.yaml)")

    # Allow inline metrics as fallback (for piping/testing without --input)
    parser.add_argument(
        "inline_metrics", nargs="*", default=[],
        help="Inline metrics as key=value pairs (fallback when --input is not used)")

    return parser


def main():
    """Entry point -- dispatches to v1 legacy or v2 CLI."""
    argv = sys.argv[1:]

    # Detect old-style CLI
    if _is_legacy_cli(argv):
        return _run_legacy(argv)

    # Also handle the case where no args at all -> run legacy with empty stats
    if not argv:
        return _run_legacy(argv)

    # v2 CLI
    parser = _build_parser()
    args = parser.parse_args(argv)

    # Load policy
    policy = load_policy(args.policy_path)

    # Determine metrics source
    metrics = {}
    source_label = "cli_args"
    input_path = args.input_path

    if input_path:
        source_label = str(input_path)
        loaded, err = load_metrics(input_path)

        if err:
            # Distinguish "file not found" (lenient) from "invalid JSON" (hard error)
            is_invalid_json = "Invalid JSON" in err

            # Invalid JSON is always a hard error (exit 2), regardless of mode
            if is_invalid_json:
                print(f"ERROR: {err}", file=sys.stderr)
                return 2

            # Mode-specific behavior for missing files
            if args.mode == "pre-gpt":
                # Strict mode: missing file is BLOCKED
                decision = _build_decision(
                    "UNKNOWN", "BLOCKING",
                    [_reason("metrics_file_missing", input_path, "exists", "blocking")],
                    "generate_handoff", source_label)
                if args.json_output:
                    print(json.dumps(decision, indent=2))
                else:
                    print(f"BLOCKED: {err}", file=sys.stderr)
                if args.write_path:
                    _write_decision(args.write_path, decision)
                return 3

            elif args.mode in ("pre-task", "evidence-pack"):
                # Lenient mode: missing -> UNKNOWN, not blocked
                decision = _build_decision(
                    "UNKNOWN", "WARNING",
                    [_reason("metrics_file_missing", input_path, "exists", "warning")],
                    "suggest_handoff", source_label)
                if args.json_output:
                    print(json.dumps(decision, indent=2))
                else:
                    print(f"WARNING: {err}", file=sys.stderr)
                if args.write_path:
                    _write_decision(args.write_path, decision)
                return 0

            elif args.mode == "advisory":
                # Advisory never blocks
                decision = _build_decision(
                    "UNKNOWN", "WARNING",
                    [_reason("metrics_file_missing", input_path, "exists", "advisory")],
                    "suggest_handoff", source_label)
                if args.json_output:
                    print(json.dumps(decision, indent=2))
                else:
                    print(f"ADVISORY: {err}", file=sys.stderr)
                if args.write_path:
                    _write_decision(args.write_path, decision)
                return 0

            else:
                # No mode specified -- treat as error
                print(f"ERROR: {err}", file=sys.stderr)
                return 2

        # Flatten current.json structure: extract last_known_metrics to top level
        lkm = loaded.get("last_known_metrics", {})
        if isinstance(lkm, dict):
            metrics = dict(lkm)  # start with nested metrics
        else:
            metrics = {}
        # Top-level fields from current.json override / supplement
        for key in ("metrics_source", "last_checked_at"):
            if key in loaded:
                metrics[key] = loaded[key]
        # nav_result can be last_nav_result in current.json
        if "last_nav_result" in loaded and "nav_result" not in metrics:
            metrics["nav_result"] = loaded["last_nav_result"]
        if "nav_result" in loaded:
            metrics["nav_result"] = loaded["nav_result"]

    elif args.inline_metrics:
        # Parse inline key=value pairs (v2 style, not pure legacy)
        for item in args.inline_metrics:
            if "=" in item:
                k, _, v = item.partition("=")
                try:
                    metrics[k.strip()] = int(v.strip())
                except ValueError:
                    metrics[k.strip()] = v.strip()
        # If no metrics_source was provided inline, default to wrapper_counter
        if "metrics_source" not in metrics:
            metrics["metrics_source"] = "wrapper_counter"
    else:
        # No input file, no inline metrics
        if args.mode == "pre-gpt":
            decision = _build_decision(
                "UNKNOWN", "BLOCKING",
                [_reason("no_metrics_provided", "none", "metrics_required", "blocking")],
                "generate_handoff", "none")
            if args.json_output:
                print(json.dumps(decision, indent=2))
            if args.write_path:
                _write_decision(args.write_path, decision)
            return 3
        elif args.mode == "advisory":
            decision = _build_decision(
                "UNKNOWN", "INFO",
                [_reason("no_metrics_provided", "none", "metrics_optional", "advisory")],
                "suggest_handoff", "none")
            if args.json_output:
                print(json.dumps(decision, indent=2))
            if args.write_path:
                _write_decision(args.write_path, decision)
            return 0
        else:
            # Default: no metrics -> UNKNOWN
            metrics = {"metrics_source": "none"}

    # --- evidence-pack mode: also check if decision file already exists ---
    if args.mode == "evidence-pack" and args.write_path:
        write_p = Path(args.write_path)
        if write_p.is_file():
            try:
                existing = json.loads(write_p.read_text(encoding="utf-8"))
                if existing.get("schema_version") == "conversation-health-decision.v1":
                    # Decision already exists -- still run check but note it
                    pass
            except (json.JSONDecodeError, OSError):
                pass

    # --- Run the v2 check ---
    decision = check_handoff_v2(
        metrics,
        policy=policy,
        mode=args.mode,
        max_staleness_hours=args.max_staleness_hours,
        composite=args.composite,
        source_label=source_label,
    )

    # --- Advisory mode: never block, always exit 0 ---
    if args.mode == "advisory":
        decision["severity"] = "INFO" if decision["severity"] != "BLOCKING" else "INFO"

    # --- Output ---
    if args.json_output:
        print(json.dumps(decision, indent=2))
    else:
        _print_decision_human(decision)

    # --- Write decision file ---
    if args.write_path:
        _write_decision(args.write_path, decision)

    # --- Exit code ---
    if args.mode == "advisory":
        return 0

    if args.fail_on_force and decision["decision"] in ("FORCE_HANDOFF", "HUMAN_REQUIRED"):
        return 1

    return 0


def _print_decision_human(decision):
    """Pretty-print a decision dict for human-readable console output."""
    d = decision["decision"]
    sev = decision["severity"]
    action = decision["recommended_action"]
    print(f"Decision:  {d}  [{sev}]")
    print(f"Action:    {action}")
    print(f"Checked:   {decision['checked_at']}")
    print(f"Source:    {decision['source']}")
    if decision["reasons"]:
        print("Reasons:")
        for r in decision["reasons"]:
            print(f"  - [{r['policy']}] {r['code']}: actual={r['actual']}, threshold={r['threshold']}")
    else:
        print("Reasons:   (none)")


def _write_decision(write_path, decision):
    """Write a decision dict as JSON to the given path, creating dirs as needed."""
    p = Path(write_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(decision, indent=2) + "\n", encoding="utf-8")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    sys.exit(main())
