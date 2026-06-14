# TaskSpec: DEVFRAME-SYSTEM-ACTIVATION-GATES-A1

**ID**: devframe-system-activation-gates-a1
**Priority**: P1
**Status**: in_progress
**Type**: governance_activation_gate

## Intent

Create a canonical activation-gates document for the future `devframe-system`
superproject. This records the exact conditions for strict clean-baseline
bootstrap versus dirty-aware skeleton bootstrap, without creating
`D:\devframe-system`, adding submodules, executing external runtimes, or
mutating external repositories.

gate_0:
  triggered: true
  trigger_reason: "Continue Phase 0.5 by converting readiness reports and draft contracts into an executable activation gate document."
  inventory_evidence:
    queried_sources:
      - "_reports/devframe-system-phase05-readiness-rollup-a1/READINESS_ROLLUP.md"
      - "_reports/devframe-system-contract-only-plan-a1/CONTRACT_ONLY_PLAN.md"
      - "_reports/devframe-system-contract-drafts-a1/CONTRACT_DRAFTS_REPORT.md"
      - "schemas/draft/devframe-system-contracts.schema.draft.json"
    matched_capabilities:
      - sadp_governance
      - contract_only_planning
      - activation_gate_documentation
      - external_runtime_non_execution_gate
  rules_checked: [core-001, core-004, core-005, core-007, core-008, review-001, git-001]
  sufficiency_decision: existing_sufficient
  decision: reuse
  delta_justification: "The task creates governance documentation only and preserves inactive external-frame boundaries."

conflict_registry:
  read_set:
    - "_reports/devframe-system-phase05-readiness-rollup-a1/READINESS_ROLLUP.md"
    - "_reports/devframe-system-contract-only-plan-a1/CONTRACT_ONLY_PLAN.md"
    - "_reports/devframe-system-contract-drafts-a1/CONTRACT_DRAFTS_REPORT.md"
    - "schemas/draft/devframe-system-contracts.schema.draft.json"
    - ".ai/current-task.yaml"
  write_set:
    - tasks/devframe-system-activation-gates-a1.md
    - .ai/current-task.yaml
    - docs/agent-runtime/devframe-system-activation-gates.md
    - _reports/devframe-system-activation-gates-a1/**
    - _evidence/DEVFRAME-SYSTEM-ACTIVATION-GATES-A1/**
    - hooks/sealed-files-manifest.json
    - _evidence/hook-output/**
  governance_adjacent_files_modified:
    - ".ai/current-task.yaml"
    - "docs/agent-runtime/devframe-system-activation-gates.md"
  protected_files_touched: false
  conflict_level: medium

**Acceptance Gates**:
  1. Runner start, edit-check, and finish complete without blocking.
  2. Activation gates document names both allowed future routes: strict clean-baseline bootstrap and dirty-aware skeleton.
  3. Document keeps `test-frame` as controlled verification runtime candidate, not plugin and not GateResult authority.
  4. Document records that external runtimes, submodule add, cleanup/reset/stash, and paper workflow remain forbidden in Phase 0.5.
  5. No `D:\devframe-system` directory is created and no external repository is mutated.
  6. Targeted checks pass and staged commit contains only this activation-gates package plus hook-managed manifest.
