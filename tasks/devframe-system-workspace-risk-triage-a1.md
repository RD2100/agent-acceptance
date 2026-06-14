# TaskSpec: devframe-system-workspace-risk-triage-a1

task_id: devframe-system-workspace-risk-triage-a1
priority: P1
status: completed
type: governance_triage

description: >
  Record the current post-refresh workspace risks that block safe devframe-system
  activation or broad staging. This task is read-only with respect to registry
  mutations, project-gamma deletions, and external repositories.

gate_0:
  triggered: true
  trigger_reason: "The current worktree contains a registry migration diff and a large project-gamma deletion set after the controlled multi-GPT refresh commit."
  inventory_evidence:
    queried_sources:
      - git status --short
      - git diff -- .agent/PROJECT_REGISTRY.json
      - git diff --stat -- _projects/project-gamma
      - python -m pytest tests/test_validate_project_registry_bindings.py tests/test_router_10_project_stress.py -q
    matched_capabilities:
      - project_registry_validation
      - multi_project_router
      - sadp_task_runner
  rules_checked: [core-004, core-007, core-008, review-001]
  sufficiency_decision: existing_sufficient
  decision: reuse
  delta_justification: "This task creates a factual triage report only; no new runtime capability is introduced."

conflict_registry:
  read_set:
    - .agent/PROJECT_REGISTRY.json
    - _projects/project-gamma/**
    - git status --short
    - git diff --stat -- _projects/project-gamma
    - tests/test_validate_project_registry_bindings.py
    - tests/test_router_10_project_stress.py
  write_set:
    - .ai/current-task.yaml
    - tasks/devframe-system-workspace-risk-triage-a1.md
    - _reports/devframe-system-workspace-risk-triage-a1/**
    - _evidence/devframe-system-workspace-risk-triage-a1/**
    - hooks/sealed-files-manifest.json
    - _evidence/hook-output/**
  governance_adjacent_files_modified:
    - .ai/current-task.yaml
  protected_files_touched: false
  conflict_level: low

acceptance_criteria:
  - "Report records .agent/PROJECT_REGISTRY.json as HUMAN_REQUIRED rather than committed."
  - "Report records _projects/project-gamma deletions as not accepted for staging."
  - "Report confirms D:\\devframe-system exists but is not a git repo and not an activated superproject baseline."
  - "Targeted registry/router validation result is recorded."
  - "No external repository runtime, build, test, cleanup, reset, stash, checkout, or commit is executed."

external_runtime_execution_authorized: false
paper_workflow_status: paused
