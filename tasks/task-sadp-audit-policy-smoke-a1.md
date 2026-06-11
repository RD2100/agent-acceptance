# TaskSpec: SADP-AUDIT-POLICY-SMOKE-A1

- **ID**: SADP-AUDIT-POLICY-SMOKE-A1
- **Batch**: SHARED-CDP-V2-REVIEW
- **Risk**: low
- **Priority**: P1
- **Goal**: Add smoke test ensuring sadp-audit.ps1 governance patterns cover all protected files in SADP_POLICY.json
- **Context**: ChatGPT R8 recommended verifying that PowerShell audit and Python enforcer share consistent policy. The Python enforcer already has drift tests against SADP_POLICY.json. The PowerShell audit script has hardcoded governancePatterns that should also cover all protected files.

- **Gate 0 Ledger**:
  ```yaml
  gate_0:
    triggered: true
    trigger_reason: "New test required for cross-consumer policy consistency"
    inventory_evidence:
      queried_sources:
        - capability-inventory.md
        - scripts/sadp-audit.ps1
        - scripts/sadp_pre_task_enforcer.py
        - .sadp/SADP_POLICY.json
        - tests/test_sadp_pre_task_enforcer.py
      matched_capabilities:
        - "TestPolicyDrift class already validates enforcer <-> SADP_POLICY.json"
        - "No existing test validates sadp-audit.ps1 patterns <-> SADP_POLICY.json"
      sufficiency_decision: new_delta_required
      delta_justification: "Gap identified by ChatGPT R8 reviewer — no existing test covers PowerShell audit script governance pattern consistency with SADP_POLICY.json"
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
      - scripts/sadp_pre_task_enforcer.py
      - tests/test_sadp_pre_task_enforcer.py
    write_set:
      - tests/test_sadp_pre_task_enforcer.py
    conflict_level: low
    protected_files_touched: []
  ```

- **Acceptance Gates**:
  1. Smoke test class exists validating sadp-audit.ps1 governance patterns vs SADP_POLICY.json
  2. Test verifies each protected_file has a matching governance pattern in sadp-audit.ps1
  3. Test verifies SADP_POLICY.json is valid JSON with required schema
  4. Any coverage gaps documented as known limitations
  5. Full regression suite passes
