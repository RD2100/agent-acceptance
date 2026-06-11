# TaskSpec: QODERWORK-SADP-ENFORCER-HARDEN-A1 — Enforcer Hardening

- **ID**: QODERWORK-SADP-ENFORCER-HARDEN-A1
- **Batch**: shared-cdp-v2-governance
- **Risk**: medium
- **Priority**: P0
- **Goal**: Harden the SADP pre-task enforcer based on ChatGPT R5 feedback. Expand protected files, add self-protection, implement priority-based scope creep blocking, create unified policy source.
- **Context**: R5 reviewer identified 5 limitations: (1) enforcer not mandatory, (2) protected files incomplete, (3) scope creep only WARNING for P0/P1, (4) no unified policy source, (5) missing AGENTS.md workflow.
- **Allowed Files**:
  - scripts/sadp_pre_task_enforcer.py (modify — add hardening)
  - tests/test_sadp_pre_task_enforcer.py (modify — add tests)
  - .sadp/SADP_POLICY.json (new — unified policy)
  - .sadp/TRIGGER_RULES.json (new — trigger rules)
- **Forbidden**:
  - Do not modify sadp-audit.ps1 (self-protecting)
  - Do not modify core rules
  - Do not modify SADP protocol

- **Gate 0 Ledger**:
  ```yaml
  gate_0:
    triggered: true
    trigger_reason: "P0 — reviewer-identified hardening gaps in SADP enforcer"
    inventory_evidence:
      queried_sources:
        - scripts/sadp_pre_task_enforcer.py (existing enforcer — modify target)
        - scripts/sadp-audit.ps1 (existing audit — complement, not replace)
        - .sadp/ (new directory for unified policy)
        - rules/core.md (P0 rules reference)
      matched_capabilities:
        - sadp_pre_task_enforcer.py (existing — hardened)
        - sadp-audit.ps1 (existing — policy source shared)
      compared_against_request:
        - "expand protected files list"
        - "add enforcer self-protection"
        - "P0/P1 scope creep → BLOCKED"
        - "unified policy source"
    rules_checked: [core-003, core-008]
    sufficiency_decision: existing_partial
    decision: build_delta
    delta_justification: "Protected files list and scope creep blocking are gaps in existing enforcer. New .sadp/ directory needed for unified policy."
  ```

- **Conflict Registry**:
  ```yaml
  conflict_registry:
    read_set:
      - scripts/sadp_pre_task_enforcer.py
      - .sadp/ (new)
    write_set:
      - scripts/sadp_pre_task_enforcer.py
      - tests/test_sadp_pre_task_enforcer.py
      - .sadp/SADP_POLICY.json
      - .sadp/TRIGGER_RULES.json
    protected_files_touched: false
    conflict_level: low
  ```

- **Acceptance Gates**:
  1. Protected files expanded (include SADP policy + enforcer scripts)
  2. Self-protecting files defined (enforcer + audit)
  3. P0 scope creep → BLOCKED (exit 1)
  4. SADP_POLICY.json created with scope_creep_by_priority
  5. TRIGGER_RULES.json created
  6. Policy loading from .sadp/SADP_POLICY.json
  7. Priority parsing from TaskSpec
  8. All 43 enforcer tests pass
  9. Full regression: 1003 passed

- **Expected Output**: Hardened enforcer + unified policy + 16 new tests
- **Rollback**: git checkout + delete .sadp/
- **Report To**: ChatGPT conversation 6a26cc03
