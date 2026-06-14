# TaskSpec: DEVFRAME-SYSTEM-PHASE05-READINESS-ROLLUP-A1

**ID**: devframe-system-phase05-readiness-rollup-a1
**Priority**: P1
**Status**: in_progress
**Type**: governance_readiness_rollup

## Intent

Consolidate the current Phase 0.5 readiness state after strict gate, dirty
baseline triage, and repository-specific owner-action reports. This task must
not create `D:\devframe-system`, add submodules, run external runtimes, or
mutate external repositories.

gate_0:
  triggered: true
  trigger_reason: "Consolidate current devframe-system Phase 0.5 readiness after four repository triage slices."
  inventory_evidence:
    queried_sources:
      - "D:/agent-acceptance git status"
      - "D:/test-frame git status"
      - "D:/devframe-control-plane git status"
      - "D:/dev-frame-opencode git status"
      - "_reports/devframe-system-phase05-strict-gate-a1/PREFLIGHT_REPORT.md"
      - "_reports/devframe-system-dirty-baseline-triage-a1/TRIAGE_REPORT.md"
      - "_reports/test-frame-bootstrap-owner-action-a1/OWNER_ACTION_REPORT.md"
      - "_reports/control-plane-artifact-policy-owner-action-a1/OWNER_ACTION_REPORT.md"
      - "_reports/opencode-dirty-split-owner-action-a1/OWNER_ACTION_REPORT.md"
    matched_capabilities:
      - sadp_governance
      - superproject_preflight
      - dirty_baseline_triage
      - external_runtime_non_execution_gate
  rules_checked: [core-001, core-004, core-005, core-007, core-008, review-001, git-001]
  sufficiency_decision: existing_sufficient
  decision: reuse
  delta_justification: "The task creates a governance readiness rollup in agent-acceptance only."

conflict_registry:
  read_set:
    - "D:/agent-acceptance git status"
    - "D:/test-frame git status"
    - "D:/devframe-control-plane git status"
    - "D:/dev-frame-opencode git status"
    - "_reports/devframe-system-phase05-strict-gate-a1/PREFLIGHT_REPORT.md"
    - "_reports/devframe-system-dirty-baseline-triage-a1/TRIAGE_REPORT.md"
    - "_reports/test-frame-bootstrap-owner-action-a1/OWNER_ACTION_REPORT.md"
    - "_reports/control-plane-artifact-policy-owner-action-a1/OWNER_ACTION_REPORT.md"
    - "_reports/opencode-dirty-split-owner-action-a1/OWNER_ACTION_REPORT.md"
    - ".ai/current-task.yaml"
  write_set:
    - tasks/devframe-system-phase05-readiness-rollup-a1.md
    - .ai/current-task.yaml
    - _reports/devframe-system-phase05-readiness-rollup-a1/**
    - _evidence/DEVFRAME-SYSTEM-PHASE05-READINESS-ROLLUP-A1/**
    - hooks/sealed-files-manifest.json
    - _evidence/hook-output/**
  governance_adjacent_files_modified:
    - ".ai/current-task.yaml"
  protected_files_touched: false
  conflict_level: medium

**Acceptance Gates**:
  1. Runner start, edit-check, and finish complete without blocking.
  2. Rollup states physical `D:\devframe-system` bootstrap remains blocked.
  3. Rollup distinguishes current state from older snapshot reports where state drift occurred.
  4. Rollup lists prioritized owner actions for all remaining blockers.
  5. No external repo mutation, external runtime, external test, submodule command, or paper workflow is executed.
  6. Targeted checks pass and staged commit contains only this rollup package plus hook-managed manifest.
