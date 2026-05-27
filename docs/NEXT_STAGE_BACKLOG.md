# Next Stage Backlog

## P1: Real Full E2E Data-Plane Pass

- **Why**: Control-plane passes but data-plane (executor creates file, reviewer proceeds) still needs verification.
- **Trigger**: User ACK + real backend call with budget 300/600.
- **Acceptance**: `goal run` creates allowed untracked file, diff captured, reviewer passes, file present in worktree.
- **Risk**: MODEL_TIMEOUT (planner latency ~188s), system timeout (600s).

## P1: Cleanup Apply Mode

- **Why**: Dry-run lists 92 test goals + 16 orphan runs. Apply mode would reduce clutter.
- **Trigger**: Retention policy reviewed, ARTIFACT_RETENTION_POLICY.md signed off.
- **Acceptance**: `artifacts cleanup --apply --yes` deletes only classifier-confirmed fixtures; real E2E preserved.
- **Risk**: Classifier over-deletion of unknown artifacts. Conservative defaults mitigate.

## P2: Retention Dashboard

- **Why**: 92+ test goals is not visible without running cleanup dry-run.
- **Trigger**: Cleanup apply mode enabled.
- **Acceptance**: `artifacts status` or `goal list` shows retention summary.
- **Risk**: Dashboard query performance on large artifact counts.

## P2: Executor/Reviewer Behavior Tuning

- **Why**: Current executor conservatively skips file creation, leading to reviewer block.
- **Trigger**: After data-plane E2E pass is attempted.
- **Acceptance**: Executor creates allowed files by default; reviewer proceeds on valid diff.
- **Risk**: Executor writes to wrong worktree or exceeds allowed_files.

## P3: Release Automation

- **Why**: Manual verification checklist is 9 commands.
- **Trigger**: P1 items complete.
- **Acceptance**: `acceptance run pre-release` runs all checks in one command.
- **Risk**: Low — wraps existing commands.

## P2: Missing Documentation Recovery

The following documents are referenced by batch-docs-quality checks but do not exist in the repository. They are exempt from docs-quality checks and tracked here for future completion.

- **E2E_FULL_WORKFLOW_EXPERIMENT.md** — referenced by v1.17 release pack; records the full E2E workflow experiment.
- **E2E_TIMEOUT_DECISION.md** — Planner timeout decision record.
- **E2E_PROBE_RUNBOOK.md** — v1.17 Key Commands reference; runbook for E2E probing.
- **STATUS_MACHINE.md** — WorkQueue state machine rules.

## P3: Multi-Project E2E

- **Why**: Current testing only uses `test-repo`.
- **Trigger**: Data-plane E2E pass on single project.
- **Acceptance**: Goal run with real project as target.
- **Risk**: Higher — may modify real project files.
