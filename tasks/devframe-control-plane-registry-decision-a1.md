# TaskSpec: devframe-control-plane-registry-decision-a1

task_id: devframe-control-plane-registry-decision-a1
priority: P1
status: completed
type: human_required_decision_packet

description: >
  Prepare a Human Required decision packet for the pending
  `devframe-control-plane` project registry migration without committing the
  registry mutation itself.

gate_0:
  triggered: true
  trigger_reason: "Current .agent/PROJECT_REGISTRY.json contains an unstaged devframe-control-plane project entry, which is a Project Registry Migration trigger."
  inventory_evidence:
    queried_sources:
      - .agent/PROJECT_REGISTRY.json
      - docs/agent-runtime/human-required-decision-record.md
      - docs/agent-runtime/inactive-frame-registry.md
      - _reports/devframe-system-workspace-risk-triage-a1/WORKSPACE_RISK_TRIAGE.md
      - python -m pytest tests/test_validate_project_registry_bindings.py tests/test_router_10_project_stress.py -q
    matched_capabilities:
      - project_registry_validation
      - human_required_decision_record
      - inactive_frame_registry
      - sadp_task_runner
  rules_checked: [core-004, core-007, core-008, review-001]
  sufficiency_decision: existing_sufficient
  decision: reuse
  delta_justification: "This task only creates a decision packet; it does not authorize or commit the registry mutation."

conflict_registry:
  read_set:
    - .agent/PROJECT_REGISTRY.json
    - docs/agent-runtime/human-required-decision-record.md
    - docs/agent-runtime/inactive-frame-registry.md
    - _reports/devframe-system-workspace-risk-triage-a1/WORKSPACE_RISK_TRIAGE.md
    - tests/test_validate_project_registry_bindings.py
    - tests/test_router_10_project_stress.py
  write_set:
    - .ai/current-task.yaml
    - tasks/devframe-control-plane-registry-decision-a1.md
    - _reports/devframe-control-plane-registry-decision-a1/**
    - _evidence/devframe-control-plane-registry-decision-a1/**
    - hooks/sealed-files-manifest.json
    - _evidence/hook-output/**
  governance_adjacent_files_modified:
    - .ai/current-task.yaml
  protected_files_touched: false
  conflict_level: low

acceptance_criteria:
  - "Decision packet references Trigger 5: Project Registry Migration."
  - "Decision packet offers genuine approve/defer/reject routes."
  - "Decision packet leaves human_decision and authorization as pending."
  - "No .agent/PROJECT_REGISTRY.json mutation is staged or committed by this task."
  - "Targeted registry/router validation result is recorded as technical evidence only."
  - "No external repository runtime, build, test, cleanup, reset, stash, checkout, or commit is executed."

external_runtime_execution_authorized: false
paper_workflow_status: paused
