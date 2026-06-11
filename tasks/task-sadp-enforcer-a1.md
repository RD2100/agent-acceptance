# TaskSpec: QODERWORK-SADP-ENFORCER-A1 — Pre-Task SADP Enforcement

- **ID**: QODERWORK-SADP-ENFORCER-A1
- **Batch**: shared-cdp-v2-governance
- **Risk**: medium
- **Priority**: P0
- **Goal**: Create a runtime SADP enforcement mechanism that validates compliance BEFORE agents edit code, closing the gap where sadp-audit.ps1 only enforces at git commit time.
- **Context**: sadp-audit.ps1 (task-ext-enforce-001) enforces SADP at commit boundary. But agents can make edits before commit, potentially violating SADP rules (no TaskSpec, write_set scope creep, protected file access). This enforcer adds pre-task, pre-edit, and post-task validation points.
- **Allowed Files**:
  - scripts/sadp_pre_task_enforcer.py (new)
  - tests/test_sadp_pre_task_enforcer.py (new)
- **Forbidden**:
  - Do not modify sadp-audit.ps1 (separate mechanism)
  - Do not modify core rules
  - Do not modify SADP protocol
  - Do not modify .git/hooks/

- **Gate 0 Ledger**:
  ```yaml
  gate_0:
    triggered: true
    trigger_reason: "P0 — runtime SADP enforcement gap at pre-task/pre-edit boundary"

    inventory_evidence:
      queried_sources:
        - capability-inventory.md (checked: no existing pre-task enforcer)
        - sub-agent-dispatch-protocol.md (§0.1 Gate 0, §0.2 Conflict Registry, §0.0a)
        - scripts/sadp-audit.ps1 (existing commit-time enforcer — reuse base)
        - tasks/task-ext-enforce-001.md (existing enforcement TaskSpec)
        - rules/core.md (core-003 phase boundary, core-008 reuse-before-build)
      matched_capabilities:
        - sadp-audit.ps1 (commit-time enforcement — reused as complement)
      compared_against_request:
        - "pre-task validation: TaskSpec exists, Gate 0 valid, no conflicts"
        - "pre-edit validation: file in write_set, no protected files"
        - "post-task validation: ExecutionReport exists, gates evaluated"

    rules_checked:
      - core-003 (phase boundary: enforce before edit, not just commit)
      - core-008 (reuse: sadp-audit.ps1 complemented, not replaced)
    lessons_checked:
      - LL-009 (external enforcement gap — this closes the pre-task gap)

    sufficiency_decision: existing_partial
    decision: build_delta
    delta_justification: "sadp-audit.ps1 only fires at git commit. No mechanism validates SADP compliance before agents start editing. Pre-task enforcer fills this gap with 3 enforcement points: pre_task, pre_edit, post_task."
  ```

- **Conflict Registry**:
  ```yaml
  conflict_registry:
    read_set:
      - tasks/ (directory listing for TaskSpec discovery)
      - _evidence/ (directory listing for ExecutionReport discovery)
      - reports/ (directory listing for report discovery)
    write_set:
      - scripts/sadp_pre_task_enforcer.py
      - tests/test_sadp_pre_task_enforcer.py
    protected_files_touched: false
    conflict_level: low
  ```

- **Acceptance Gates**:
  1. pre_task: Nonexistent TaskSpec → BLOCKED (exit 1)
  2. pre_task: Valid TaskSpec with Gate 0 + CR → PASS (exit 0)
  3. pre_task: TaskSpec without Gate 0 → BLOCKED
  4. pre_task: TaskSpec without Conflict Registry → BLOCKED
  5. pre_task: Protected file in write_set → BLOCKED
  6. pre_edit: Protected governance file → BLOCKED (exit 1)
  7. pre_edit: File in write_set → PASS (exit 0)
  8. pre_edit: File not in write_set → WARNING (exit 2)
  9. post_task: Completed task with ER → PASS (exit 0)
  10. post_task: Missing ExecutionReport → BLOCKED (exit 1)
  11. Full regression: all existing tests still pass
  12. Enforcer tests: all pass

- **Expected Output**: 1 script + 1 test file, complementing sadp-audit.ps1
- **Rollback**: Delete sadp_pre_task_enforcer.py and test file
- **Report To**: ChatGPT conversation 6a26cc03
