# TaskSpec: OPENCODE-DIRTY-SPLIT-OWNER-ACTION-A1

**ID**: opencode-dirty-split-owner-action-a1
**Priority**: P1
**Status**: in_progress
**Type**: governance_owner_action_report

## Intent

Classify the dirty `D:\dev-frame-opencode` baseline into source/config changes,
generated state, and evidence/artifact noise without cleaning, resetting,
committing, testing, or executing the external repository.

gate_0:
  triggered: true
  trigger_reason: "Continue ordered progress by addressing the largest dirty-baseline blocker: dev-frame-opencode."
  inventory_evidence:
    queried_sources:
      - "D:/dev-frame-opencode/AGENTS.md"
      - "D:/dev-frame-opencode git status"
      - "D:/dev-frame-opencode git diff --name-status"
      - "D:/dev-frame-opencode git diff --numstat"
      - "D:/dev-frame-opencode git diff --check"
      - "D:/dev-frame-opencode .gitignore"
      - "_reports/devframe-system-dirty-baseline-triage-a1/TRIAGE_REPORT.md"
    matched_capabilities:
      - sadp_governance
      - external_runtime_non_execution_gate
      - dirty_baseline_triage
      - opencode_owner_action
  rules_checked: [core-001, core-004, core-005, core-007, core-008, review-001, git-001]
  sufficiency_decision: existing_sufficient
  decision: reuse
  delta_justification: "The task creates a governance owner-action report in agent-acceptance only."

conflict_registry:
  read_set:
    - "D:/dev-frame-opencode/AGENTS.md"
    - "D:/dev-frame-opencode git status"
    - "D:/dev-frame-opencode git diff --name-status"
    - "D:/dev-frame-opencode git diff --numstat"
    - "D:/dev-frame-opencode git diff --check"
    - "D:/dev-frame-opencode .gitignore"
    - "_reports/devframe-system-dirty-baseline-triage-a1/TRIAGE_REPORT.md"
    - ".ai/current-task.yaml"
  write_set:
    - tasks/opencode-dirty-split-owner-action-a1.md
    - .ai/current-task.yaml
    - _reports/opencode-dirty-split-owner-action-a1/**
    - _evidence/OPENCODE-DIRTY-SPLIT-OWNER-ACTION-A1/**
    - hooks/sealed-files-manifest.json
    - _evidence/hook-output/**
  governance_adjacent_files_modified:
    - ".ai/current-task.yaml"
  protected_files_touched: false
  conflict_level: medium

**Acceptance Gates**:
  1. Runner start, edit-check, and finish complete without blocking.
  2. Report separates source/config changes from generated state and evidence/artifact noise.
  3. Report identifies the large `cli.py` and `tasks.yaml` deltas as hard blockers for submodule pinning.
  4. Report gives owner actions without performing them.
  5. No opencode commit, reset, clean, stash, runtime, build, or test is executed.
  6. Targeted checks pass and staged commit contains only this governance package plus hook-managed manifest.
