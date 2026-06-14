# TaskSpec: ROUTER-REGISTRY-CURRENT-COUNT-SYNC-A1

**ID**: router-registry-current-count-sync-a1
**Priority**: P1
**Status**: completed
**Type**: test_governance_alignment

## Intent

Fix the router stress test drift exposed by the current project registry. The
test must continue to verify router behavior, but it should not hard-code a
stale project count when `PROJECT_REGISTRY.json` already declares the canonical
`total_projects` value.

gate_0:
  triggered: true
  trigger_reason: "Router stress tests failed because registry now contains 18 projects while the test still expected 17."
  inventory_evidence:
    queried_sources:
      - "tests/test_router_10_project_stress.py"
      - ".agent/PROJECT_REGISTRY.json"
      - "python -m pytest tests/test_validate_project_registry_bindings.py tests/test_router_10_project_stress.py -q"
    matched_capabilities:
      - sadp_governance
      - multi_project_registry
      - shared_cdp_router
      - test_governance
  rules_checked: [core-001, core-004, core-005, core-008, review-001, git-001]
  sufficiency_decision: existing_sufficient
  decision: reuse
  delta_justification: "This task changes the test contract only; it does not mutate registry data or external repositories."

conflict_registry:
  read_set:
    - tests/test_router_10_project_stress.py
    - .agent/PROJECT_REGISTRY.json
    - .ai/current-task.yaml
  write_set:
    - tasks/router-registry-current-count-sync-a1.md
    - .ai/current-task.yaml
    - tests/test_router_10_project_stress.py
    - _reports/router-registry-current-count-sync-a1/**
    - _evidence/ROUTER-REGISTRY-CURRENT-COUNT-SYNC-A1/**
    - hooks/sealed-files-manifest.json
    - _evidence/hook-output/**
  governance_adjacent_files_modified:
    - ".ai/current-task.yaml"
    - "tests/test_router_10_project_stress.py"
  protected_files_touched: false
  conflict_level: medium

**Acceptance Gates**:
  1. Runner start, edit-check, and finish complete without blocking.
  2. Router stress tests derive project count from registry `total_projects` and actual registry entries.
  3. Tests still assert known active, suspended, and pending project identities that matter for routing.
  4. `python -m pytest tests/test_validate_project_registry_bindings.py tests/test_router_10_project_stress.py -q` passes in the current worktree.
  5. No external repository or runtime is touched.
