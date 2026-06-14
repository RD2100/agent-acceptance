# TaskSpec: DEVFRAME-SYSTEM-PHASE05-ROUTE-APPROVAL-SCHEMA-A1

**ID**: devframe-system-phase05-route-approval-schema-a1
**Priority**: P1
**Status**: completed
**Type**: governance_route_approval_schema

## Intent

Extend the inactive `devframe-system` draft contract packet with a
`HumanRouteApprovalRecord` definition that matches the route approval record
template. This makes future Route A or Route B approval evidence structurally
checkable without activating any validator or runtime.

The task must stay inside `D:\agent-acceptance`. It must not create
`D:\devframe-system`, add submodules, run external runtimes/tests/builds/package
installs, run paper workflow, or mutate external repositories.

gate_0:
  triggered: true
  trigger_reason: "Approval record template exists, but no inactive draft schema defines its required structure."
  inventory_evidence:
    queried_sources:
      - "schemas/draft/devframe-system-contracts.schema.draft.json"
      - "docs/agent-runtime/devframe-system-route-approval-record-template.md"
      - "docs/agent-runtime/devframe-system-phase05-index.md"
      - "docs/agent-runtime/devframe-system-phase05-handoff-brief.md"
    matched_capabilities:
      - sadp_governance
      - documentation_navigation
      - route_decision_governance
      - human_approval_recording
      - draft_contract_schema
      - external_runtime_non_execution_gate
  rules_checked: [core-001, core-004, core-005, core-007, core-008, review-001, git-001]
  sufficiency_decision: existing_sufficient
  decision: reuse
  delta_justification: "The task extends inactive draft schema only and does not wire schema into active validators."

conflict_registry:
  read_set:
    - "schemas/draft/devframe-system-contracts.schema.draft.json"
    - "docs/agent-runtime/devframe-system-route-approval-record-template.md"
    - "docs/agent-runtime/devframe-system-phase05-index.md"
    - "docs/agent-runtime/devframe-system-phase05-handoff-brief.md"
    - ".ai/current-task.yaml"
  write_set:
    - tasks/devframe-system-phase05-route-approval-schema-a1.md
    - .ai/current-task.yaml
    - schemas/draft/devframe-system-contracts.schema.draft.json
    - docs/agent-runtime/devframe-system-route-approval-record-template.md
    - docs/agent-runtime/devframe-system-phase05-index.md
    - docs/agent-runtime/devframe-system-phase05-handoff-brief.md
    - _reports/devframe-system-phase05-route-approval-schema-a1/**
    - _evidence/DEVFRAME-SYSTEM-PHASE05-ROUTE-APPROVAL-SCHEMA-A1/**
    - hooks/sealed-files-manifest.json
    - _evidence/hook-output/**
  governance_adjacent_files_modified:
    - ".ai/current-task.yaml"
    - "schemas/draft/devframe-system-contracts.schema.draft.json"
    - "docs/agent-runtime/devframe-system-route-approval-record-template.md"
    - "docs/agent-runtime/devframe-system-phase05-index.md"
    - "docs/agent-runtime/devframe-system-phase05-handoff-brief.md"
  protected_files_touched: false
  conflict_level: medium

**Acceptance Gates**:
  1. Runner start, edit-check, and finish complete without blocking.
  2. Draft schema contains `HumanRouteApprovalRecord` and includes it in top-level `oneOf`.
  3. Draft schema remains explicitly inactive and does not authorize runtime, submodules, or GateResult authority.
  4. Approval template, index, and handoff brief reference the draft schema.
  5. No physical bootstrap/runtime/submodule/paper workflow action is performed.
  6. Targeted checks pass and staged commit contains only this schema package plus hook-managed manifest.
