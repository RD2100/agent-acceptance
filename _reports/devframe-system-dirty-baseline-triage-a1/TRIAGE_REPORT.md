# Devframe-System Dirty Baseline Triage Report

Task ID: devframe-system-dirty-baseline-triage-a1
Generated: 2026-06-14
Verdict: HUMAN_REQUIRED
Supersedes count snapshot in: `_reports/devframe-system-phase05-strict-gate-a1/PREFLIGHT_REPORT.md`

## Summary

The strict Phase 0.5 gate is still correct. `D:\devframe-system` must not be
created yet, and local submodules must not be added yet. The blocker is no
longer just "some dirty files"; the dirty baseline has four different classes:

1. `dev-frame-opencode` has real code/config changes and a very large modified
   task file.
2. `test-frame` has a staged governance bootstrap package that is not committed.
3. `devframe-control-plane` appears mostly artifact/runtime-output dirty.
4. `agent-acceptance` contains prior project-gamma deletions, live refresh work,
   hook artifacts, and many untracked governance artifacts.

Pinning submodules now would pin only committed HEADs and lose the real current
state visible in each worktree.

## Latest Dirty Inventory

| Project | Path | Branch | HEAD | Total status entries | Tracked | Staged | Unstaged | Untracked | Triage class |
|---|---|---|---|---:|---:|---:|---:|---:|---|
| agent-acceptance | `D:\agent-acceptance` | master | 7856e5f1 | 412 | 199 | 0 | 199 | 213 | mixed governance leftovers and active local work |
| dev-frame-opencode | `D:\dev-frame-opencode` | master | da4de796 | 894 | 7 | 0 | 7 | 887 | code/config changes plus large untracked workspace |
| devframe-control-plane | `D:\devframe-control-plane` | main | a62dd30 | 29 | 1 | 0 | 1 | 28 | runtime/artifact outputs likely separable |
| test-frame | `D:\test-frame` | codex/harden-baseline | ee00179 | 113 | 113 | 111 | 2 | 0 | staged governance bootstrap package |

## Repository Triage

### agent-acceptance

Observed groups:

- 188 deleted tracked files under `_projects/project-gamma`.
- 11 modified tracked files, including local conversation binding, hook output,
  live multi-agent evidence, dispatch plan/current preflight state, and related
  tests/scripts.
- 213 untracked entries, mostly evidence/report/task artifacts and backup files.

Decision:

- Not safe to use as a clean baseline for superproject submodule pinning.
- This repository can still host governance reports because the task runner and
  pre-commit hook enforce precise staging.

Owner action needed:

- Separate project-gamma deletion intent from unrelated artifacts.
- Commit or explicitly archive the live-refresh/multi-agent work.
- Keep hook-output rotation out of logical readiness claims.

### dev-frame-opencode

Tracked dirty files:

- `AGENTS.md`
- `ai-workflow-hub/pyproject.toml`
- `ai-workflow-hub/src/ai_workflow_hub/cli.py`
- `ai-workflow-hub/src/ai_workflow_hub/daemon.py`
- `ai-workflow-hub/src/ai_workflow_hub/task_queue.py`
- `ai-workflow-hub/tasks.yaml`
- `smoke_report.txt`

Diff scale:

- 7 tracked files changed.
- About 76,524 insertions and 338 deletions.
- `ai-workflow-hub/tasks.yaml` dominates the diff with about 72,228 inserted lines.
- 887 untracked entries are present.

Decision:

- This is a hard blocker for submodule pinning.
- It is not only artifact noise; it includes core CLI, daemon, queue, config, and
  task data changes.

Owner action needed:

- Produce a dedicated commit or rollback/partition plan inside `dev-frame-opencode`.
- Identify whether the large `tasks.yaml` delta is intended state, generated
  state, or an artifact that should be excluded.
- Do not run opencode runtime as part of Phase 0.5 triage.

### devframe-control-plane

Observed groups:

- 1 modified tracked file: `artifacts/run_history.jsonl`.
- 28 untracked entries, mostly `.coverage` and `artifacts/cli-test-*.json`.

Decision:

- Likely artifact/runtime-output dirty, but still not clean.
- Lower risk than `dev-frame-opencode` because no core source file appears in
  the tracked dirty set.

Owner action needed:

- Decide whether runtime artifacts should be ignored, archived, or committed.
- Re-run clean baseline check after owner action.
- Do not start control-plane runtime as part of this triage.

### test-frame

Observed groups:

- 111 staged changes.
- 2 unstaged modifications in `.claude/blackboard/state.json` and backup.
- Staged package includes `AGENTS.md`, `docs/agent-runtime/**`, `rules/**`,
  `schemas/**`, and `templates/runtime-bootstrap/**`.

Decision:

- Hard blocker for submodule pinning because staged but uncommitted governance
  bootstrap work would not be represented by a submodule commit pointer.
- `test-frame` remains a controlled verification runtime candidate, not a
  plugin, not a governance source of truth, and not a verdict source.

Owner action needed:

- Commit, split, or explicitly discard the staged bootstrap package.
- Resolve the blackboard state modifications separately.
- Do not run test-frame tests or runtime as part of Phase 0.5 triage.

## Readiness Decision

Current readiness for physical `D:\devframe-system` bootstrap:

- `strict_superproject_bootstrap`: BLOCKED
- `dirty_aware_skeleton_without_submodules`: available only after explicit human authorization
- `submodule_add`: BLOCKED
- `runtime_integration`: BLOCKED
- `paper_workflow`: paused

## Recommended Next Sequence

1. Resolve `test-frame` staged governance bootstrap first. It is already staged
   and likely closest to becoming a clean commit.
2. Triage `devframe-control-plane` artifacts next. It appears mostly output-only.
3. Split `dev-frame-opencode` into code/config changes versus generated task or
   evidence state. This is the largest and riskiest dirty source.
4. Handle `agent-acceptance` project-gamma deletions and live-refresh leftovers
   separately from the devframe-system integration track.
5. Re-run Phase 0.5 preflight only after all four source repositories are clean,
   or after explicit authorization for a dirty-aware skeleton.

## Non-Actions

The following actions were not performed:

- No cleanup, reset, stash, commit, or checkout in external repositories.
- No `git submodule add`.
- No `D:\devframe-system` directory creation.
- No opencode runtime execution.
- No control-plane runtime execution.
- No test-frame test/build/runtime execution.
- No paper workflow execution.

## Acceptance Gate Evaluation

| Gate | Result | Evidence |
|---|---|---|
| Runner start/edit-check | PASS | Runner start and edit-check completed for task/report/evidence/current-task files. |
| Dirty states classified | PASS | See repository triage sections. |
| Phase 0.5 verdict preserved | PASS | Verdict remains HUMAN_REQUIRED. |
| Owner action identified | PASS | See owner action needed sections. |
| No external runtime or mutation | PASS | Only read-only git status/diff-stat commands were used outside `D:\agent-acceptance`. |
| Final checks | PASS | Targeted tests: 22 passed. Diff check: exit 0 with LF/CRLF warning only. `D:\devframe-system`: absent. |
