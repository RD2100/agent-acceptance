# Devframe-System Workspace Risk Triage A1

Date: 2026-06-14
Task: devframe-system-workspace-risk-triage-a1
Verdict: HUMAN_REQUIRED

## Purpose

This report records the current `D:\agent-acceptance` worktree risks after
commit `0f1e69fa docs: record controlled multi-gpt human-required refresh`.
It prevents broad staging of unrelated dirty changes while devframe-system
activation work continues.

## Current Facts

| Item | Evidence | Status |
| --- | --- | --- |
| Latest committed governance step | `git log --oneline -1` -> `0f1e69fa docs: record controlled multi-gpt human-required refresh` | committed |
| Total current worktree entries | `git status --short` -> 508 entries | dirty |
| Project registry diff | `.agent/PROJECT_REGISTRY.json` -> 8 insertions, 2 deletions | HUMAN_REQUIRED |
| Registry semantic change | adds `devframe-control-plane` with `binding_status=pending_binding`; `total_projects` 17 -> 18 | Trigger 5 |
| Registry/router validation | `python -m pytest tests/test_validate_project_registry_bindings.py tests/test_router_10_project_stress.py -q` -> 22 passed | technically valid |
| Project-gamma deletion set | `_projects/project-gamma` -> 188 deleted files, 14301 deleted lines | not accepted |
| Historical recursive governance artifacts | 14 untracked entries under old closure/evidence tasks | not part of current commit scope |
| Devframe-system directory | `D:\devframe-system` exists; `git rev-parse --is-inside-work-tree` -> not a git repo | not activated |

## Risk Classification

### 1. `.agent/PROJECT_REGISTRY.json`

The diff is internally consistent and targeted tests pass, but it is still a
project registry migration:

- It changes `total_projects`.
- It adds a new project entry for `devframe-control-plane`.
- It grants future routing awareness to an external repository path.

Per `docs/agent-runtime/human-required-decision-record.md`, this activates
Mandatory Trigger 5: Project Registry Migration. Therefore this change must not
be committed as a side effect of another task. It needs either:

1. a valid decision record committed with the registry migration, or
2. an explicit de-scope decision that leaves `devframe-control-plane` only in
   `docs/agent-runtime/inactive-frame-registry.md`.

Current decision: HUMAN_REQUIRED.

### 2. `_projects/project-gamma`

The worktree currently shows 188 deleted tracked files under
`_projects/project-gamma`, totaling 14301 deleted lines. This is a large
baseline mutation and is not covered by the current task.

No evidence in this triage proves that these deletions are intentional,
reviewed, or safe. They must not be staged by broad commands.

Current decision: HOLD / DO NOT STAGE.

### 3. `D:\devframe-system`

The directory exists, but it is not a git repository and does not establish a
trusted superproject baseline. It remains a future superproject control target,
not an active runtime or submodule root.

Current decision: NOT ACTIVATED.

## Allowed Next Routes

Route A: strict baseline

- Resolve or commit all intentional work in the four source repositories.
- Ensure each source repository has an owner-approved clean commit.
- Only then create a trusted superproject baseline or submodule pin.

Route B: dirty-aware skeleton

- Human explicitly authorizes skeleton-only work despite dirty sources.
- No submodule add.
- No source lock claiming clean baseline.
- Record every dirty source as an accepted limitation.

Registry route

- Create a Trigger 5 decision record for `devframe-control-plane` registry
  registration before committing `.agent/PROJECT_REGISTRY.json`.

Project-gamma route

- Owner must either restore the deletion set, or provide a dedicated TaskSpec
  and evidence proving the deletion is intended.

## Explicit Non-Actions

- No external repository runtime executed.
- No external repository tests executed.
- No paper workflow executed.
- No cleanup, reset, stash, checkout, delete, or broad staging performed.
- No `D:\devframe-system` bootstrap or submodule add performed.
- No `.agent/PROJECT_REGISTRY.json` change accepted by this task.
- No `_projects/project-gamma` deletion accepted by this task.

## Verification

| Command | Result |
| --- | --- |
| `git status --short` | 508 entries |
| `git diff --numstat -- .agent/PROJECT_REGISTRY.json` | 8 insertions, 2 deletions |
| `git diff --stat -- _projects/project-gamma` | 188 files changed, 14301 deletions |
| `python -m pytest tests/test_validate_project_registry_bindings.py tests/test_router_10_project_stress.py -q` | 22 passed |
| `Test-Path D:\devframe-system` | True |
| `git -C D:\devframe-system rev-parse --is-inside-work-tree` | not_git_repo |

## Reviewer Index

Changed files in this task:

- `.ai/current-task.yaml`
- `tasks/devframe-system-workspace-risk-triage-a1.md`
- `_reports/devframe-system-workspace-risk-triage-a1/WORKSPACE_RISK_TRIAGE.md`

Review focus:

- Confirm the report does not claim the registry migration is approved.
- Confirm the report does not accept project-gamma deletions.
- Confirm no external runtime or external repository mutation is claimed.
- Confirm the registry/router test result is scoped to technical validity only.
