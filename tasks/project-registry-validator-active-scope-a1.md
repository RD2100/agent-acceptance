# TaskSpec: PROJECT-REGISTRY-VALIDATOR-ACTIVE-SCOPE-A1

task_id: PROJECT-REGISTRY-VALIDATOR-ACTIVE-SCOPE-A1
priority: P1
status: completed
type: governance_validator_fix

description: >
  Scope project registry duplicate conversation validation to dispatch-active
  projects and active bindings, so suspended historical bindings remain
  auditable without blocking current readiness.

gate_0:
  triggered: true
  trigger_reason: "Registry validator currently flags a suspended project conversation as an active duplicate."
  inventory_evidence:
    queried_sources:
      - ".agent/PROJECT_REGISTRY.json"
      - "_projects/dev-frame-writing/.agent/CONVERSATION_BINDING.json"
      - "D:/dev-frame-opencode/.agent/CONVERSATION_BINDING.json"
      - "scripts/validate_project_registry_bindings.py"
    matched_capabilities:
      - conversation_registry
      - project_registry_validation
  rules_checked: [core-004, core-007, core-008, review-001]
  sufficiency_decision: existing_sufficient
  decision: reuse
  delta_justification: "The fix changes validator classification only; no runtime is executed."

conflict_registry:
  read_set:
    - ".agent/PROJECT_REGISTRY.json"
    - "_projects/dev-frame-writing/.agent/CONVERSATION_BINDING.json"
    - "D:/dev-frame-opencode/.agent/CONVERSATION_BINDING.json"
    - "scripts/validate_project_registry_bindings.py"
  write_set:
    - tasks/project-registry-validator-active-scope-a1.md
    - tasks/registry-convergence-devframe-binding-a1.md
    - .ai/current-task.yaml
    - scripts/validate_project_registry_bindings.py
    - tests/test_validate_project_registry_bindings.py
    - tests/test_router_10_project_stress.py
    - _evidence/PROJECT-REGISTRY-VALIDATOR-ACTIVE-SCOPE-A1/**
  protected_files_touched: false
  conflict_level: low

**Acceptance Gates**:
  1. Suspended registry projects do not count toward duplicate active conversation validation.
  2. Non-active bindings do not count toward duplicate active conversation validation.
  3. Duplicate active conversations among active projects still fail.
  4. The real registry validation reaches all 8 rules passed.
  5. No external runtime or paper workflow is executed.
