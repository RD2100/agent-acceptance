# TaskSpec: DEVFRAME-SYSTEM-PHASE05-ROUTE-DECISION-WORKSHEET-A1

**ID**: devframe-system-phase05-route-decision-worksheet-a1
**Priority**: P1
**Status**: completed
**Type**: governance_route_decision_worksheet

## Intent

Create a compact human decision worksheet for choosing the next
`devframe-system` Phase 0.5 route. The worksheet must make the three valid
choices explicit: continue contract-only planning, choose Route A after clean
baseline proof, or choose Route B dirty-aware skeleton by explicit approval.

The task must stay inside `D:\agent-acceptance`. It must not create
`D:\devframe-system`, add submodules, run external runtimes/tests/builds/package
installs, run paper workflow, or mutate external repositories.

gate_0:
  triggered: true
  trigger_reason: "Route decision packet exists, but there is no compact one-page worksheet for human route selection."
  inventory_evidence:
    queried_sources:
      - "docs/agent-runtime/devframe-system-phase05-index.md"
      - "docs/agent-runtime/devframe-system-phase05-handoff-brief.md"
      - "docs/agent-runtime/devframe-system-route-decision-packet.md"
      - "_reports/devframe-system-phase05-freshness-snapshot-a1/FRESHNESS_SNAPSHOT.md"
    matched_capabilities:
      - sadp_governance
      - documentation_navigation
      - route_decision_governance
      - external_runtime_non_execution_gate
  rules_checked: [core-001, core-004, core-005, core-007, core-008, review-001, git-001]
  sufficiency_decision: existing_sufficient
  decision: reuse
  delta_justification: "The task adds a decision worksheet only and does not require new runtime capability."

conflict_registry:
  read_set:
    - "docs/agent-runtime/devframe-system-phase05-index.md"
    - "docs/agent-runtime/devframe-system-phase05-handoff-brief.md"
    - "docs/agent-runtime/devframe-system-route-decision-packet.md"
    - "_reports/devframe-system-phase05-freshness-snapshot-a1/FRESHNESS_SNAPSHOT.md"
    - ".ai/current-task.yaml"
  write_set:
    - tasks/devframe-system-phase05-route-decision-worksheet-a1.md
    - .ai/current-task.yaml
    - docs/agent-runtime/devframe-system-phase05-index.md
    - docs/agent-runtime/devframe-system-phase05-handoff-brief.md
    - docs/agent-runtime/devframe-system-route-decision-worksheet.md
    - _reports/devframe-system-phase05-route-decision-worksheet-a1/**
    - _evidence/DEVFRAME-SYSTEM-PHASE05-ROUTE-DECISION-WORKSHEET-A1/**
    - hooks/sealed-files-manifest.json
    - _evidence/hook-output/**
  governance_adjacent_files_modified:
    - ".ai/current-task.yaml"
    - "docs/agent-runtime/devframe-system-phase05-index.md"
    - "docs/agent-runtime/devframe-system-phase05-handoff-brief.md"
    - "docs/agent-runtime/devframe-system-route-decision-worksheet.md"
  protected_files_touched: false
  conflict_level: medium

**Acceptance Gates**:
  1. Runner start, edit-check, and finish complete without blocking.
  2. Decision worksheet states `HUMAN_REQUIRED` as the default when no route is selected.
  3. Decision worksheet states `test-frame` is a controlled verification runtime candidate, not a plugin.
  4. Index and handoff brief reference the worksheet.
  5. No physical bootstrap/runtime/submodule/paper workflow action is performed.
  6. Targeted checks pass and staged commit contains only this worksheet package plus hook-managed manifest.
