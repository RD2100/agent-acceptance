# Agent-Acceptance Runtime Artifact Ignore A1

Generated: 2026-06-14
Task: agent-acceptance-runtime-artifact-ignore-a1

## Verdict

Runtime artifact cleanup: COMPLETED

This task reduces `agent-acceptance` local baseline noise without deleting local
evidence files. It adds precise ignore rules for generated governance/runtime
artifacts and removes the rotating hook latest file from version control while
leaving the local file on disk.

## Actions

- Added `.gitignore` rules for:
  - `.agent` registry backup files.
  - `_evidence/hook-output/` generated hook logs.
  - archived non-conformant governance closure evidence directories.
  - known one-off generated report snapshots.
  - stale recursive closure TaskSpecs.
- Ran index-only untrack:

```powershell
git rm --cached -- _evidence/hook-output/latest.json
```

- Confirmed `_evidence/hook-output/latest.json` still exists locally after
  untracking.
- Closed stale untracked TaskSpec:
  `tasks/devframe-system-decision-index-refresh-a1.md`.

## Evidence

- Pre-ignore status:
  `_evidence/agent-acceptance-runtime-artifact-ignore-a1/pre_ignore_status.txt`
- Post-ignore status:
  `_evidence/agent-acceptance-runtime-artifact-ignore-a1/post_ignore_status.txt`

## Non-Actions

- No generated evidence files were deleted.
- No external repository mutation.
- No external runtime, external tests, submodule command, cleanup, reset, stash,
  checkout, or paper workflow.
- No source, test, schema, rule, or active governance document path was hidden by
  a broad ignore rule.

## Gate Results

| Gate | Result |
|---|---|
| Gate 0: runtime artifact inventory | PASS |
| Gate 1: precise ignore rules | PASS |
| Gate 2: index-only latest untrack | PASS |
| Gate 3: local latest file preserved | PASS |
| Gate 4: stale task closed, not hidden | PASS |

## Remaining Merge Blocker

`dev-frame-opencode` is still dirty and remains the external Route A blocker.
