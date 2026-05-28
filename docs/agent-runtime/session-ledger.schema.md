# Session Ledger Schema

> Plan Auditor input artifact. Generated after every session that produces file changes.
> This ledger is the primary evidence source for audit — Plan Agent must update it, Auditor verifies it.

## Schema

```yaml
session_ledger:
  session_id: "unique-session-identifier"
  objective: "1-sentence goal summary"
  started_at: "ISO-8601"
  completed_at: "ISO-8601"

  changed_files:
    - path: "relative/path/to/file"
      change_type: modified | new | deleted
      governance_file: true | false
      protected_file: true | false

  protected_files_touched: true | false
  protected_files_list: ["AGENTS.md", "rules/core.md"]

  taskspecs_created:
    - task_id: "task-xxx-001"
      has_gate_0: true | false
      has_inventory_evidence: true | false
      gate_0_valid: true | false

  execution_reports_created:
    - report_id: "rep-xxx-001"
      status: PASS | FAIL | BLOCKED
      trust_record_present: true | false

  cumulative_write_set: 8
  cumulative_new_artifacts: 2
  cumulative_protected_touches: 2
  cumulative_task_count: 1

  sadp_required: true | false
  sadp_trigger_reason:
    - "3+ files modified"
    - "governance files touched"

  audit_required: true | false
  audit_status: pending | passed | blocked | escalated

  plan_agent_signoff: "Agent ID or name"
  plan_agent_cannot_self_audit: true
```

## Required Fields

| Field | Required When | Purpose |
|-------|--------------|---------|
| session_id | Always | Unique session identifier |
| changed_files | Session has git diff | Full list of files modified/created/deleted |
| protected_files_touched | Always | Whether any protected file was accessed |
| taskspecs_created | SADP triggered | List of TaskSpecs with gate_0 validity |
| execution_reports_created | Execution occurred | List of ExecutionReports with Trust Record |
| cumulative_write_set | Multiple tasks | Anti-gaming: total files written this objective |
| sadp_required | Always | Whether SADP auto-trigger conditions were met |
| audit_required | Always | Whether independent audit is required |
| audit_status | Always | Current audit state |

## Anti-Bypass Rules

1. Plan Agent MUST update this ledger before session finalization.
2. Plan Agent CANNOT set audit_status to `passed` — only Plan Auditor can.
3. If changed_files is non-empty and taskspecs_created is empty when sadp_required is true → automatic audit block.
4. If cumulative_write_set >= 3 and taskspecs_created count < 1 → automatic audit block.
