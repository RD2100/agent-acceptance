# TaskSpec: External Enforcement — sadp-audit.ps1 + pre-commit hook

- **ID**: task-ext-enforce-001
- **Batch**: batch-external-enforcement
- **Risk**: medium
- **Priority**: P0
- **Goal**: Create the first external (non-agent-triggered) SADP enforcement mechanism: a git pre-commit hook that runs sadp-audit.ps1 to verify TaskSpec/ExecutionReport/AuditRecord exist when git diff shows qualifying changes. This closes the LL-009/LL-010 gap where Plan Agent can silently bypass all agent-internal governance.
- **Context**: LL-009 proved Plan Agent can skip SADP entirely. LL-010 proved post-hoc audit can detect but not prevent. All existing mechanisms (Gate 0, Plan Auditor, Pre-write Hook, Session Ledger) are agent-triggered. The minimal external enforcement is a git pre-commit hook that runs independently of agent decision.
- **Allowed Files**:
  - scripts/sadp-audit.ps1 (new)
  - .git/hooks/pre-commit (new or amend)
- **Forbidden**:
  - Do not modify core rules
  - Do not modify SADP protocol
  - Do not modify any other files

- **Gate 0 Ledger**:
  ```yaml
  gate_0:
    triggered: true
    trigger_reason: "New external enforcement mechanism — first non-agent-triggered governance"

    inventory_evidence:
      queried_sources:
        - capability-inventory.md
        - sub-agent-dispatch-protocol.md
        - lessons-learned.md
        - .git/hooks/ (checked: empty)
      matched_capabilities:
        - None — no external enforcement exists
      compared_against_request:
        - "independent git diff → TaskSpec verification"
        - "prevent commit without SADP compliance"

    rules_checked:
      - core-008
    lessons_checked:
      - LL-009
      - LL-010

    sufficiency_decision: new_delta_required
    decision: build_delta
    delta_justification: "No external enforcement mechanism exists. All governance is agent-triggered. git pre-commit hook is OS-level, independent of agent decision."
  ```

- **Conflict Registry**:
  ```yaml
  conflict_registry:
    read_set:
      - .git/hooks/ (directory listing)
    write_set:
      - scripts/sadp-audit.ps1
      - .git/hooks/pre-commit
    protected_files_touched: false
    conflict_level: low
  ```

- **Acceptance Gates**:
  1. sadp-audit.ps1 exists and is valid PowerShell
  2. pre-commit hook calls sadp-audit.ps1
  3. Test 1: git diff exists + no TaskSpec → pre-commit FAILS (exit 1)
  4. Test 2: governance file touched + no Audit Record → pre-commit FAILS
  5. Test 3: clean state (no diff) → pre-commit PASSES
  6. R1-R6 regression all PASS

- **Expected Output**: 2 files; independent git-level enforcement
- **Rollback**: Delete sadp-audit.ps1; `git checkout` pre-commit
- **Report To**: this session
