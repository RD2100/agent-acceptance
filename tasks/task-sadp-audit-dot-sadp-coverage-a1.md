# TaskSpec: SADP-AUDIT-DOT-SADP-COVERAGE-A1

- **ID**: SADP-AUDIT-DOT-SADP-COVERAGE-A1
- **Batch**: SHARED-CDP-V2-REVIEW
- **Risk**: low
- **Priority**: P1
- **Goal**: Add .sadp/ directory to sadp-audit.ps1 governancePatterns so that .sadp/SADP_POLICY.json and .sadp/TRIGGER_RULES.json trigger SADP-required at commit-time audit
- **Context**: ChatGPT R9 identified that .sadp/ policy files are protected by pre-edit enforcer but NOT detected by commit-time audit governancePatterns. This leaves a bypass path where .sadp/ files could be committed without triggering SADP-required flag.

- **Gate 0 Ledger**:
  ```yaml
  gate_0:
    triggered: true
    trigger_reason: "R9 limitation — close .sadp/ audit coverage gap"
    inventory_evidence:
      queried_sources:
        - capability-inventory.md
        - scripts/sadp-audit.ps1
        - .sadp/SADP_POLICY.json
        - tests/test_sadp_pre_task_enforcer.py
      matched_capabilities:
        - "TestAuditPolicySmoke already validates governance pattern coverage"
        - "sadp-audit.ps1 $governancePatterns can be extended"
      sufficiency_decision: existing_sufficient
    rules_checked:
      - rules/core.md
    lessons_checked:
      - docs/agent-runtime/lessons-learned.md
    decision: proceed
  ```

- **Conflict Registry**:
  ```yaml
  conflict_registry:
    read_set:
      - scripts/sadp-audit.ps1
      - .sadp/SADP_POLICY.json
      - tests/test_sadp_pre_task_enforcer.py
    write_set:
      - scripts/sadp-audit.ps1
      - tests/test_sadp_pre_task_enforcer.py
    conflict_level: low
    protected_files_touched:
      - scripts/sadp-audit.ps1 (self-protecting — HUMAN_REQUIRED)
  ```

- **Acceptance Gates**:
  1. .sadp/ pattern added to $governancePatterns in sadp-audit.ps1
  2. Smoke test verifies .sadp/SADP_POLICY.json matched by governance pattern
  3. Smoke test verifies .sadp/TRIGGER_RULES.json matched by governance pattern
  4. test_sadp_directory_pattern_coverage upgraded from warning to pass
  5. test_all_protected_files_coverage_report has no warnings for .sadp/ files
  6. Full regression suite passes
