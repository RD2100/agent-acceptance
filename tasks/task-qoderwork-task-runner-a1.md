# TaskSpec: QODERWORK-TASK-RUNNER-A1 — Unified Task Runner

- **ID**: QODERWORK-TASK-RUNNER-A1
- **Batch**: shared-cdp-v2-governance
- **Risk**: low
- **Priority**: P1
- **Goal**: Create unified mandatory entry point for P0/P1 task execution. Agents call start/edit-check/finish instead of directly editing files.
- **Context**: Enforcer provides the validation logic but agents can bypass it. Task Runner is the CLI wrapper that makes enforcement ergonomic and mandatory.
- **Allowed Files**:
  - scripts/qoderwork_task_runner.py (new)
  - tests/test_qoderwork_task_runner.py (new)
- **Forbidden**:
  - Do not modify enforcer or audit scripts
  - Do not modify governance files

- **Gate 0 Ledger**:
  ```yaml
  gate_0:
    triggered: true
    trigger_reason: "P1 — mandatory task runner for agent workflow enforcement"
    inventory_evidence:
      queried_sources:
        - scripts/sadp_pre_task_enforcer.py (existing — wrapped by runner)
        - sub-agent-dispatch-protocol.md (workflow requirements)
      matched_capabilities:
        - sadp_pre_task_enforcer (reused as backend)
      compared_against_request:
        - "start: validate before editing"
        - "edit-check: validate each file modification"
        - "finish: validate completion artifacts"
    rules_checked: [core-003, core-008]
    sufficiency_decision: existing_sufficient
    decision: reuse
    delta_justification: "Runner is a thin CLI wrapper around existing enforcer. No new validation logic needed."
  ```

- **Conflict Registry**:
  ```yaml
  conflict_registry:
    read_set:
      - scripts/sadp_pre_task_enforcer.py
    write_set:
      - scripts/qoderwork_task_runner.py
      - tests/test_qoderwork_task_runner.py
    protected_files_touched: false
    conflict_level: low
  ```

- **Acceptance Gates**:
  1. start: delegates to pre_task correctly
  2. edit-check: delegates to pre_edit correctly
  3. finish: delegates to post_task correctly
  4. Exit codes: 0=PASS, 1=BLOCKED, 2=WARNING
  5. Full integration workflow passes
  6. 13 runner tests pass
  7. Full regression: 1016 passed

- **Expected Output**: 1 runner script + 1 test file (13 tests)
- **Rollback**: Delete runner and test files
- **Report To**: ChatGPT conversation 6a26cc03
