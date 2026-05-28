# TaskSpec: P0-Structural-Sync

- **ID**: task-p0-sync-001
- **Batch**: batch-p0-structural-sync
- **Risk**: low
- **Priority**: P0
- **Goal**: Synchronize 8 downstream files after SADP/capability-inventory governance changes. Fix structural inconsistencies: schemas missing fields, AGENTS.md doc map stale, header counts wrong, INSTANTIATION.md incomplete, LL-008 unrecorded, governance manifest missing.
- **Context**: SADP was upgraded (evidence-based Gate 0, Cumulative Trigger Window, expiration policy, canaries). Capability inventory gained expiration policy. But JSON schemas, AGENTS.md, INSTANTIATION.md, and header counts still reflected pre-upgrade state.
- **Allowed Files**:
  - schemas/agent-runtime/task-spec.schema.json
  - schemas/agent-runtime/execution-report.schema.json
  - AGENTS.md
  - docs/agent-runtime/capability-inventory.md
  - docs/agent-runtime/lessons-learned.md
  - templates/runtime-bootstrap/INSTANTIATION.md
  - docs/agent-runtime/governance-manifest.md (new)
- **Forbidden**:
  - Do not modify rules/core.md (correct as-is)
  - Do not modify SADP protocol (correct as-is)
  - Do not modify any other files
  - No git commit/push

- **Gate 0 Ledger**:
  ```yaml
  gate_0:
    triggered: true
    trigger_reason: "8 downstream files need sync after governance changes"

    inventory_evidence:
      queried_sources:
        - capability-inventory.md
        - sub-agent-dispatch-protocol.md
      matched_capabilities:
        - rg/Grep/Read (CAP-002) — filesystem search
        - Shell (CAP-003) — PowerShell file editing
        - Codex direct — filesystem write
      compared_against_request:
        - "sync 8 downstream files after governance changes"
        - "update JSON schemas with new fields"
        - "update document map and header counts"

    rules_checked:
      - core-008
    lessons_checked:
      - LL-007
      - LL-008

    sufficiency_decision: new_delta_required
    decision: build_delta
    delta_justification: "No automated cascade sync tool exists. Manual synchronization of 8 downstream files is required."
  ```

- **Conflict Registry**:
  ```yaml
  conflict_registry:
    read_set:
      - schemas/agent-runtime/task-spec.schema.json
      - schemas/agent-runtime/execution-report.schema.json
      - AGENTS.md
      - docs/agent-runtime/capability-inventory.md
      - docs/agent-runtime/lessons-learned.md
      - templates/runtime-bootstrap/INSTANTIATION.md
    write_set:
      - schemas/agent-runtime/task-spec.schema.json
      - schemas/agent-runtime/execution-report.schema.json
      - AGENTS.md
      - docs/agent-runtime/capability-inventory.md
      - docs/agent-runtime/lessons-learned.md
      - templates/runtime-bootstrap/INSTANTIATION.md
      - docs/agent-runtime/governance-manifest.md
      - docs/agent-runtime/dependency-canaries.md
    protected_files_touched: true
    conflict_level: high
  ```

- **Acceptance Gates**:
  1. task-spec.schema.json contains gate_0.inventory_evidence + conflict_registry fields
  2. execution-report.schema.json contains trust_record + fallback_record
  3. AGENTS.md doc map lists SADP, lessons, canaries, manifest, bootstrap, schemas
  4. AGENTS.md correctly states "8 rules" (not 6)
  5. capability-inventory.md header says "28 capabilities" (not 27)
  6. INSTANTIATION.md includes Step 2b governance manifest verification
  7. LL-008 recorded in lessons-learned.md
  8. governance-manifest.md created with current hashes
  9. All R1-R6 regression tests PASS

- **Expected Output**: 7 modified files + 2 new files; R1-R6 all PASS
- **Rollback**: `git checkout --` on the 7 tracked files; delete 2 new files
- **Report To**: this session (Codex plan agent)
