# TaskSpec: devframe-control-plane-registry-migration-a1

**ID**: devframe-control-plane-registry-migration-a1
**Priority**: P1
**Status**: completed
**Type**: project_registry_migration

## Intent

Commit the already-reviewed `devframe-control-plane` pending binding entry in
`.agent/PROJECT_REGISTRY.json` after explicit human authorization. This task
must not run external runtimes, mutate external repositories, commit unrelated
dirty files, or activate `devframe-system` physical bootstrap.

gate_0:
  triggered: true
  trigger_reason: "Project registry migration for devframe-control-plane requires explicit human authorization before commit."
  inventory_evidence:
    queried_sources:
      - "_reports/devframe-control-plane-registry-decision-a1/DECISION_PACKET.md"
      - "_reports/devframe-control-plane-merge-readiness-a1/MERGE_READINESS_REPORT.md"
      - ".agent/PROJECT_REGISTRY.json diff"
      - "tests/test_validate_project_registry_bindings.py"
      - "tests/test_router_10_project_stress.py"
    matched_capabilities:
      - sadp_governance
      - project_registry_migration
      - registry_binding_validation
      - external_runtime_non_execution_gate
  rules_checked: [core-001, core-004, core-005, core-007, core-008, review-001, git-001]
  lessons_checked:
    - "Do not self-authorize project registry migrations."
    - "Keep registry migration separate from physical bootstrap."
    - "Do not stage unrelated dirty worktree changes."
  sufficiency_decision: existing_sufficient
  decision: reuse
  delta_justification: "The pending registry shape already exists and targeted tests previously passed; this task records authorization and commits the scoped diff."

authorization:
  decision_id: DECISION-20260614-DEVFRAME-CONTROL-PLANE-REGISTRY-A1
  selected_option: "Approve registry migration"
  human_authorization_text: "授权！"
  authorized_at_local: "2026-06-14"
  scope:
    - "Commit the devframe-control-plane pending_binding entry in .agent/PROJECT_REGISTRY.json."
    - "Do not run external runtimes."
    - "Do not mutate dev-frame-opencode, test-frame, devframe-control-plane, or devframe-system."

conflict_registry:
  read_set:
    - "_reports/devframe-control-plane-registry-decision-a1/DECISION_PACKET.md"
    - "_reports/devframe-control-plane-merge-readiness-a1/MERGE_READINESS_REPORT.md"
    - ".agent/PROJECT_REGISTRY.json"
    - "tests/test_validate_project_registry_bindings.py"
    - "tests/test_router_10_project_stress.py"
    - "scripts/qoderwork_task_runner.py"
    - "scripts/sadp_pre_task_enforcer.py"
  write_set:
    - .ai/current-task.yaml
    - .agent/PROJECT_REGISTRY.json
    - tasks/devframe-control-plane-registry-migration-a1.md
    - _reports/devframe-control-plane-registry-migration-a1/**
    - _evidence/devframe-control-plane-registry-migration-a1/**
    - _reports/devframe-control-plane-registry-decision-a1/DECISION_PACKET.md
    - hooks/sealed-files-manifest.json
  governance_adjacent_files_modified:
    - ".ai/current-task.yaml"
    - ".agent/PROJECT_REGISTRY.json"
    - "_reports/devframe-control-plane-registry-decision-a1/DECISION_PACKET.md"
    - "hooks/sealed-files-manifest.json"
  protected_files_touched: true
  protected_file_justification: ".agent/PROJECT_REGISTRY.json is intentionally migrated after human authorization; sealed manifest may be pre-commit regenerated."
  conflict_level: medium

**Acceptance Gates**:
  1. Registry diff only adds `devframe-control-plane` pending binding and updates `total_projects`/`updated_at`.
  2. Decision packet records the human-approved option.
  3. `devframe-system` remains `NOT_MERGED`.
  4. No external runtime or external repository mutation occurs.
  5. Targeted registry/router tests pass.
  6. Runner start/edit-check/finish and pre-commit governance pass.
