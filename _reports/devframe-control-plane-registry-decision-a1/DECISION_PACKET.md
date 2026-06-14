# Devframe-Control-Plane Registry Migration Decision Packet A1

Date: 2026-06-14
Created at: 2026-06-14T15:09:14.4308011+08:00
Task: devframe-control-plane-registry-decision-a1
Verdict: APPROVED_FOR_SCOPED_REGISTRY_MIGRATION

## Decision Record Draft

```yaml
decision_record:
  id: DECISION-20260614-DEVFRAME-CONTROL-PLANE-REGISTRY-A1
  timestamp: "2026-06-14T15:09:14.4308011+08:00"
  trigger: "Trigger 5: Project Registry Migration"
  decision_required: "Decide whether to accept the pending devframe-control-plane entry in .agent/PROJECT_REGISTRY.json."
  context: >
    The current worktree contains an unstaged registry diff that adds
    devframe-control-plane as a pending_binding project and changes
    total_projects from 17 to 18. Targeted registry/router tests pass, but
    project registry migration requires human authorization before commit.
  affected_files:
    - path: ".agent/PROJECT_REGISTRY.json"
      reason: "Adds devframe-control-plane and changes total_projects."
  options:
    - label: "Approve registry migration"
      description: "Commit the devframe-control-plane registry entry as pending_binding in a separate authorized task."
      risk: "medium"
      impact: "agent-acceptance gains routing awareness of D:\\devframe-control-plane, but execution remains forbidden until later human-gated activation."
    - label: "Defer registry migration"
      description: "Keep devframe-control-plane only in inactive-frame-registry for now and do not commit the PROJECT_REGISTRY diff."
      risk: "low"
      impact: "No new project routing surface is added; future integration remains documentation-only."
    - label: "Reject and restore registry diff"
      description: "Remove the pending PROJECT_REGISTRY diff and leave devframe-control-plane entirely outside the active project registry."
      risk: "low"
      impact: "Eliminates current registry drift, but a future task must recreate the entry if needed."
  agent_recommendation: >
    Defer registry migration unless a near-term task needs routing awareness of
    devframe-control-plane. This keeps devframe-control-plane governed by
    inactive-frame-registry while other agents finish work in external repos.
  human_decision: "Approve registry migration"
  authorization: "User replied: 授权！"
  committed_with: "devframe-control-plane-registry-migration-a1"
```

## Current Diff Summary

`git diff -- .agent/PROJECT_REGISTRY.json` currently shows:

- `total_projects`: 17 -> 18
- Added project entry: `devframe-control-plane`
- `project_root`: `D:\devframe-control-plane`
- `binding_status`: `pending_binding`
- `registered_at`: `2026-06-14T06:17:57Z`
- `updated_at`: `2026-06-14T06:17:57Z`

`git diff --numstat -- .agent/PROJECT_REGISTRY.json`:

- 8 insertions
- 2 deletions

## Technical Validation

The pending registry shape is technically valid:

```text
python -m pytest tests/test_validate_project_registry_bindings.py tests/test_router_10_project_stress.py -q
22 passed
```

This is only technical evidence. It does not authorize the registry migration.

## Human Authorization

On 2026-06-14, the user explicitly replied:

```text
授权！
```

This was interpreted as approval for
`DECISION-20260614-DEVFRAME-CONTROL-PLANE-REGISTRY-A1` option:
`Approve registry migration`.

The authorization is limited to committing the
`devframe-control-plane` pending binding entry in
`.agent/PROJECT_REGISTRY.json`. It does not authorize external runtime
execution, physical `devframe-system` bootstrap, submodule operations, or
mutation of `D:\dev-frame-opencode`, `D:\test-frame`, `D:\devframe-control-plane`,
or `D:\devframe-system`.

## Authority Boundary

Per `docs/agent-runtime/human-required-decision-record.md`, changing project
count or adding a project entry activates Mandatory Trigger 5: Project Registry
Migration. The agent must not self-authorize this action.

## Explicit Non-Actions

- `.agent/PROJECT_REGISTRY.json` is staged only by the follow-up authorized
  task `devframe-control-plane-registry-migration-a1`.
- `_projects/project-gamma` deletions are not staged by this task.
- No external repository runtime is executed.
- No external repository tests are executed.
- No paper workflow is executed.
- No cleanup, reset, stash, checkout, delete, or broad staging is performed.

## Historical Copy-Ready Human Decision Blocks

Approve:

```text
I approve DECISION-20260614-DEVFRAME-CONTROL-PLANE-REGISTRY-A1 Option: Approve registry migration. You may commit the devframe-control-plane pending_binding entry in .agent/PROJECT_REGISTRY.json in a dedicated scoped task. Do not execute external runtimes.
```

Defer:

```text
I choose DECISION-20260614-DEVFRAME-CONTROL-PLANE-REGISTRY-A1 Option: Defer registry migration. Do not commit the current .agent/PROJECT_REGISTRY.json diff. Keep devframe-control-plane in inactive-frame-registry only.
```

Reject:

```text
I choose DECISION-20260614-DEVFRAME-CONTROL-PLANE-REGISTRY-A1 Option: Reject and restore registry diff. Prepare a scoped task to remove the current .agent/PROJECT_REGISTRY.json devframe-control-plane diff without touching other worktree changes.
```
