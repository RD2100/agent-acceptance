# TaskSpec: DEVFRAME-SYSTEM-PHASE05-FRESHNESS-SNAPSHOT-A1

**ID**: devframe-system-phase05-freshness-snapshot-a1
**Priority**: P1
**Status**: in_progress
**Type**: governance_read_only_freshness_snapshot

## Intent

Create a read-only freshness snapshot of the four source repositories relevant
to future `devframe-system` work. The task may inspect branch, HEAD, remote, and
dirty status, then record the findings inside `D:\agent-acceptance`. It must not
create `D:\devframe-system`, run external runtimes/tests/builds, add
submodules, or mutate external repositories.

gate_0:
  triggered: true
  trigger_reason: "Continue Phase 0.5 by refreshing source repository readiness facts without side effects."
  inventory_evidence:
    queried_sources:
      - "docs/agent-runtime/devframe-system-phase05-index.md"
      - "docs/agent-runtime/devframe-system-phase05-handoff-brief.md"
      - "docs/agent-runtime/devframe-system-route-a-clean-baseline-checklist.md"
      - "docs/agent-runtime/devframe-system-route-b-noop-dry-run.md"
    matched_capabilities:
      - sadp_governance
      - read_only_inventory
      - freshness_snapshot
      - external_runtime_non_execution_gate
  rules_checked: [core-001, core-004, core-005, core-007, core-008, review-001, git-001]
  sufficiency_decision: existing_sufficient
  decision: reuse
  delta_justification: "The task collects read-only git facts and writes governance artifacts only."

conflict_registry:
  read_set:
    - "docs/agent-runtime/devframe-system-phase05-index.md"
    - "docs/agent-runtime/devframe-system-phase05-handoff-brief.md"
    - "D:/agent-acceptance/.git"
    - "D:/dev-frame-opencode/.git"
    - "D:/devframe-control-plane/.git"
    - "D:/test-frame/.git"
    - ".ai/current-task.yaml"
  write_set:
    - tasks/devframe-system-phase05-freshness-snapshot-a1.md
    - .ai/current-task.yaml
    - _reports/devframe-system-phase05-freshness-snapshot-a1/**
    - _evidence/DEVFRAME-SYSTEM-PHASE05-FRESHNESS-SNAPSHOT-A1/**
    - hooks/sealed-files-manifest.json
    - _evidence/hook-output/**
  governance_adjacent_files_modified:
    - ".ai/current-task.yaml"
  protected_files_touched: false
  conflict_level: medium

**Acceptance Gates**:
  1. Runner start, edit-check, and finish complete without blocking.
  2. Snapshot records path, branch, HEAD, remote, and dirty counts for agent-acceptance, dev-frame-opencode, devframe-control-plane, and test-frame.
  3. Snapshot states whether `D:\devframe-system` exists.
  4. Snapshot preserves current verdict as HUMAN_REQUIRED unless all strict Route A requirements are proven clean.
  5. No external runtime/test/build/package install, cleanup/reset/stash/checkout/delete/stage/commit, submodule command, or paper workflow is executed.
  6. Targeted checks pass and staged commit contains only this freshness-snapshot package plus hook-managed manifest.
