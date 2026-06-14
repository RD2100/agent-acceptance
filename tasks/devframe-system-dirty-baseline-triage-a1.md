# TaskSpec: DEVFRAME-SYSTEM-DIRTY-BASELINE-TRIAGE-A1

**ID**: devframe-system-dirty-baseline-triage-a1
**Priority**: P1
**Status**: in_progress
**Type**: governance_triage

## Intent

Classify the dirty baseline that blocks `devframe-system` Phase 0.5 physical
bootstrap. This task must not clean, reset, stash, commit, test, or execute any
external repository.

gate_0:
  triggered: true
  trigger_reason: "Continue ordered progress after the Phase 0.5 strict gate recorded HUMAN_REQUIRED."
  inventory_evidence:
    queried_sources:
      - "D:/agent-acceptance git status and diff stat"
      - "D:/dev-frame-opencode git status and diff stat"
      - "D:/devframe-control-plane git status and diff stat"
      - "D:/test-frame git status and diff stat"
      - "_reports/devframe-system-phase05-strict-gate-a1/PREFLIGHT_REPORT.md"
    matched_capabilities:
      - sadp_governance
      - superproject_preflight
      - dirty_baseline_triage
      - external_runtime_non_execution_gate
  rules_checked: [core-004, core-005, core-007, core-008, review-001, git-001]
  sufficiency_decision: existing_sufficient
  decision: reuse
  delta_justification: "The required capability is governance triage and read-only repository inventory."

conflict_registry:
  read_set:
    - "D:/agent-acceptance git status and diff stat"
    - "D:/dev-frame-opencode git status and diff stat"
    - "D:/devframe-control-plane git status and diff stat"
    - "D:/test-frame git status and diff stat"
    - "_reports/devframe-system-phase05-strict-gate-a1/PREFLIGHT_REPORT.md"
    - ".ai/current-task.yaml"
  write_set:
    - tasks/devframe-system-dirty-baseline-triage-a1.md
    - .ai/current-task.yaml
    - _reports/devframe-system-dirty-baseline-triage-a1/**
    - _evidence/DEVFRAME-SYSTEM-DIRTY-BASELINE-TRIAGE-A1/**
    - hooks/sealed-files-manifest.json
    - _evidence/hook-output/**
  governance_adjacent_files_modified:
    - ".ai/current-task.yaml"
  protected_files_touched: false
  conflict_level: medium

**Acceptance Gates**:
  1. Runner start, edit-check, and finish complete without blocking.
  2. Report classifies each source repository dirty state without mutating it.
  3. Report preserves Phase 0.5 verdict as HUMAN_REQUIRED.
  4. Report identifies which repositories need owner action before submodule pinning.
  5. No external runtime, external test, cleanup, reset, stash, commit, submodule add, or paper workflow is executed.
  6. Targeted checks pass and staged commit contains only this triage package plus hook-managed manifest.
