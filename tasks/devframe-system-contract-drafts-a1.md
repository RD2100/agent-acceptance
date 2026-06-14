# TaskSpec: DEVFRAME-SYSTEM-CONTRACT-DRAFTS-A1

**ID**: devframe-system-contract-drafts-a1
**Priority**: P1
**Status**: in_progress
**Type**: governance_contract_draft

## Intent

Create an inactive draft schema packet for the future `devframe-system`
contract-only boundary. This must not activate validation, create
`D:\devframe-system`, add submodules, execute external runtimes, or mutate
external repositories.

gate_0:
  triggered: true
  trigger_reason: "Continue contract-only progress by turning planning contract names into inactive draft schema definitions."
  inventory_evidence:
    queried_sources:
      - "schemas/draft/boundary-envelope.schema.draft.json"
      - "schemas/draft/frame-manifest.schema.draft.json"
      - "_reports/devframe-system-contract-only-plan-a1/CONTRACT_ONLY_PLAN.md"
    matched_capabilities:
      - sadp_governance
      - contract_only_planning
      - draft_schema_authoring
      - external_runtime_non_execution_gate
  rules_checked: [core-001, core-004, core-005, core-007, core-008, review-001, git-001]
  sufficiency_decision: existing_sufficient
  decision: reuse
  delta_justification: "The task creates inactive draft schema documentation only."

conflict_registry:
  read_set:
    - "schemas/draft/boundary-envelope.schema.draft.json"
    - "schemas/draft/frame-manifest.schema.draft.json"
    - "_reports/devframe-system-contract-only-plan-a1/CONTRACT_ONLY_PLAN.md"
    - ".ai/current-task.yaml"
  write_set:
    - tasks/devframe-system-contract-drafts-a1.md
    - .ai/current-task.yaml
    - schemas/draft/devframe-system-contracts.schema.draft.json
    - _reports/devframe-system-contract-drafts-a1/**
    - _evidence/DEVFRAME-SYSTEM-CONTRACT-DRAFTS-A1/**
    - hooks/sealed-files-manifest.json
    - _evidence/hook-output/**
  governance_adjacent_files_modified:
    - ".ai/current-task.yaml"
  protected_files_touched: false
  conflict_level: medium

**Acceptance Gates**:
  1. Runner start, edit-check, and finish complete without blocking.
  2. Draft schema is valid JSON and explicitly marked DRAFT / NOT ACTIVE.
  3. Draft schema covers RepoBaselineRecord, SuperprojectLock, RuntimeExecutionRequest, FrameActivationRecord, and VerificationRuntimeResult.
  4. Draft schema preserves GateResult authority as forbidden for external frames.
  5. No validator wiring, external repo mutation, external runtime/test, submodule command, or paper workflow is executed.
  6. Targeted checks pass and staged commit contains only this draft package plus hook-managed manifest.
