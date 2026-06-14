# TaskSpec: DEVFRAME-SYSTEM-PHASE05-STRICT-GATE-A1

**ID**: devframe-system-phase05-strict-gate-a1
**Priority**: P1
**Status**: in_progress
**Type**: governance_preflight_closure

## Intent

Record the Phase 0.5 strict gate decision for the future `devframe-system`
superproject without creating `D:\devframe-system`, adding submodules, running
external runtimes, or modifying source repositories outside `D:\agent-acceptance`.

gate_0:
  triggered: true
  trigger_reason: "User requested implementation of the Phase 0.5 strict gate plan."
  inventory_evidence:
    queried_sources:
      - "D:/agent-acceptance git status"
      - "D:/dev-frame-opencode git status"
      - "D:/devframe-control-plane git status"
      - "D:/test-frame git status"
      - "D:/devframe-system path existence"
    matched_capabilities:
      - project_registry_validation
      - sadp_governance
      - superproject_preflight
      - external_runtime_non_execution_gate
  rules_checked: [core-004, core-005, core-007, core-008, review-001, git-001]
  sufficiency_decision: existing_sufficient
  decision: reuse
  delta_justification: "This task documents a strict HUMAN_REQUIRED gate and does not require new runtime capability."

conflict_registry:
  read_set:
    - "D:/agent-acceptance git status"
    - "D:/dev-frame-opencode git status"
    - "D:/devframe-control-plane git status"
    - "D:/test-frame git status"
    - "D:/devframe-system path existence"
    - ".ai/current-task.yaml"
  write_set:
    - tasks/devframe-system-phase05-strict-gate-a1.md
    - .ai/current-task.yaml
    - _reports/devframe-system-phase05-strict-gate-a1/**
    - _evidence/DEVFRAME-SYSTEM-PHASE05-STRICT-GATE-A1/**
    - hooks/sealed-files-manifest.json
    - _evidence/hook-output/**
  governance_adjacent_files_modified:
    - ".ai/current-task.yaml"
  protected_files_touched: false
  conflict_level: medium

**Acceptance Gates**:
  1. Runner start, edit-check, and finish complete without blocking.
  2. Preflight report verdict is HUMAN_REQUIRED, not READY.
  3. Report states `test-frame` is a controlled verification runtime candidate, not a plugin.
  4. No `D:\devframe-system` directory is created.
  5. No external source repository is modified.
  6. No external runtime, submodule add, cleanup/reset/stash, or paper workflow is executed.
  7. Targeted registry/router tests and git diff check pass.
