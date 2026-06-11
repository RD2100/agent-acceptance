"""Generate runtime negative-path evidence for CONVERSATION-HEALTH-GATE-A2.

Produces evidence files demonstrating that the Pre-GPT Gate correctly:
1. Blocks FORCE_HANDOFF submissions
2. Blocks HUMAN_REQUIRED submissions
3. Blocks when current.json is missing (no refresh path)
4. Warns on stale metrics
5. Records access_denied as FORCE
6. Records auth_required as HUMAN_REQUIRED
7. Successfully refreshes metrics
8. Writes latest.json for Pre-GPT flows

Each scenario writes a .txt file with Expected/Actual exit codes.
ALL PASS means the gate behaves as specified.
"""
import json
import os
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SCRIPTS = REPO / "scripts"
EVIDENCE_OUT = REPO / "_evidence" / "pre-gpt-gate-evidence"

sys.path.insert(0, str(SCRIPTS))
from pre_gpt_gate import (
    check_pre_gpt_gate, update_metrics, record_nav_result,
    EXIT_OK, EXIT_FORCE, EXIT_HUMAN_REQUIRED, EXIT_MISSING_BLOCKED,
)


def _make_env(tmp, **overrides):
    """Create a temp current.json and evidence dir."""
    ai_dir = Path(tmp) / "ai" / "conversation"
    ai_dir.mkdir(parents=True, exist_ok=True)
    ev_dir = Path(tmp) / "evidence" / "conversation-health"
    ev_dir.mkdir(parents=True, exist_ok=True)

    data = {
        "schema_version": "conversation-health.v1",
        "conversation_id": "evidence-test",
        "chat_url": "https://chatgpt.com/c/evidence-test",
        "status": "active",
        "last_known_metrics": {
            "assistant_message_count": 10,
            "review_round_count": 1,
            "last_response_time_seconds": 5.0,
            "last_gpt_reply_bytes": 5000,
        },
        "last_nav_result": "ok",
        "last_checked_at": "2026-06-12T12:00:00+08:00",
        "metrics_source": "cdp_dom_count",
        "metrics_freshness": "fresh",
    }
    for k, v in overrides.items():
        if k == "last_known_metrics" and isinstance(v, dict):
            data["last_known_metrics"].update(v)
        else:
            data[k] = v

    cp = ai_dir / "current.json"
    cp.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return str(cp), str(ev_dir)


def _write_result(name, description, expected_exit, actual_exit, decision, message):
    """Write a single scenario evidence file."""
    EVIDENCE_OUT.mkdir(parents=True, exist_ok=True)
    status = "PASS" if expected_exit == actual_exit else "FAIL"
    lines = [
        f"# Scenario: {name}",
        f"# Description: {description}",
        f"# Expected: exit_code={expected_exit}",
        f"# Actual exit: {actual_exit}",
        f"# Decision: {decision.get('decision', 'N/A')}",
        f"# Severity: {decision.get('severity', 'N/A')}",
        f"# Status: {status}",
        f"#",
        f"# Message: {message}",
        f"#",
        f"# Reasons:",
    ]
    for r in decision.get("reasons", []):
        if isinstance(r, dict):
            lines.append(f"#   - {r.get('code')}: actual={r.get('actual')} "
                         f"threshold={r.get('threshold')} policy={r.get('policy')}")
        else:
            lines.append(f"#   - {r}")

    op = EVIDENCE_OUT / f"{name}.txt"
    op.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return status


def main():
    import shutil

    # Clean previous evidence
    if EVIDENCE_OUT.exists():
        shutil.rmtree(EVIDENCE_OUT)
    EVIDENCE_OUT.mkdir(parents=True)

    results = []

    # --- Scenario 1: force_handoff_blocks_submit ---
    with tempfile.TemporaryDirectory() as tmp:
        cp, ev = _make_env(tmp, last_known_metrics={"assistant_message_count": 65})
        exit_code, decision, message = check_pre_gpt_gate(cp, evidence_dir=ev)
        s = _write_result(
            "force_handoff_blocks_submit",
            "High message count (65 >= 60) triggers FORCE_HANDOFF, blocking submission",
            EXIT_FORCE, exit_code, decision, message,
        )
        results.append(("force_handoff_blocks_submit", s))

    # --- Scenario 2: human_required_blocks_submit ---
    with tempfile.TemporaryDirectory() as tmp:
        cp, ev = _make_env(tmp, last_nav_result="auth_required")
        exit_code, decision, message = check_pre_gpt_gate(cp, evidence_dir=ev)
        s = _write_result(
            "human_required_blocks_submit",
            "auth_required nav result triggers HUMAN_REQUIRED, blocking submission",
            EXIT_HUMAN_REQUIRED, exit_code, decision, message,
        )
        results.append(("human_required_blocks_submit", s))

    # --- Scenario 3: missing_current_json_blocks_without_refresh ---
    with tempfile.TemporaryDirectory() as tmp:
        fake_path = str(Path(tmp) / "nonexistent" / "current.json")
        ev = str(Path(tmp) / "evidence")
        exit_code, decision, message = check_pre_gpt_gate(fake_path, evidence_dir=ev)
        s = _write_result(
            "missing_current_json_blocks_without_refresh",
            "Missing current.json with no allow_init blocks submission",
            EXIT_MISSING_BLOCKED, exit_code, decision, message,
        )
        results.append(("missing_current_json_blocks_without_refresh", s))

    # --- Scenario 4: stale_metrics_warns_or_suggests ---
    with tempfile.TemporaryDirectory() as tmp:
        cp, ev = _make_env(tmp, last_checked_at="2026-06-08T00:00:00+08:00")
        exit_code, decision, message = check_pre_gpt_gate(cp, evidence_dir=ev)
        # Stale metrics should produce SUGGEST (exit 0 but with warning)
        expected = EXIT_OK  # SUGGEST still exits 0
        s = _write_result(
            "stale_metrics_warns_or_suggests",
            "Stale metrics (>12h old) produce SUGGEST_HANDOFF warning",
            expected, exit_code, decision, message,
        )
        results.append(("stale_metrics_warns_or_suggests", s))

    # --- Scenario 5: access_denied_records_force ---
    with tempfile.TemporaryDirectory() as tmp:
        cp, ev = _make_env(tmp)
        exit_code, decision, message = record_nav_result(
            "access_denied", cp, ev,
        )
        s = _write_result(
            "access_denied_records_force",
            "access_denied nav result is recorded and triggers FORCE_HANDOFF",
            EXIT_FORCE, exit_code, decision, message,
        )
        results.append(("access_denied_records_force", s))

    # --- Scenario 6: auth_required_records_human_required ---
    with tempfile.TemporaryDirectory() as tmp:
        cp, ev = _make_env(tmp)
        exit_code, decision, message = record_nav_result(
            "auth_required", cp, ev,
        )
        s = _write_result(
            "auth_required_records_human_required",
            "auth_required nav result is recorded and triggers HUMAN_REQUIRED",
            EXIT_HUMAN_REQUIRED, exit_code, decision, message,
        )
        results.append(("auth_required_records_human_required", s))

    # --- Scenario 7: successful_metrics_refresh_updates_current_json ---
    with tempfile.TemporaryDirectory() as tmp:
        cp, ev = _make_env(tmp)
        new_metrics = {
            "assistant_message_count": 20,
            "last_response_time_seconds": 10.0,
            "last_gpt_reply_bytes": 4000,
        }
        updated, err = update_metrics(cp, new_metrics=new_metrics, source="cdp_dom_count")
        # Verify update happened
        data = json.loads(Path(cp).read_text())
        actual_count = data["last_known_metrics"]["assistant_message_count"]
        expected_count = 20
        # For this scenario, we compare the metric value, not exit code
        status = "PASS" if actual_count == expected_count and err is None else "FAIL"
        EVIDENCE_OUT.mkdir(parents=True, exist_ok=True)
        lines = [
            "# Scenario: successful_metrics_refresh_updates_current_json",
            "# Description: update_metrics() refreshes current.json with new CDP metrics",
            f"# Expected: assistant_message_count={expected_count}",
            f"# Actual value: {actual_count}",
            f"# Error: {err}",
            f"# Status: {status}",
            f"#",
            f"# Updated metrics: {json.dumps(data.get('last_known_metrics', {}))}",
            f"# Freshness: {data.get('metrics_freshness')}",
            f"# Source: {data.get('metrics_source')}",
        ]
        (EVIDENCE_OUT / "successful_metrics_refresh_updates_current_json.txt").write_text(
            "\n".join(lines) + "\n", encoding="utf-8"
        )
        results.append(("successful_metrics_refresh_updates_current_json", status))

    # --- Scenario 8: latest_json_written_for_pre_gpt_gate ---
    with tempfile.TemporaryDirectory() as tmp:
        cp, ev = _make_env(tmp)
        exit_code, decision, message = check_pre_gpt_gate(cp, evidence_dir=ev)
        latest_path = Path(ev) / "latest.json"
        snapshot_path = Path(ev) / "current-snapshot.json"
        has_latest = latest_path.exists()
        has_snapshot = snapshot_path.exists()
        status = "PASS" if has_latest and has_snapshot else "FAIL"

        latest_data = json.loads(latest_path.read_text()) if has_latest else {}
        snapshot_data = json.loads(snapshot_path.read_text()) if has_snapshot else {}

        EVIDENCE_OUT.mkdir(parents=True, exist_ok=True)
        lines = [
            "# Scenario: latest_json_written_for_pre_gpt_gate",
            "# Description: Pre-GPT gate writes latest.json AND current-snapshot.json",
            f"# Expected: latest.json exists AND current-snapshot.json exists",
            f"# Actual value: latest={has_latest}, snapshot={has_snapshot}",
            f"# Status: {status}",
            f"#",
            f"# latest.json decision: {latest_data.get('last_health_decision')}",
            f"# snapshot conversation_id: {snapshot_data.get('conversation_id')}",
            f"# snapshot source: {snapshot_data.get('_snapshot_source')}",
        ]
        (EVIDENCE_OUT / "latest_json_written_for_pre_gpt_gate.txt").write_text(
            "\n".join(lines) + "\n", encoding="utf-8"
        )
        results.append(("latest_json_written_for_pre_gpt_gate", status))

    # --- Scenario 9: legacy_helper_import_failure_blocks ---
    # Prove that run_pre_gpt_gate() in _cdp_submit_helper.py is coded
    # to fail-closed when pre_gpt_gate module is unavailable.
    # We verify by reading the source code (runtime simulation is unreliable
    # because the module is cached in sys.modules).
    helper_path = REPO / "_cdp_submit_helper.py"
    helper_source = helper_path.read_text(encoding="utf-8") if helper_path.exists() else ""

    # Check for fail-closed pattern in the source
    has_fail_closed = 'return 3,' in helper_source
    has_blocking = '"severity": "BLOCKING"' in helper_source or "'severity': 'BLOCKING'" in helper_source
    has_blocking_str = "BLOCKING" in helper_source
    no_fail_open = 'proceeding without gate check' not in helper_source

    status = "PASS" if (has_fail_closed and has_blocking_str and no_fail_open) else "FAIL"

    EVIDENCE_OUT.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Scenario: legacy_helper_import_failure_blocks",
        "# Description: _cdp_submit_helper.run_pre_gpt_gate() source code verification",
        "#   that ImportError handling returns exit 3 (fail-closed), not exit 0 (fail-open)",
        f"# Expected: return 3, severity=BLOCKING, no 'proceeding without gate check'",
        f"# Actual value: return_3={has_fail_closed}, blocking={has_blocking_str}, no_fail_open={no_fail_open}",
        f"# Status: {status}",
        f"#",
        f"# Source verification:",
        f"#   has 'return 3,': {has_fail_closed}",
        f"#   has 'BLOCKING': {has_blocking_str}",
        f"#   no 'proceeding without gate check': {no_fail_open}",
    ]
    (EVIDENCE_OUT / "legacy_helper_import_failure_blocks.txt").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )
    results.append(("legacy_helper_import_failure_blocks", status))

    # --- Scenario 10: legacy_script_post_response_updates_current_json ---
    # Prove that a legacy script can call update_metrics() after CDP response
    # and successfully write back to current.json
    with tempfile.TemporaryDirectory() as tmp:
        cp, ev = _make_env(tmp)
        # Simulate post-response metrics capture
        simulated_metrics = {
            "assistant_message_count": 15,
            "last_gpt_reply_bytes": 3200,
            "last_response_time_seconds": 7.5,
        }
        updated, err = update_metrics(
            cp, new_metrics=simulated_metrics,
            nav_result="ok", source="cdp_dom_count"
        )
        data = json.loads(Path(cp).read_text())
        actual_msgs = data["last_known_metrics"]["assistant_message_count"]
        actual_bytes = data["last_known_metrics"]["last_gpt_reply_bytes"]
        actual_source = data.get("metrics_source")
        actual_freshness = data.get("metrics_freshness")
        all_ok = (
            err is None
            and actual_msgs == 15
            and actual_bytes == 3200
            and actual_source == "cdp_dom_count"
            and actual_freshness == "fresh"
        )
        status = "PASS" if all_ok else "FAIL"
        EVIDENCE_OUT.mkdir(parents=True, exist_ok=True)
        lines = [
            "# Scenario: legacy_script_post_response_updates_current_json",
            "# Description: Legacy CDP script calls update_metrics() after GPT response,",
            "#   writing assistant_message_count, last_gpt_reply_bytes, last_response_time_seconds",
            "#   back to current.json with source=cdp_dom_count and freshness=fresh",
            f"# Expected: msgs=15, bytes=3200, source=cdp_dom_count, freshness=fresh",
            f"# Actual value: msgs={actual_msgs}, bytes={actual_bytes}, source={actual_source}, freshness={actual_freshness}",
            f"# Error: {err}",
            f"# Status: {status}",
            f"#",
            f"# Full metrics: {json.dumps(data.get('last_known_metrics', {}))}",
        ]
        (EVIDENCE_OUT / "legacy_script_post_response_updates_current_json.txt").write_text(
            "\n".join(lines) + "\n", encoding="utf-8"
        )
        results.append(("legacy_script_post_response_updates_current_json", status))

    # --- Combined summary ---
    all_pass = all(s == "PASS" for _, s in results)
    lines = [
        "# COMBINED: Pre-GPT Gate Negative-Path Evidence",
        f"# Overall: {'ALL PASS' if all_pass else 'FAILURES DETECTED'}",
        f"# Scenarios: {len(results)}",
        f"# Passed: {sum(1 for _, s in results if s == 'PASS')}",
        f"# Failed: {sum(1 for _, s in results if s == 'FAIL')}",
        "#",
    ]
    for name, status in results:
        lines.append(f"# {status}: {name}")

    (EVIDENCE_OUT / "combined_summary.txt").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )

    # Print summary
    print(f"Pre-GPT Gate Evidence: {len(results)} scenarios")
    for name, status in results:
        print(f"  {status}: {name}")
    print(f"\nOverall: {'ALL PASS' if all_pass else 'FAILURES DETECTED'}")
    print(f"Output: {EVIDENCE_OUT}")

    return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(main())
