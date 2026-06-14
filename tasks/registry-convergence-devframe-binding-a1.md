# TaskSpec: REGISTRY-CONVERGENCE-DEVFRAME-BINDING-A1

task_id: REGISTRY-CONVERGENCE-DEVFRAME-BINDING-A1
priority: P1
status: in_progress
type: governance_commit_closure

description: >
  Commit the precise registry convergence, devframe-system control binding,
  and active-scope registry validator package without staging unrelated dirty
  workspace changes.

gate_0:
  triggered: true
  trigger_reason: "User authorized committing the precise registry/binding/validator package."
  inventory_evidence:
    queried_sources:
      - ".agent/PROJECT_REGISTRY.json"
      - "_projects/devframe-system/.agent/CONVERSATION_BINDING.json"
      - "scripts/validate_project_registry_bindings.py"
      - "tests/test_validate_project_registry_bindings.py"
      - "tests/test_router_10_project_stress.py"
    matched_capabilities:
      - conversation_registry
      - bind_chrome_conversation
      - project_registry_validation
      - shared_cdp_transport
  rules_checked: [core-004, core-007, core-008, review-001, git-001]
  sufficiency_decision: existing_sufficient
  decision: reuse
  delta_justification: "This is a commit closure task for already verified governance changes."

conflict_registry:
  read_set:
    - ".agent/PROJECT_REGISTRY.json"
    - "_projects/devframe-system/.agent/CONVERSATION_BINDING.json"
    - "scripts/validate_project_registry_bindings.py"
    - "tests/test_validate_project_registry_bindings.py"
    - "tests/test_router_10_project_stress.py"
    - "git status --short"
  write_set:
    - tasks/registry-convergence-devframe-binding-a1.md
    - tasks/devframe-system-master-binding-a1.md
    - tasks/project-registry-validator-active-scope-a1.md
    - .ai/current-task.yaml
    - .agent/PROJECT_REGISTRY.json
    - _projects/devframe-system/.agent/CONVERSATION_BINDING.json
    - _projects/devframe-system/.agent/CONVERSATION_REGISTRY.schema.json
    - scripts/validate_project_registry_bindings.py
    - tests/test_validate_project_registry_bindings.py
    - tests/test_router_10_project_stress.py
    - _evidence/DEVFRAME-SYSTEM-MASTER-BINDING-A1/**
    - _evidence/PROJECT-REGISTRY-VALIDATOR-ACTIVE-SCOPE-A1/**
    - _evidence/REGISTRY-CONVERGENCE-DEVFRAME-BINDING-A1/**
    - hooks/sealed-files-manifest.json
    - _evidence/hook-output/**
  governance_adjacent_files_modified:
    - .agent/PROJECT_REGISTRY.json
  protected_files_touched: false
  conflict_level: medium

**Acceptance Gates**:
  1. Only the authorized precision package is staged.
  2. Registry validation returns 8/8 rules passed.
  3. devframe-system binding validates with schema_validated=true.
  4. Targeted tests pass.
  5. Commit hook passes or any block is reported without broad staging.
  6. No external runtime, test-frame runtime, or paper workflow is executed.
