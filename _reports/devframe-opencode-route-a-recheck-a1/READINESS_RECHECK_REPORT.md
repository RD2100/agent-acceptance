# Dev-Frame-OpenCode Route A Readiness Recheck A1

Generated: 2026-06-14
Task: devframe-opencode-route-a-recheck-a1
Evidence: `_evidence/devframe-opencode-route-a-recheck-a1/route_a_preflight_stdout.json`

## Verdict

dev-frame-opencode: NOT_READY_FOR_ROUTE_A_BASELINE
devframe-system physical merge: NOT_AUTHORIZED
Route A strict clean baseline: HUMAN_REQUIRED

The user reported that `dev-frame-opencode` should be ready. Current local
evidence contradicts that report. This recheck is read-only and does not mutate
any source repository.

## Current Evidence

| Source | Status | Branch | HEAD | Upstream | Dirty summary |
|---|---|---|---|---|---|
| agent-acceptance | HUMAN_REQUIRED | master | df97ec0f33dea44ed83d598fba79b567bb4003bb | origin/master | tracked dirty 189, staged 0, unstaged 189, untracked 408 |
| devframe-control-plane | READY_AS_CLEAN_BASELINE_CANDIDATE | codex/route-a-baseline-candidate | 311847818927d3c7ec8c8718949b38c74605fc83 | origin/codex/route-a-baseline-candidate | clean |
| test-frame | READY_AS_CLEAN_BASELINE_CANDIDATE | codex/harden-baseline | aeb4a31f770e35e7f698e5c3169406ddba231a4d | origin/codex/harden-baseline | clean |
| dev-frame-opencode | NOT_READY | master | da4de796c38d466a6df31422e5a066445edc05f4 | origin/master | tracked dirty 7, staged 0, unstaged 7, untracked 10511 |

`dev-frame-opencode` HEAD equals `origin/master`, but the worktree is not clean.
That means its current HEAD cannot be frozen as a trusted strict Route A
baseline.

## Dev-Frame-OpenCode Dirty Tracked Paths

```text
AGENTS.md
ai-workflow-hub/pyproject.toml
ai-workflow-hub/src/ai_workflow_hub/cli.py
ai-workflow-hub/src/ai_workflow_hub/daemon.py
ai-workflow-hub/src/ai_workflow_hub/task_queue.py
ai-workflow-hub/tasks.yaml
smoke_report.txt
```

Untracked count at recheck time: 10511.

Representative untracked paths include:

```text
.agent/CONVERSATION_BINDING.json
.agents/skills/oracle-gpt-review-handoff/SKILL.md
.ai/ledger/issues.jsonl
.ai/ledger/recurrence-index.json
.ai/reports/2026-05-31-go-agent-issue-ledger-result.md
```

## Target Path State

`D:\devframe-system` exists, but it is still empty and inactive:

```text
exists: true
item_count: 0
has_git_dir: false
has_gitmodules: false
```

The directory existence alone is not a completed merge and does not authorize
submodule bootstrap.

## Non-Actions

- No external repository mutation.
- No external runtime execution.
- No external tests or builds.
- No cleanup, reset, stash, checkout, or destructive git operation.
- No submodule add.
- No paper workflow.

## Gate Results

| Gate | Result | Evidence |
|---|---|---|
| Gate 0: current state inspected | PASS | route preflight JSON captured |
| Gate 1: no runtime execution | PASS | `executed_external_runtime=false` |
| Gate 2: no mutation | PASS | `performed_mutation=false` |
| Gate 3: clean baselines identified | PARTIAL | control-plane and test-frame passed |
| Gate 4: opencode readiness | FAIL | dirty total 10518 |
| Gate 5: physical merge authorization | BLOCKED | Route A remains HUMAN_REQUIRED |

## Required Next Action

`dev-frame-opencode` must be re-run in the actual checkout at
`D:\dev-frame-opencode` until:

```powershell
git status --porcelain=v1 -uall
git rev-parse HEAD
git rev-parse @{u}
```

The first command has no output, and the two hashes match. Only then should
Route A preflight be refreshed again.
