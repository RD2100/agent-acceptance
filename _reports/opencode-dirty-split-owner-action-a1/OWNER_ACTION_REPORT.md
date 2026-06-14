# Dev-Frame-Opencode Dirty Split Owner Action Report

Task ID: opencode-dirty-split-owner-action-a1
Generated: 2026-06-14
Verdict: OWNER_ACTION_REQUIRED

## Summary

`D:\dev-frame-opencode` is the largest remaining dirty-baseline blocker for
`devframe-system` Phase 0.5. Its dirty state is not artifact-only. It includes
real source/config changes, a very large `tasks.yaml` generated/state delta,
and more than ten thousand untracked files.

This repository cannot be pinned as a trustworthy submodule baseline until the
owner splits and resolves these classes.

No external mutation or runtime execution was performed by this task.

## Repository State

| Field | Value |
|---|---|
| Path | `D:\dev-frame-opencode` |
| Branch | `master` |
| HEAD | `da4de796` |
| Remote | `origin=git@github.com:RD2100/dev-frame-opencode.git` |
| Total status entries | 10,288 |
| Tracked dirty files | 7 |
| Staged files | 0 |
| Unstaged files | 7 |
| Untracked files | 10,281 |

Local policy:

- `AGENTS.md` exists.
- Phase 0-5 forbids git mutations: no commit, push, reset, clean, or stash.
- External skills are not active, package install is forbidden, and capability
  registration requires review before enablement.

## Tracked Dirty Files

| File | Added | Deleted | Classification | Submodule impact |
|---|---:|---:|---|---|
| `AGENTS.md` | 62 | 68 | governance instructions drift | hard blocker |
| `ai-workflow-hub/pyproject.toml` | 1 | 0 | config/dependency drift | hard blocker |
| `ai-workflow-hub/src/ai_workflow_hub/cli.py` | 4,176 | 243 | source code expansion | hard blocker |
| `ai-workflow-hub/src/ai_workflow_hub/daemon.py` | 38 | 11 | source code/runtime behavior | hard blocker |
| `ai-workflow-hub/src/ai_workflow_hub/task_queue.py` | 5 | 2 | source code/queue behavior | hard blocker |
| `ai-workflow-hub/tasks.yaml` | 72,848 | 0 | generated/task state or large operational state | hard blocker until classified |
| `smoke_report.txt` | 14 | 14 | report artifact drift | separable artifact |

Tracked diff total:

- 7 files changed.
- 77,144 insertions.
- 338 deletions.
- `git diff --check`: PASS with LF/CRLF warnings only.

## CLI Change Signal

The `cli.py` diff adds many paper-related commands and support helpers,
including:

- `paper create`
- `paper run`
- `paper resume`
- `paper status`
- `paper list`
- `paper go`
- `paper ledger`
- `paper evidence`
- `paper validate`
- `paper report`
- `paper audit`
- `paper verify`
- `paper verify-chain`
- `paper checkpoint`
- `paper policy-schema`

This is a major source-code change, not an artifact cleanup issue. It also
touches the paused paper workflow domain, so it must not be treated as active
integration work without separate authorization and review.

## Untracked Top-Level Groups

| Group | Count | Initial classification |
|---|---:|---|
| `.chrome-cdp-profile` | 4,159 | browser profile/session state, likely should not be committed |
| `_reports` | 3,386 | generated reports/evidence candidate |
| `ai-workflow-hub` | 895 | mixed source/generated/test artifacts, requires owner review |
| `_package_for_gpt` | 541 | review package/artifact |
| `_global_final_audit_pack` | 537 | audit package/artifact |
| `.ai` | 353 | governance/session state |
| `tools` | 94 | possible source/tooling, requires owner review |
| `_global_final_audit_remediation_pack` | 73 | audit remediation artifact |
| `docs` | 52 | possible governance/source docs |
| `schemas` | 45 | possible governance/source schemas |
| `scripts` | 40 | possible source/tooling |
| `.opencode` | 9 | local tool/session state |
| `templates` | 8 | possible source templates |
| `rules` | 8 | governance source candidate |
| `.claude` | 2 | local blackboard/session state |

The untracked set is too large and mixed to classify automatically as either
source or artifact. Owner partitioning is required.

## Owner Action Needed

Recommended owner sequence:

1. Freeze the current `dev-frame-opencode` worktree for review, without running
   runtime commands.
2. Split tracked changes into at least four review tracks:
   - governance instruction drift: `AGENTS.md`;
   - source/config changes: `pyproject.toml`, `cli.py`, `daemon.py`,
     `task_queue.py`;
   - generated/task state: `tasks.yaml`;
   - artifacts: `smoke_report.txt`.
3. For `cli.py`, perform a dedicated paper-domain review before any integration
   claim, because the added command surface is large and paper workflow remains
   paused in the current governance scope.
4. For untracked files, define policy by group:
   - never commit browser/session profiles;
   - archive or ignore generated audit/report packages;
   - separately review untracked `tools`, `scripts`, `docs`, `schemas`,
     `rules`, and `templates` as possible source/governance content.
5. Bring the repository to a clean owner-approved commit state.
6. Re-run Phase 0.5 preflight after `dev-frame-opencode` is clean.

## Integration Impact

Current state:

- `dev-frame-opencode` remains the largest blocker.
- It blocks physical `devframe-system` submodule pinning.
- It blocks any claim that opencode integration is ready for runtime use.

Allowed now:

- Read-only review and planning.
- Owner-directed split/commit plan.

Still not allowed:

- `opencode run`.
- Paper workflow execution.
- Runtime/bootstrap integration.
- Submodule pinning.

## Non-Actions

The following actions were not performed:

- No `dev-frame-opencode` commit.
- No `dev-frame-opencode` reset, clean, stash, checkout, or unstage.
- No opencode runtime, build, package install, or test command.
- No paper workflow execution.
- No `D:\devframe-system` creation.
- No submodule command.

## Acceptance Gate Evaluation

| Gate | Result | Evidence |
|---|---|---|
| Runner start/edit-check | PASS | Runner start and edit-check passed for task/report/evidence/current-task files. |
| Dirty state split | PASS | Source/config, generated state, and artifact groups are separated above. |
| Large hard blockers identified | PASS | `cli.py` and `tasks.yaml` deltas are explicitly called out. |
| Owner actions given without performing them | PASS | See Owner Action Needed and Non-Actions. |
| No external mutation or runtime | PASS | Only read-only git/contents commands were used against `D:\dev-frame-opencode`. |
| Final checks | PASS | Targeted tests: 22 passed. Diff check: exit 0 with LF/CRLF warning only. `D:\devframe-system`: absent. Opencode HEAD: `da4de796`; status entries: 10,288. |
