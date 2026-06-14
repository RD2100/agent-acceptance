# TaskSpec: DEVFRAME-SYSTEM-PHASE05-ROUTE-APPROVAL-TEMPLATE-A1

**ID**: devframe-system-phase05-route-approval-template-a1
**Priority**: P1
**Status**: completed
**Type**: governance_route_approval_template

## Intent

Create a copy-ready approval record template for future `devframe-system`
Route A or Route B decisions. The template must make it clear that an approval
record is evidence of a human decision, not an approval by itself.

The task must stay inside `D:\agent-acceptance`. It must not create
`D:\devframe-system`, add submodules, run external runtimes/tests/builds/package
installs, run paper workflow, or mutate external repositories.

gate_0:
  triggered: true
  trigger_reason: "The route worksheet requires a human approval record, but no copy-ready approval record template exists."
  inventory_evidence:
    queried_sources:
      - "docs/agent-runtime/devframe-system-route-decision-worksheet.md"
      - "docs/agent-runtime/devframe-system-route-decision-packet.md"
      - "docs/agent-runtime/devframe-system-phase05-index.md"
      - "docs/agent-runtime/devframe-system-phase05-handoff-brief.md"
    matched_capabilities:
      - sadp_governance
      - documentation_navigation
      - route_decision_governance
      - human_approval_recording
      - external_runtime_non_execution_gate
  rules_checked: [core-001, core-004, core-005, core-007, core-008, review-001, git-001]
  sufficiency_decision: existing_sufficient
  decision: reuse
  delta_justification: "The task adds a documentation template only and does not require new runtime capability."

conflict_registry:
  read_set:
    - "docs/agent-runtime/devframe-system-route-decision-worksheet.md"
    - "docs/agent-runtime/devframe-system-route-decision-packet.md"
    - "docs/agent-runtime/devframe-system-phase05-index.md"
    - "docs/agent-runtime/devframe-system-phase05-handoff-brief.md"
    - ".ai/current-task.yaml"
  write_set:
    - tasks/devframe-system-phase05-route-approval-template-a1.md
    - .ai/current-task.yaml
    - docs/agent-runtime/devframe-system-route-approval-record-template.md
    - docs/agent-runtime/devframe-system-route-decision-worksheet.md
    - docs/agent-runtime/devframe-system-phase05-index.md
    - docs/agent-runtime/devframe-system-phase05-handoff-brief.md
    - _reports/devframe-system-phase05-route-approval-template-a1/**
    - _evidence/DEVFRAME-SYSTEM-PHASE05-ROUTE-APPROVAL-TEMPLATE-A1/**
    - hooks/sealed-files-manifest.json
    - _evidence/hook-output/**
  governance_adjacent_files_modified:
    - ".ai/current-task.yaml"
    - "docs/agent-runtime/devframe-system-route-approval-record-template.md"
    - "docs/agent-runtime/devframe-system-route-decision-worksheet.md"
    - "docs/agent-runtime/devframe-system-phase05-index.md"
    - "docs/agent-runtime/devframe-system-phase05-handoff-brief.md"
  protected_files_touched: false
  conflict_level: medium

**Acceptance Gates**:
  1. Runner start, edit-check, and finish complete without blocking.
  2. Approval template includes exact route name, allowed scope, superproject creation authorization, submodule status, runtime gate status, and `test-frame` evidence-only confirmation.
  3. Approval template states it is not valid until filled by a human decision.
  4. Index, handoff brief, and worksheet reference the approval template.
  5. No physical bootstrap/runtime/submodule/paper workflow action is performed.
  6. Targeted checks pass and staged commit contains only this template package plus hook-managed manifest.
