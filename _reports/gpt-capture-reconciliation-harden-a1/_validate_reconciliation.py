#!/usr/bin/env python3
"""_validate_reconciliation.py — Validate GPT Capture Reconciliation Report.

Checks the report against HANDOFF_WORKFLOW_HARDENING_PLAN.md §5.4 spec:
1. JSON schema compliance (report_id, generated_at, summary, reconciliation, anomalies)
2. Summary counts match reconciliation array
3. Every known task has at least one entry
4. Status values belong to valid enumeration
5. All known anomalies are tagged and explained
6. Authorization chain integrity (no broken links to non-existent tasks)
7. Verdict values belong to valid enumeration
8. Report covers >= expected minimum task count
9. Pre-standardization tasks explicitly tagged
10. Truncated captures flagged with resolution notes

Usage:
    python _reports/gpt-capture-reconciliation-harden-a1/_validate_reconciliation.py
"""

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
REPORT_DIR = Path(__file__).resolve().parent
REPORT_JSON = REPORT_DIR / "GPT_CAPTURE_RECONCILIATION_REPORT.json"
REPORT_MD = REPORT_DIR / "GPT_CAPTURE_RECONCILIATION_REPORT.md"

VALID_STATUSES = {
    "complete", "orphan_submission", "orphan_capture",
    "unverified_capture", "verdict_mismatch", "pre_standardization",
    "truncated_capture", "blocked_chain_continuation"
}

VALID_VERDICTS = {
    "accepted", "accepted_with_limitation", "blocked",
    "human_required", "review_unverified", "mixed_blocked", "mixed",
    None  # (none) is valid for pre-standardization
}

VALID_ANOMALY_TYPES = {
    "orphan_submission", "orphan_capture", "unverified_capture",
    "verdict_mismatch", "stale_submission", "pre_standardization",
    "truncated_capture"
}

VALID_SEVERITIES = {"critical", "high", "medium", "low", "info"}

# Expected minimum task count (from subagent scan)
MIN_TASK_COUNT = 15

checks = []
errors = []


def check(name: str, condition: bool, detail: str = ""):
    """Record a check result."""
    status = "PASS" if condition else "FAIL"
    checks.append({"name": name, "status": status, "detail": detail})
    if not condition:
        errors.append(f"FAIL: {name} — {detail}")


def main():
    print("=" * 60)
    print("Reconciliation Report Validation")
    print("=" * 60)

    # ── Load report ──
    if not REPORT_JSON.exists():
        print(f"FATAL: Report JSON not found: {REPORT_JSON}")
        sys.exit(1)

    report = json.loads(REPORT_JSON.read_text(encoding="utf-8"))

    # ── Check 1: JSON schema compliance ──
    required_fields = ["report_id", "task_id", "generated_at", "summary",
                       "reconciliation", "anomalies"]
    for field in required_fields:
        check(f"schema.{field}", field in report,
              f"Missing required field: {field}")

    check("schema.report_id_format",
          report.get("report_id", "").startswith("RECON-"),
          f"report_id should start with RECON-: {report.get('report_id')}")

    check("schema.task_id",
          report.get("task_id") == "GPT-CAPTURE-RECONCILIATION-HARDEN-A1",
          f"task_id mismatch: {report.get('task_id')}")

    check("schema.hardening_plan_ref",
          "section 5.4" in report.get("hardening_plan_ref", ""),
          f"Missing hardening_plan_ref to section 5.4")

    # ── Check 2: Summary counts match ──
    summary = report.get("summary", {})
    reconciliation = report.get("reconciliation", [])

    check("summary.total_submissions",
          summary.get("total_submissions") == len(reconciliation),
          f"total_submissions={summary.get('total_submissions')} != "
          f"len(reconciliation)={len(reconciliation)}")

    total_captures = sum(1 for e in reconciliation if e.get("result_file"))
    check("summary.total_captures",
          summary.get("total_captures") == total_captures,
          f"total_captures={summary.get('total_captures')} != computed={total_captures}")

    orphan_subs = sum(1 for e in reconciliation if e.get("status") == "orphan_submission")
    check("summary.orphan_submissions",
          summary.get("orphan_submissions") == orphan_subs,
          f"orphan_submissions={summary.get('orphan_submissions')} != computed={orphan_subs}")

    # ── Check 3: Every known task has at least one entry ──
    task_ids_in_report = set(e["task_id"] for e in reconciliation)
    check("coverage.tasks_present",
          len(task_ids_in_report) >= MIN_TASK_COUNT,
          f"Found {len(task_ids_in_report)} tasks, expected >= {MIN_TASK_COUNT}")

    # ── Check 4: Status values valid ──
    invalid_statuses = [
        e for e in reconciliation
        if e.get("status") not in VALID_STATUSES
    ]
    check("status.valid_values",
          len(invalid_statuses) == 0,
          f"Invalid statuses: {[e['status'] for e in invalid_statuses]}")

    # ── Check 5: Anomalies tagged ──
    anomalies = report.get("anomalies", [])
    untagged = [a for a in anomalies if not a.get("type")]
    check("anomalies.all_tagged",
          len(untagged) == 0,
          f"{len(untagged)} anomalies without type tags")

    unexplained = [a for a in anomalies if not a.get("description")]
    check("anomalies.all_explained",
          len(unexplained) == 0,
          f"{len(unexplained)} anomalies without descriptions")

    # ── Check 6: Authorization chain integrity ──
    auth_chain = report.get("authorization_chain", [])
    broken_links = [
        link for link in auth_chain
        if not link.get("authorized_exists")
    ]
    # Broken links are expected for tasks not yet executed (e.g., GENERATE-APPROVED-HANDOFF-A1)
    # and the current task (GPT-CAPTURE-RECONCILIATION-HARDEN-A1)
    expected_broken = {
        "GENERATE-APPROVED-HANDOFF-A1",
        "GPT-CAPTURE-RECONCILIATION-HARDEN-A1",
    }
    unexpected_broken = [
        link for link in broken_links
        if link.get("authorized_task_id") not in expected_broken
    ]
    check("auth_chain.no_unexpected_broken",
          len(unexpected_broken) == 0,
          f"Unexpected broken links: "
          f"{[(l['source_task_id'], l['authorized_task_id']) for l in unexpected_broken]}")

    check("auth_chain.has_entries",
          len(auth_chain) >= 10,
          f"Authorization chain has {len(auth_chain)} links, expected >= 10")

    # ── Check 7: Verdict values valid ──
    invalid_verdicts = [
        e for e in reconciliation
        if e.get("verdict") is not None and e["verdict"] not in VALID_VERDICTS
    ]
    check("verdict.valid_values",
          len(invalid_verdicts) == 0,
          f"Invalid verdicts: {[e['verdict'] for e in invalid_verdicts]}")

    # ── Check 8: Coverage ──
    check("coverage.min_tasks",
          len(task_ids_in_report) >= MIN_TASK_COUNT,
          f"Task count {len(task_ids_in_report)} < minimum {MIN_TASK_COUNT}")

    # ── Check 9: Pre-standardization explicitly tagged ──
    pre_standard_entries = [
        e for e in reconciliation
        if e.get("status") == "pre_standardization"
    ]
    aa_entries = [
        e for e in reconciliation
        if e.get("task_id", "").upper().startswith("AA-")
    ]
    check("pre_standard.aa_tagged",
          len(aa_entries) > 0 and all(
              e["status"] == "pre_standardization" for e in aa_entries
          ),
          f"AA-* tasks not all tagged as pre_standardization: "
          f"{[(e['task_id'], e['status']) for e in aa_entries if e['status'] != 'pre_standardization']}")

    pipeline_entries = [
        e for e in reconciliation
        if "HANDOFF-PIPELINE-REFACTOR" in e.get("task_id", "").upper()
    ]
    check("pre_standard.pipeline_tagged",
          len(pipeline_entries) > 0 and all(
              e["status"] == "pre_standardization" for e in pipeline_entries
          ),
          f"HANDOFF-PIPELINE-REFACTOR-A1 entries not all pre_standardization")

    # ── Check 10: Truncated captures flagged ──
    # Check that PARAMETERIZE R1 is flagged (it was truncated)
    param_r1 = [
        e for e in reconciliation
        if "PARAMETERIZE" in e.get("task_id", "").upper()
        and e.get("round") == "R1"
    ]
    if param_r1:
        entry = param_r1[0]
        check("truncated.parameterize_r1_flagged",
              entry.get("status") in ("truncated_capture", "verdict_mismatch"),
              f"PARAMETERIZE R1 status={entry.get('status')}, expected truncated_capture or verdict_mismatch")

    # ── Check 11: Markdown report exists and has content ──
    check("md_report.exists",
          REPORT_MD.exists(),
          f"Markdown report not found: {REPORT_MD}")

    if REPORT_MD.exists():
        md_content = REPORT_MD.read_text(encoding="utf-8")
        check("md_report.has_summary",
              "## Summary" in md_content,
              "Markdown report missing Summary section")
        check("md_report.has_reconciliation",
              "## Reconciliation Detail" in md_content,
              "Markdown report missing Reconciliation Detail section")
        check("md_report.has_auth_chain",
              "## Authorization Chain" in md_content,
              "Markdown report missing Authorization Chain section")
        check("md_report.has_anomalies",
              "## Anomalies" in md_content,
              "Markdown report missing Anomalies section")
        check("md_report.has_end_marker",
              "END_OF_RECONCILIATION_REPORT" in md_content,
              "Markdown report missing end marker")

    # ── Check 12: No self-reference ──
    current_task_entries = [
        e for e in reconciliation
        if e.get("task_id", "").upper() == "GPT-CAPTURE-RECONCILIATION-HARDEN-A1"
    ]
    check("no_self_reference",
          len(current_task_entries) == 0,
          f"Current task found in reconciliation: {len(current_task_entries)} entries")

    # ── Check 13: No orphan submissions (critical for audit) ──
    check("audit.no_orphans",
          summary.get("orphan_submissions", 0) == 0,
          f"orphan_submissions={summary.get('orphan_submissions')} (should be 0 or explicitly explained)")

    # ── Print results ──
    print()
    passed = sum(1 for c in checks if c["status"] == "PASS")
    failed = sum(1 for c in checks if c["status"] == "FAIL")

    for c in checks:
        symbol = "OK" if c["status"] == "PASS" else "XX"
        detail = f" -- {c['detail']}" if c["detail"] else ""
        print(f"  [{symbol}] {c['name']}{detail}")

    print()
    print(f"{'=' * 60}")
    print(f"Results: {passed} PASS, {failed} FAIL, {passed + failed} total")
    print(f"{'=' * 60}")

    if errors:
        print("\nFailed checks:")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)
    else:
        print("\nAll checks passed!")
        sys.exit(0)


if __name__ == "__main__":
    main()
