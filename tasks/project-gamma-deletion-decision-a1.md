# TaskSpec: project-gamma-deletion-decision-a1

task_id: project-gamma-deletion-decision-a1
priority: P1
status: completed
type: human_required_decision_packet

description: >
  Prepare a Human Required decision packet for the current `_projects/project-gamma`
  tracked deletion set. This task does not restore, stage, or commit those
  deletions.

gate_0:
  triggered: true
  trigger_reason: "The worktree contains 188 tracked deletions under _projects/project-gamma, including governance docs, schemas, rules, and templates."
  inventory_evidence:
    queried_sources:
      - git status --short -- _projects/project-gamma
      - git diff --stat -- _projects/project-gamma
      - git diff --name-status -- _projects/project-gamma
      - docs/agent-runtime/human-required-decision-record.md
      - _reports/devframe-system-workspace-risk-triage-a1/WORKSPACE_RISK_TRIAGE.md
    matched_capabilities:
      - sadp_task_runner
      - human_required_decision_record
      - dirty_baseline_triage
  rules_checked: [core-001, core-005, core-008, review-001]
  sufficiency_decision: existing_sufficient
  decision: reuse
  delta_justification: "This task only creates a decision packet for an existing dirty deletion set; it does not mutate the deletion set."

conflict_registry:
  read_set:
    - _projects/project-gamma/**
    - docs/agent-runtime/human-required-decision-record.md
    - _reports/devframe-system-workspace-risk-triage-a1/WORKSPACE_RISK_TRIAGE.md
  write_set:
    - .ai/current-task.yaml
    - tasks/project-gamma-deletion-decision-a1.md
    - _reports/project-gamma-deletion-decision-a1/**
    - _evidence/project-gamma-deletion-decision-a1/**
    - hooks/sealed-files-manifest.json
    - _evidence/hook-output/**
  governance_adjacent_files_modified:
    - .ai/current-task.yaml
  protected_files_touched: false
  conflict_level: low

acceptance_criteria:
  - "Decision packet records 188 tracked deletions and 14301 deleted lines."
  - "Decision packet offers restore, accept-with-dedicated-review, and defer routes."
  - "Decision packet leaves human_decision and authorization as pending."
  - "No _projects/project-gamma deletion is staged or committed by this task."
  - "No cleanup, reset, stash, checkout, delete, or broad staging is executed."

external_runtime_execution_authorized: false
paper_workflow_status: paused
