# TaskSpec: devframe-system-decision-index-refresh-a1

task_id: devframe-system-decision-index-refresh-a1
priority: P1
status: closed
closeout_reason: "superseded_by_agent_acceptance_runtime_artifact_ignore_a1; decision navigation state changed before this untracked task was activated"
type: governance_navigation_refresh

description: >
  Refresh the devframe-system Phase 0.5 index and handoff brief so the two new
  Human Required decision packets are visible to future agents.

gate_0:
  triggered: true
  trigger_reason: "Two Human Required decision packets were added after the current devframe-system index and handoff brief were last refreshed."
  inventory_evidence:
    queried_sources:
      - _reports/devframe-control-plane-registry-decision-a1/DECISION_PACKET.md
      - _reports/project-gamma-deletion-decision-a1/DECISION_PACKET.md
      - docs/agent-runtime/devframe-system-phase05-index.md
      - docs/agent-runtime/devframe-system-phase05-handoff-brief.md
    matched_capabilities:
      - sadp_task_runner
      - human_required_decision_record
      - governance_navigation
  rules_checked: [core-004, core-007, core-008, review-001]
  sufficiency_decision: existing_sufficient
  decision: reuse
  delta_justification: "This task updates navigation only; it does not decide or execute the pending actions."

conflict_registry:
  read_set:
    - _reports/devframe-control-plane-registry-decision-a1/DECISION_PACKET.md
    - _reports/project-gamma-deletion-decision-a1/DECISION_PACKET.md
    - docs/agent-runtime/devframe-system-phase05-index.md
    - docs/agent-runtime/devframe-system-phase05-handoff-brief.md
  write_set:
    - .ai/current-task.yaml
    - tasks/devframe-system-decision-index-refresh-a1.md
    - docs/agent-runtime/devframe-system-phase05-index.md
    - docs/agent-runtime/devframe-system-phase05-handoff-brief.md
    - _reports/devframe-system-decision-index-refresh-a1/**
    - _evidence/devframe-system-decision-index-refresh-a1/**
    - hooks/sealed-files-manifest.json
    - _evidence/hook-output/**
  governance_adjacent_files_modified:
    - .ai/current-task.yaml
    - docs/agent-runtime/devframe-system-phase05-index.md
    - docs/agent-runtime/devframe-system-phase05-handoff-brief.md
  protected_files_touched: false
  conflict_level: low

acceptance_criteria:
  - "Index links both Human Required decision packets."
  - "Handoff brief links both Human Required decision packets."
  - "Docs preserve HUMAN_REQUIRED and do not approve registry migration or project-gamma deletion."
  - "No .agent/PROJECT_REGISTRY.json or _projects/project-gamma change is staged."
  - "No external runtime, build, test, cleanup, reset, stash, checkout, delete, or broad staging is executed."

external_runtime_execution_authorized: false
paper_workflow_status: paused
