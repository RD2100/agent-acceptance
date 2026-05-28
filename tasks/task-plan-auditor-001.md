# TaskSpec: Plan Auditor Implementation

- **ID**: task-plan-auditor-001
- **Batch**: batch-plan-auditor
- **Risk**: medium
- **Priority**: P0
- **Goal**: Create a lightweight Plan Auditor that independently verifies SADP compliance per session — checking whether git diff, TaskSpecs, ExecutionReports, Gate 0 evidence, and protected file access are consistent. Plan Agent must not audit its own compliance.
- **Context**: LL-009 exposed that Plan Agent can silently bypass SADP (no TaskSpec, no ExecutionReport). Existing mechanisms (Veto Contract, Human Reviewer) cannot catch this because they require a TaskSpec to exist. A structured, evidence-only auditor is the minimal fix.
- **Allowed Files**:
  - docs/agent-runtime/session-ledger.schema.md (new)
  - docs/agent-runtime/audit-record.schema.md (new)
  - docs/agent-runtime/sub-agent-dispatch-protocol.md (amend §3.3a → §3.3b Plan Auditor)
- **Forbidden**:
  - Do not change core rules
  - Do not change veto contract
  - Do not change Gate 0 format
  - Do not touch non-governance files

- **Gate 0 Ledger**:
  ```yaml
  gate_0:
    triggered: true
    trigger_reason: "New agent role (Plan Auditor) + governance mechanism addition"

    inventory_evidence:
      queried_sources:
        - capability-inventory.md
        - sub-agent-dispatch-protocol.md
        - lessons-learned.md
      matched_capabilities:
        - SADP §3.3a (Plan Agent Review) — self-review, insufficient
        - Veto Contract (Execute Agent) — requires TaskSpec to exist
        - Human Reviewer — not per-session
      compared_against_request:
        - "independent per-session SADP compliance verification"
        - "prevent Plan Agent self-bypass (LL-009)"

    rules_checked:
      - core-008
    lessons_checked:
      - LL-007
      - LL-009

    sufficiency_decision: new_delta_required
    decision: build_delta
    delta_justification: "No independent per-session audit mechanism exists. LL-009 proves Veto Contract + Human Reviewer cannot catch Plan Agent bypassing SADP entirely."
  ```

- **Conflict Registry**:
  ```yaml
  conflict_registry:
    read_set:
      - docs/agent-runtime/sub-agent-dispatch-protocol.md
      - docs/agent-runtime/lessons-learned.md
      - docs/agent-runtime/capability-inventory.md
    write_set:
      - docs/agent-runtime/session-ledger.schema.md
      - docs/agent-runtime/audit-record.schema.md
      - docs/agent-runtime/sub-agent-dispatch-protocol.md
    protected_files_touched: true
    conflict_level: high
  ```

- **Acceptance Gates**:
  1. session-ledger.schema.md exists with required fields (session_id, changed_files, taskspecs_created, execution_reports_created, protected_files_touched, cumulative_write_set, sadp_required, audit_required, audit_status)
  2. audit-record.schema.md exists with required fields (session_id, findings, decision, rationale)
  3. SADP amended: §3.3a renamed to §3.3b, new §3.3a Plan Auditor with anti-bypass rule
  4. Hard rule: "Any session with git diff must produce Audit Record. Plan Agent cannot self-audit."
  5. R1-R6 regression all PASS after changes

- **Expected Output**: 2 new schema files + 1 SADP amendment; R1-R6 all PASS
- **Rollback**: Delete 2 new files; `git checkout` SADP
- **Report To**: this session (Codex plan agent)
