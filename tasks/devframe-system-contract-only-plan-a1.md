# TaskSpec: DEVFRAME-SYSTEM-CONTRACT-ONLY-PLAN-A1

**ID**: devframe-system-contract-only-plan-a1
**Priority**: P1
**Status**: in_progress
**Type**: governance_contract_planning

## Intent

Define the minimum contract-only planning boundary for `devframe-system` while
physical bootstrap remains blocked. This task updates governance documentation
inside `D:\agent-acceptance` only. It must not create `D:\devframe-system`, add
submodules, execute external runtimes, or mutate external repositories.

gate_0:
  triggered: true
  trigger_reason: "Proceed along the READY contract-only planning path identified by the Phase 0.5 readiness rollup."
  inventory_evidence:
    queried_sources:
      - "docs/agent-runtime/integration-contracts.md"
      - "docs/agent-runtime/inactive-frame-registry.md"
      - "_reports/devframe-system-phase05-readiness-rollup-a1/READINESS_ROLLUP.md"
      - "schemas/agent-runtime"
      - "schemas/resource-integration"
    matched_capabilities:
      - sadp_governance
      - contract_only_planning
      - inactive_frame_registry
      - external_runtime_non_execution_gate
  rules_checked: [core-001, core-004, core-005, core-007, core-008, review-001, git-001]
  sufficiency_decision: existing_sufficient
  decision: reuse
  delta_justification: "The task records planning contracts and inactive frame boundaries only."

conflict_registry:
  read_set:
    - "docs/agent-runtime/integration-contracts.md"
    - "docs/agent-runtime/inactive-frame-registry.md"
    - "_reports/devframe-system-phase05-readiness-rollup-a1/READINESS_ROLLUP.md"
    - "schemas/agent-runtime"
    - "schemas/resource-integration"
    - ".ai/current-task.yaml"
  write_set:
    - tasks/devframe-system-contract-only-plan-a1.md
    - .ai/current-task.yaml
    - docs/agent-runtime/inactive-frame-registry.md
    - _reports/devframe-system-contract-only-plan-a1/**
    - _evidence/DEVFRAME-SYSTEM-CONTRACT-ONLY-PLAN-A1/**
    - hooks/sealed-files-manifest.json
    - _evidence/hook-output/**
  governance_adjacent_files_modified:
    - ".ai/current-task.yaml"
    - "docs/agent-runtime/inactive-frame-registry.md"
  protected_files_touched: false
  conflict_level: medium

**Acceptance Gates**:
  1. Runner start, edit-check, and finish complete without blocking.
  2. Contract-only plan defines minimal future inputs/outputs without creating active runtime contracts.
  3. Inactive frame registry includes dev-frame-opencode, devframe-control-plane, test-frame, and devframe-system boundaries.
  4. Plan preserves physical bootstrap as blocked and external runtime execution as forbidden.
  5. No external repository mutation, external runtime, external test, submodule command, or paper workflow is executed.
  6. Targeted checks pass and staged commit contains only this contract-only package plus hook-managed manifest.
