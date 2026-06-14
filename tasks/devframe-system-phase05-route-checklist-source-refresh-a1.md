# TaskSpec: DEVFRAME-SYSTEM-PHASE05-ROUTE-CHECKLIST-SOURCE-REFRESH-A1

**ID**: devframe-system-phase05-route-checklist-source-refresh-a1
**Priority**: P1
**Status**: completed
**Type**: governance_route_checklist_source_refresh

## Intent

Refresh the Route A and Route B no-op checklists so they point future operators
to the latest freshness snapshot for repository facts. The checklists already
forbid physical bootstrap and runtime execution; this task only clarifies the
current evidence source used before any later route activation.

The task must stay inside `D:\agent-acceptance`. It must not create
`D:\devframe-system`, add submodules, run external runtimes/tests/builds/package
installs, run paper workflow, or mutate external repositories.

gate_0:
  triggered: true
  trigger_reason: "Route A/B checklists do not yet name the freshness snapshot as the latest repository-fact source."
  inventory_evidence:
    queried_sources:
      - "docs/agent-runtime/devframe-system-route-a-clean-baseline-checklist.md"
      - "docs/agent-runtime/devframe-system-route-b-noop-dry-run.md"
      - "docs/agent-runtime/devframe-system-route-decision-packet.md"
      - "_reports/devframe-system-phase05-freshness-snapshot-a1/FRESHNESS_SNAPSHOT.md"
    matched_capabilities:
      - sadp_governance
      - route_checklist_refresh
      - documentation_navigation
      - external_runtime_non_execution_gate
  rules_checked: [core-001, core-004, core-005, core-007, core-008, review-001, git-001]
  sufficiency_decision: existing_sufficient
  decision: reuse
  delta_justification: "The task updates governance documentation only and does not require new runtime capability."

conflict_registry:
  read_set:
    - "docs/agent-runtime/devframe-system-route-a-clean-baseline-checklist.md"
    - "docs/agent-runtime/devframe-system-route-b-noop-dry-run.md"
    - "docs/agent-runtime/devframe-system-route-decision-packet.md"
    - "_reports/devframe-system-phase05-freshness-snapshot-a1/FRESHNESS_SNAPSHOT.md"
    - ".ai/current-task.yaml"
  write_set:
    - tasks/devframe-system-phase05-route-checklist-source-refresh-a1.md
    - .ai/current-task.yaml
    - docs/agent-runtime/devframe-system-route-a-clean-baseline-checklist.md
    - docs/agent-runtime/devframe-system-route-b-noop-dry-run.md
    - _reports/devframe-system-phase05-route-checklist-source-refresh-a1/**
    - _evidence/DEVFRAME-SYSTEM-PHASE05-ROUTE-CHECKLIST-SOURCE-REFRESH-A1/**
    - hooks/sealed-files-manifest.json
    - _evidence/hook-output/**
  governance_adjacent_files_modified:
    - ".ai/current-task.yaml"
    - "docs/agent-runtime/devframe-system-route-a-clean-baseline-checklist.md"
    - "docs/agent-runtime/devframe-system-route-b-noop-dry-run.md"
  protected_files_touched: false
  conflict_level: medium

**Acceptance Gates**:
  1. Runner start, edit-check, and finish complete without blocking.
  2. Route A checklist names the freshness snapshot as the latest repository-fact source.
  3. Route B checklist names the freshness snapshot as the latest repository-fact source.
  4. Verdict remains HUMAN_REQUIRED and no physical bootstrap/runtime/submodule/paper workflow action is performed.
  5. Targeted checks pass and staged commit contains only this route-checklist refresh package plus hook-managed manifest.
