# TaskSpec: TEST-FRAME-BOOTSTRAP-OWNER-ACTION-A1

**ID**: test-frame-bootstrap-owner-action-a1
**Priority**: P1
**Status**: in_progress
**Type**: governance_owner_action_report

## Intent

Record the owner action status for the dirty `D:\test-frame` bootstrap package
without committing, unstaging, cleaning, testing, or otherwise mutating the
external repository. During this task, an external actor committed the staged
bootstrap package; this task records that state transition and the remaining
blackboard drift.

gate_0:
  triggered: true
  trigger_reason: "Continue ordered progress by addressing the first dirty-baseline blocker: test-frame staged bootstrap package."
  inventory_evidence:
    queried_sources:
      - "D:/test-frame/AGENTS.md"
      - "D:/test-frame git status"
      - "D:/test-frame git log --oneline -5"
      - "D:/test-frame git show --name-status HEAD"
      - "D:/test-frame git diff --cached --check"
      - "D:/test-frame git diff --check"
      - "_reports/devframe-system-dirty-baseline-triage-a1/TRIAGE_REPORT.md"
    matched_capabilities:
      - sadp_governance
      - external_runtime_non_execution_gate
      - dirty_baseline_triage
      - test_frame_owner_action
  rules_checked: [core-001, core-004, core-005, core-007, core-008, review-001, git-001]
  sufficiency_decision: existing_sufficient
  decision: reuse
  delta_justification: "The task creates a governance owner-action report in agent-acceptance only."

conflict_registry:
  read_set:
    - "D:/test-frame/AGENTS.md"
    - "D:/test-frame git status"
    - "D:/test-frame git log --oneline -5"
    - "D:/test-frame git show --name-status HEAD"
    - "D:/test-frame git diff --cached --check"
    - "D:/test-frame git diff --check"
    - "_reports/devframe-system-dirty-baseline-triage-a1/TRIAGE_REPORT.md"
    - ".ai/current-task.yaml"
  write_set:
    - tasks/test-frame-bootstrap-owner-action-a1.md
    - .ai/current-task.yaml
    - _reports/test-frame-bootstrap-owner-action-a1/**
    - _evidence/TEST-FRAME-BOOTSTRAP-OWNER-ACTION-A1/**
    - hooks/sealed-files-manifest.json
    - _evidence/hook-output/**
  governance_adjacent_files_modified:
    - ".ai/current-task.yaml"
  protected_files_touched: false
  conflict_level: medium

**Acceptance Gates**:
  1. Runner start, edit-check, and finish complete without blocking.
  2. Report states that test-frame Phase 0-5 forbids agent-side git mutations.
  3. Report identifies the externally committed bootstrap package and remaining blackboard drift.
  4. Report gives remaining owner actions without performing them.
  5. No test-frame commit, reset, clean, stash, unstage, runtime, build, or test is executed.
  6. Targeted checks pass and staged commit contains only this governance package plus hook-managed manifest.
