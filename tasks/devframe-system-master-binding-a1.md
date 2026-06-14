# TaskSpec: DEVFRAME-SYSTEM-MASTER-BINDING-A1

task_id: DEVFRAME-SYSTEM-MASTER-BINDING-A1
priority: P1
status: completed
type: governance_binding

description: >
  Register a future devframe-system superproject control conversation without
  enabling external runtime execution or changing existing active agent bindings.

gate_0:
  triggered: true
  trigger_reason: "User provided an already-open ChatGPT conversation URL for future devframe-system superproject control."
  inventory_evidence:
    queried_sources:
      - ".agent/PROJECT_REGISTRY.json"
      - ".agent/CONVERSATION_BINDING.json"
      - "CDP http://localhost:9222/json/list"
    matched_capabilities:
      - bind_chrome_conversation
      - shared_cdp_transport
      - conversation_registry
  rules_checked: [core-004, core-007, core-008, review-001]
  sufficiency_decision: existing_sufficient
  decision: reuse
  delta_justification: "Only a future superproject control binding is added; no runtime is executed."

conflict_registry:
  read_set:
    - ".agent/PROJECT_REGISTRY.json"
    - ".agent/CONVERSATION_BINDING.json"
  write_set:
    - tasks/devframe-system-master-binding-a1.md
    - .ai/current-task.yaml
    - .agent/PROJECT_REGISTRY.json
    - _projects/devframe-system/.agent/CONVERSATION_BINDING.json
    - _projects/devframe-system/.agent/CONVERSATION_REGISTRY.schema.json
    - _evidence/DEVFRAME-SYSTEM-MASTER-BINDING-A1/**
  protected_files_touched: false
  conflict_level: low

**Acceptance Gates**:
  1. The provided conversation URL is visible through shared CDP.
  2. The devframe-system project is registered without overwriting existing active bindings.
  3. The devframe-system binding uses a real conversation_id and role=orchestrator.
  4. External runtime execution remains not authorized.
  5. Conversation binding validation passes for the new binding.
  6. The new devframe-system conversation is unique; any global duplicate report is documented as a pre-existing unrelated issue.
