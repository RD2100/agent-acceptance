# TaskSpec: DEVFRAME-SYSTEM-GAP-TRACKER-REFRESH-A1

**ID**: devframe-system-gap-tracker-refresh-a1
**Priority**: P1
**Status**: completed
**Type**: governance_gap_tracker_refresh

## Intent

Refresh the devframe-system Phase 0.5 navigation after the router/registry
stress-test blocker recorded in the current gap tracker was resolved by commit
`78689129`. The refresh must keep the larger Route A/Route B verdict unchanged:
`HUMAN_REQUIRED` because source repositories remain dirty and external runtime
execution is still unauthorized.

gate_0:
  triggered: true
  trigger_reason: "The previous current gap tracker recorded router stress failure; targeted local validation now passes after router-registry-current-count-sync-a1."
  inventory_evidence:
    queried_sources:
      - "_reports/devframe-system-current-gap-tracker-a1/CURRENT_GAP_TRACKER.md"
      - "_reports/router-registry-current-count-sync-a1/EXECUTION_REPORT.md"
      - "docs/agent-runtime/devframe-system-phase05-index.md"
      - "docs/agent-runtime/devframe-system-phase05-handoff-brief.md"
      - "python -m pytest tests/test_validate_project_registry_bindings.py tests/test_router_10_project_stress.py tests/test_multi_agent_dispatch_plan.py tests/test_multi_agent_gate0_preflight.py -q"
    matched_capabilities:
      - sadp_governance
      - documentation_navigation
      - multi_project_registry
      - shared_cdp_router
      - external_runtime_non_execution_gate
  rules_checked: [core-001, core-004, core-005, core-008, review-001, git-001]
  sufficiency_decision: existing_sufficient
  decision: reuse
  delta_justification: "This task refreshes governance navigation only and does not mutate registry or external repositories."

conflict_registry:
  read_set:
    - "_reports/devframe-system-current-gap-tracker-a1/CURRENT_GAP_TRACKER.md"
    - "_reports/router-registry-current-count-sync-a1/EXECUTION_REPORT.md"
    - "docs/agent-runtime/devframe-system-phase05-index.md"
    - "docs/agent-runtime/devframe-system-phase05-handoff-brief.md"
    - ".ai/current-task.yaml"
  write_set:
    - tasks/devframe-system-gap-tracker-refresh-a1.md
    - .ai/current-task.yaml
    - docs/agent-runtime/devframe-system-phase05-index.md
    - docs/agent-runtime/devframe-system-phase05-handoff-brief.md
    - _reports/devframe-system-gap-tracker-refresh-a1/**
    - _evidence/DEVFRAME-SYSTEM-GAP-TRACKER-REFRESH-A1/**
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
  2. Index and handoff identify the current gap refresh as the latest status overlay.
  3. Refresh report says router stress blocker is resolved, but Route A/Route B remain blocked.
  4. Targeted local governance/router tests pass.
  5. No external repository or runtime is touched.
