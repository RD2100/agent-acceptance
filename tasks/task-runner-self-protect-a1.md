# TaskSpec: QODERWORK-TASK-RUNNER-SELF-PROTECT-A1

- **ID**: QODERWORK-TASK-RUNNER-SELF-PROTECT-A1
- **Batch**: shared-cdp-v2-governance
- **Risk**: low
- **Priority**: P2
- **Goal**: Close the self-protection gap identified in R7: add qoderwork_task_runner.py to SELF_PROTECTING_FILES and add policy drift tests to prevent future divergence between enforcer code and SADP_POLICY.json.
- **Context**: R7 reviewer (L1) noted runner was not in self-protecting list, and audit/enforcer policy drift was not tested.
- **Allowed Files**:
  - scripts/sadp_pre_task_enforcer.py (modify — add runner to SELF_PROTECTING_FILES)
  - .sadp/SADP_POLICY.json (modify — add runner to self_protecting_enforcer_files)
  - tests/test_sadp_pre_task_enforcer.py (modify — add drift tests + runner self-protect test)
- **Forbidden**:
  - Do not modify qoderwork_task_runner.py (now self-protecting)
  - Do not modify sadp-audit.ps1

- **Gate 0 Ledger**:
  ```yaml
  gate_0:
    triggered: true
    trigger_reason: "P2 — R7 reviewer identified self-protection gap and policy drift risk"
    inventory_evidence:
      queried_sources:
        - scripts/sadp_pre_task_enforcer.py (SELF_PROTECTING_FILES set)
        - .sadp/SADP_POLICY.json (self_protecting_enforcer_files list)
        - tests/test_sadp_pre_task_enforcer.py (existing tests)
      matched_capabilities:
        - sadp_pre_task_enforcer (existing — extend self-protecting set)
      compared_against_request:
        - "runner should be self-protecting"
        - "policy drift between enforcer and JSON should be detected"
    rules_checked: [core-008]
    sufficiency_decision: existing_sufficient
    decision: reuse
  ```

- **Conflict Registry**:
  ```yaml
  conflict_registry:
    read_set:
      - scripts/sadp_pre_task_enforcer.py
      - .sadp/SADP_POLICY.json
    write_set:
      - scripts/sadp_pre_task_enforcer.py
      - .sadp/SADP_POLICY.json
      - tests/test_sadp_pre_task_enforcer.py
    protected_files_touched: false
    conflict_level: low
  ```

- **Acceptance Gates**:
  1. qoderwork_task_runner.py in SELF_PROTECTING_FILES
  2. edit-check --file scripts/qoderwork_task_runner.py → BLOCKED (exit 1)
  3. Policy drift test: self_protecting_files match
  4. Policy drift test: protected_files match
  5. Policy drift test: governance_adjacent match
  6. Full regression: 1022 passed

- **Expected Output**: 3 files modified, 6 new tests
- **Rollback**: git checkout
- **Report To**: ChatGPT conversation 6a26cc03
