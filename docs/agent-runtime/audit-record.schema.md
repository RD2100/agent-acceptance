# Audit Record Schema

> Plan Auditor output artifact. Generated after every session that triggers audit.
> This record is the independent verification that SADP compliance was checked.

## Schema

```yaml
audit_record:
  audit_id: "audit-{session_id}"
  session_id: "referenced session"
  audited_at: "ISO-8601"
  auditor: "Plan Auditor (independent from Plan Agent)"

  input_artifacts:
    session_ledger: "path or inline"
    changed_files_list: "path or inline"
    taskspecs: ["task-xxx-001"]
    execution_reports: ["rep-xxx-001"]
    git_diff_summary: "summary of actual changes"

  findings:
    sadp_trigger_met: true | false
    taskspec_exists_when_required: true | false
    gate_0_has_evidence: true | false
    execution_report_exists_when_required: true | false
    execution_report_covers_diff: true | false
    read_set_write_set_match_diff: true | false
    protected_files_reported: true | false
    cumulative_trigger_bypass_detected: true | false
    task_splitting_detected: true | false

  issues:
    - type: "missing_taskspec | missing_execution_report | diff_report_mismatch | protected_file_unreported | cumulative_trigger_missed | gate_0_no_evidence | unauthorized_bypass"
      severity: "block | warn"
      description: "what was found"
      affected_artifacts: ["file paths or task IDs"]

  decision: pass | block | escalate

  rationale: |
    1-3 sentences explaining the decision. For block: which finding caused it and what is required to unblock.
    For escalate: why Plan Auditor cannot determine compliance and what Human Reviewer should check.

  remediation:
    if_blocked:
      - "Create missing TaskSpec"
      - "Add gate_0 evidence"
      - "Update ExecutionReport to cover all changed files"
    if_escalated:
      - "Human Reviewer must verify [specific items]"

  plan_agent_cannot_override: true
```

## Decision Rules

| Condition | Decision |
|-----------|----------|
| All findings pass, no issues | pass |
| Missing TaskSpec when SADP required | block |
| Gate 0 without inventory_evidence | block |
| ExecutionReport missing after execution | block |
| Changed files not covered by any ExecutionReport | block |
| Protected files touched but not reported | block |
| Cumulative trigger bypass detected | block |
| Auditor uncertain, governance files touched | escalate |
| Auditor uncertain, low-risk non-governance | pass (with warn) |

## Anti-Recursion

1. Audit Record is the final artifact — no Audit-Auditor.
2. Plan Auditor only checks structured evidence consistency.
3. If Plan Auditor cannot determine pass/block → escalate to Human, not to another auditor.
4. Plan Agent CANNOT modify or override audit_record.decision.
