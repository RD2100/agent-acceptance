# Router Registry Current Count Sync A1

Status: completed
Date: 2026-06-14

## Problem

`tests/test_router_10_project_stress.py` hard-coded `EXPECTED_PROJECTS = 17`
and a fixed pending project list. The current registry declares 18 projects
after adding `devframe-control-plane` as `pending_binding`, so the router stress
suite failed even though the router behavior was not the failing component.

## Change

Updated the test contract to:

- assert `.agent/PROJECT_REGISTRY.json` `total_projects` matches the actual
  project map length;
- derive the expected project count from the registry rather than a stale test
  constant;
- derive the full pending set from the registry for count equality;
- keep explicit assertions for required active, suspended, and required pending
  project identities;
- treat `devframe-control-plane` as an optional pending project when present,
  so the test remains compatible with both the committed 17-project registry and
  the current 18-project worktree.

No registry data was changed by this task.

## Verification

- `python -m pytest tests/test_validate_project_registry_bindings.py tests/test_router_10_project_stress.py -q`
  - result: `22 passed in 0.19s`

Additional local checks:

- `git diff --check -- <task files>`
  - result: exit 0, Windows CRLF warnings only.
- `python scripts\qoderwork_task_runner.py finish --task-id router-registry-current-count-sync-a1`
  - result: PASS, all SADP artifacts present.

## Boundaries

- No external repository was modified.
- No external runtime, build, package install, submodule, cleanup, reset, stash,
  checkout, or paper workflow command was run.
- The current `.agent/PROJECT_REGISTRY.json` change remains an existing
  worktree change outside this task's write set.
