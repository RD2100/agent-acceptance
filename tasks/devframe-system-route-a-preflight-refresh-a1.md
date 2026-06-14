# TaskSpec: devframe-system-route-a-preflight-refresh-a1

**ID**: devframe-system-route-a-preflight-refresh-a1
**Priority**: P1
**Status**: completed
**Type**: devframe_system_route_a_preflight_refresh

## Intent

Refresh the latest Route A no-op preflight dashboard after `test-frame` reached
a clean baseline candidate state. This task must not mutate external
repositories, run external runtimes, run external tests/builds, or perform
physical `devframe-system` bootstrap.

gate_0:
  triggered: true
  trigger_reason: "Latest read-only validator output shows test-frame clean; dashboard needs a scoped refresh."
  inventory_evidence:
    queried_sources:
      - "_reports/devframe-system-route-a-preflight-a1/ROUTE_A_PREFLIGHT.json"
      - "_reports/devframe-system-route-a-preflight-a1/MERGE_DASHBOARD.md"
      - "scripts/devframe_system_route_a_preflight.py"
      - "docs/agent-runtime/devframe-system-phase05-index.md"
      - "docs/agent-runtime/devframe-system-phase05-handoff-brief.md"
    matched_capabilities:
      - sadp_governance
      - route_a_read_only_preflight
      - merge_readiness_reporting
      - external_runtime_non_execution_gate
  rules_checked: [core-001, core-004, core-005, core-007, core-008, review-001, git-001]
  lessons_checked:
    - "Keep dashboards current when source baseline status changes."
    - "Do not claim physical merge completion from clean candidate status."
  sufficiency_decision: existing_sufficient
  decision: reuse
  delta_justification: "Refresh existing preflight artifacts only."

conflict_registry:
  read_set:
    - "_reports/devframe-system-route-a-preflight-a1/ROUTE_A_PREFLIGHT.json"
    - "_reports/devframe-system-route-a-preflight-a1/MERGE_DASHBOARD.md"
    - "scripts/devframe_system_route_a_preflight.py"
    - "docs/agent-runtime/devframe-system-phase05-index.md"
    - "docs/agent-runtime/devframe-system-phase05-handoff-brief.md"
  write_set:
    - .ai/current-task.yaml
    - tasks/devframe-system-route-a-preflight-refresh-a1.md
    - _reports/devframe-system-route-a-preflight-a1/ROUTE_A_PREFLIGHT.json
    - _reports/devframe-system-route-a-preflight-a1/MERGE_DASHBOARD.md
    - _reports/devframe-system-route-a-preflight-refresh-a1/**
    - _evidence/devframe-system-route-a-preflight-refresh-a1/**
    - docs/agent-runtime/devframe-system-phase05-index.md
    - docs/agent-runtime/devframe-system-phase05-handoff-brief.md
    - hooks/sealed-files-manifest.json
  governance_adjacent_files_modified:
    - ".ai/current-task.yaml"
    - "docs/agent-runtime/devframe-system-phase05-index.md"
    - "docs/agent-runtime/devframe-system-phase05-handoff-brief.md"
    - "hooks/sealed-files-manifest.json"
  protected_files_touched: true
  protected_file_justification: "docs index/handoff are route navigation files; sealed manifest may be pre-commit regenerated."
  conflict_level: medium

**Acceptance Gates**:
  1. Dashboard says `test-frame` is a clean baseline candidate if validator evidence proves it.
  2. Dashboard keeps `devframe-system` as `NOT_MERGED / HUMAN_REQUIRED`.
  3. No external runtime or external repository mutation occurs.
  4. Runner start/edit-check/finish and targeted checks pass.
