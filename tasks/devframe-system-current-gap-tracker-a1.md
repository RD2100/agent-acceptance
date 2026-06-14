# TaskSpec: DEVFRAME-SYSTEM-CURRENT-GAP-TRACKER-A1

**ID**: devframe-system-current-gap-tracker-a1
**Priority**: P1
**Status**: accepted_with_limitation
**Type**: governance_current_gap_tracker

## Intent

Record the current devframe-system readiness state while other agents are
modifying source repositories. The task must update the Phase 0.5 entrypoint so
`D:\devframe-system` being present is not misread as a completed merge, and
must produce a concise gap tracker for what remains before a trusted Route A
baseline or controlled Route B skeleton can proceed.

gate_0:
  triggered: true
  trigger_reason: "The user confirmed D:\\devframe-system now exists while source repositories remain under active modification."
  inventory_evidence:
    queried_sources:
      - "docs/agent-runtime/devframe-system-phase05-index.md"
      - "docs/agent-runtime/devframe-system-phase05-handoff-brief.md"
      - "git status --porcelain for the four source repositories"
      - "Test-Path D:\\devframe-system"
    matched_capabilities:
      - sadp_governance
      - documentation_navigation
      - route_decision_governance
      - human_approval_recording
      - external_runtime_non_execution_gate
  rules_checked: [core-001, core-004, core-005, core-007, core-008, review-001, git-001]
  sufficiency_decision: existing_sufficient
  decision: reuse
  delta_justification: "This is a documentation and readiness tracking update only; it does not activate runtime, submodules, or external tests."

conflict_registry:
  read_set:
    - "docs/agent-runtime/devframe-system-phase05-index.md"
    - "docs/agent-runtime/devframe-system-phase05-handoff-brief.md"
    - ".ai/current-task.yaml"
    - "current read-only git status of D:\\agent-acceptance"
    - "current read-only git status of D:\\devframe-control-plane"
    - "current read-only git status of D:\\dev-frame-opencode"
    - "current read-only git status of D:\\test-frame"
  write_set:
    - tasks/devframe-system-current-gap-tracker-a1.md
    - .ai/current-task.yaml
    - docs/agent-runtime/devframe-system-phase05-index.md
    - docs/agent-runtime/devframe-system-phase05-handoff-brief.md
    - _reports/devframe-system-current-gap-tracker-a1/**
    - _evidence/DEVFRAME-SYSTEM-CURRENT-GAP-TRACKER-A1/**
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
  2. Phase 0.5 index states that `D:\devframe-system` exists but is not an activated or trusted baseline.
  3. Handoff brief no longer instructs future agents that `D:\devframe-system` is absent.
  4. Gap tracker lists the remaining work before Route A baseline or Route B dirty-aware skeleton.
  5. Report preserves `test-frame` as controlled verification runtime candidate, not plugin.
  6. No external repository is modified and no external runtime/test/paper workflow is executed.
  7. Local verification results are recorded honestly, including any concurrent registry/router blocker.
