# TaskSpec: DEVFRAME-SYSTEM-PHASE05-NAVIGATION-REFRESH-A1

**ID**: devframe-system-phase05-navigation-refresh-a1
**Priority**: P1
**Status**: completed
**Type**: governance_navigation_refresh

## Intent

Refresh the Phase 0.5 navigation and handoff documents after the freshness
snapshot completed. This task keeps all work inside `D:\agent-acceptance`,
records that the latest freshness snapshot is now part of the canonical reading
order, and removes stale language that still names the snapshot as the next
pending action.

The task must not create `D:\devframe-system`, add submodules, run external
runtimes/tests/builds/package installs, run paper workflow, or mutate external
repositories.

gate_0:
  triggered: true
  trigger_reason: "The latest freshness snapshot is complete, but Phase 0.5 navigation still points to it as a future next step."
  inventory_evidence:
    queried_sources:
      - "docs/agent-runtime/devframe-system-phase05-index.md"
      - "docs/agent-runtime/devframe-system-phase05-handoff-brief.md"
      - "_reports/devframe-system-phase05-freshness-snapshot-a1/FRESHNESS_SNAPSHOT.md"
      - "tasks/devframe-system-phase05-freshness-snapshot-a1.md"
    matched_capabilities:
      - sadp_governance
      - documentation_navigation
      - handoff_refresh
      - external_runtime_non_execution_gate
  rules_checked: [core-001, core-004, core-005, core-007, core-008, review-001, git-001]
  sufficiency_decision: existing_sufficient
  decision: reuse
  delta_justification: "The task updates governance navigation only and does not require new runtime capability."

conflict_registry:
  read_set:
    - "docs/agent-runtime/devframe-system-phase05-index.md"
    - "docs/agent-runtime/devframe-system-phase05-handoff-brief.md"
    - "_reports/devframe-system-phase05-freshness-snapshot-a1/FRESHNESS_SNAPSHOT.md"
    - "tasks/devframe-system-phase05-freshness-snapshot-a1.md"
    - ".ai/current-task.yaml"
  write_set:
    - tasks/devframe-system-phase05-navigation-refresh-a1.md
    - tasks/devframe-system-phase05-freshness-snapshot-a1.md
    - .ai/current-task.yaml
    - docs/agent-runtime/devframe-system-phase05-index.md
    - docs/agent-runtime/devframe-system-phase05-handoff-brief.md
    - _reports/devframe-system-phase05-navigation-refresh-a1/**
    - _evidence/DEVFRAME-SYSTEM-PHASE05-NAVIGATION-REFRESH-A1/**
    - hooks/sealed-files-manifest.json
    - _evidence/hook-output/**
  governance_adjacent_files_modified:
    - ".ai/current-task.yaml"
    - "docs/agent-runtime/devframe-system-phase05-index.md"
    - "docs/agent-runtime/devframe-system-phase05-handoff-brief.md"
  protected_files_touched: false
  conflict_level: medium

**Acceptance Gates**:
  1. Runner start, edit-check, and finish complete without blocking.
  2. Phase 0.5 index includes the completed freshness snapshot in reading order.
  3. Handoff brief no longer lists freshness snapshot capture as the next pending no-op step.
  4. Previous freshness snapshot TaskSpec is closed as completed.
  5. Verdict remains HUMAN_REQUIRED and no physical bootstrap/runtime/submodule/paper workflow action is performed.
  6. Targeted checks pass and staged commit contains only this navigation-refresh package plus hook-managed manifest.
