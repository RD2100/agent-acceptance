# TaskSpec: Session Ledger Auto + Pre-write Gate Extension

- **ID**: task-p1-auto-audit-001
- **Batch**: batch-p1-automation
- **Risk**: medium
- **Priority**: P1
- **Goal**: (1) Create a PowerShell script that auto-generates session ledger from git diff — eliminating the manual-fill vulnerability (LL-009 root cause). (2) Extend pre-edit.governance.ps1 to block writes to governance files unless a valid TaskSpec exists — closing the post-hoc audit gap (LL-010).
- **Context**: Session Ledger schema exists but requires Plan Agent to manually fill it — same honesty-dependence as early Gate 0. Pre-edit hook only blocks memory/sealed/secrets writes — governance files (AGENTS.md, rules/*, SADP, inventory, lessons) are unprotected from unauthorized modification.
- **Allowed Files**:
  - scripts/New-SessionLedger.ps1 (new)
  - hooks/pre-edit.governance.ps1 (amend — add governance file protection)
  - hooks/sealed-files-manifest.json (amend — add governance file patterns)
- **Forbidden**:
  - Do not modify core rules
  - Do not modify SADP protocol
  - Do not touch MCP config (Phase 0-5 constraint)
  - Do not change hook registration mechanism

- **Gate 0 Ledger**:
  ```yaml
  gate_0:
    triggered: true
    trigger_reason: "New automation script + governance hook extension"

    inventory_evidence:
      queried_sources:
        - capability-inventory.md
        - hooks/pre-edit.governance.ps1
        - hooks/sealed-files-manifest.json
        - scripts/
        - session-ledger.schema.md
      matched_capabilities:
        - pre-edit.governance.ps1 (CAP-015) — existing hook, partial coverage (memory/sealed/secrets only)
        - Scripts (CAP-020) — runner scripts exist but none for ledger generation
        - Shell (CAP-003) — PowerShell execution
      compared_against_request:
        - "auto-generate session ledger from git diff"
        - "block unauthorized writes to governance files"

    rules_checked:
      - core-008
    lessons_checked:
      - LL-009
      - LL-010

    sufficiency_decision: new_delta_required
    decision: build_delta
    delta_justification: "No auto-ledger script exists. Hook covers only 3 file categories, not governance files. Both are net-new automation."
  ```

- **Conflict Registry**:
  ```yaml
  conflict_registry:
    read_set:
      - hooks/pre-edit.governance.ps1
      - hooks/sealed-files-manifest.json
      - docs/agent-runtime/session-ledger.schema.md
    write_set:
      - scripts/New-SessionLedger.ps1
      - hooks/pre-edit.governance.ps1
      - hooks/sealed-files-manifest.json
    protected_files_touched: false
    conflict_level: medium
  ```

- **Acceptance Gates**:
  1. New-SessionLedger.ps1 exists and generates valid session_ledger YAML from `git diff --stat`
  2. pre-edit.governance.ps1 blocks writes to governance files (AGENTS.md, rules/*, SADP, inventory, lessons, schemas)
  3. sealed-files-manifest.json updated with governance file patterns
  4. Existing protections (memory/sealed/secrets) still work after changes
  5. R1-R6 regression all PASS

- **Expected Output**: 1 new script + 2 amended files
- **Rollback**: Delete New-SessionLedger.ps1; `git checkout` hook files
- **Report To**: this session
