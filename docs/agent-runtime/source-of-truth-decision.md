# Source of Truth Decision — RD2100 Agent Runtime v2

> Generated: Batch A2, 2026-05-27
> Decision by: Reviewer (human review of Batch A1 inventory)
> Status: **approved_for_batch_a2**

## Decision

```json
{
  "status": "approved_for_batch_a2",
  "canonical_root": "D:\\agent-acceptance",
  "secondary_paths": ["D:\\dev-frame\\agent-acceptance"],
  "deprecated_aliases": ["D:\\devFrame"],
  "decided_by": "reviewer",
  "decided_date": "2026-05-27"
}
```

## Rationale

1. **`D:\agent-acceptance` is the active working root** for the current session and contains the most complete infrastructure: `.claude/`, `.codegraph/`, `templates/`, `runs/`, scripts, workqueues, and documentation.

2. **`D:\dev-frame\agent-acceptance` is a secondary clone** at the same commit (`100a116`) but with a different remote (SSH) and fewer infrastructure files. It is recognized as a secondary path, not an alternative canonical root.

3. **`D:\devFrame` does not exist** on disk. It is referenced in `README.md` and Claude project memory but the actual path is `D:\dev-frame`. It is classified as a deprecated alias.

## Constraints (Batch A2 Scope)

The following constraints apply to Batch A2 and were set by the reviewer:

| Constraint | Detail |
|------------|--------|
| Write scope | Only new files under `D:\agent-acceptance\docs\agent-runtime\` |
| No modifications | Do not touch README.md, AGENTS.md, scripts/, agent-workqueue/, memory, hooks, MCP config, .claude/, .codegraph/ |
| Dirty baseline | Treat existing dirty worktree (13M + 6U) as baseline — no commit, stash, reset, clean |
| No destructive git | No commit, stash, reset, clean, checkout, push, delete |

## Evidence Chain

| # | Evidence | Source |
|---|----------|--------|
| 1 | `D:\agent-acceptance` exists, is a git repo, branch `master`, HEAD `100a116` | `git rev-parse`, `git branch`, `git log` |
| 2 | `D:\dev-frame\agent-acceptance` exists, same commit `100a116`, SSH remote | `git log`, `git remote -v` |
| 3 | `D:\devFrame` does not exist on disk | `test -d` returned NOT_EXISTS |
| 4 | `D:\dev-frame` exists, contains 4 git repos, smoke test 3/3 PASS | `test -d`, `ls`, `smoke_report.txt` |
| 5 | `D:\test-frame` exists, independent git repo, 102 CodeGraph indexed files | `test -d`, `ls`, CodeGraph |
| 6 | RD2100 memory exists at `C:\Users\RD\.codex\memories\RD2100-memory\` | `test -d`, `ls` |
| 7 | README.md references `D:\devFrame\ai-workflow-hub` (path drift) | `Read` of README.md line 7, 11 |
| 8 | agent-acceptance CodeGraph DB exists (139KB) but files indexed = 0 | CodeGraph status query |

## Project Memory Status

| Memory Location | Status |
|-----------------|--------|
| `C:\Users\RD\.codex\memories\RD2100-memory\` | Active, rich (80+ memory files, ACTIVE.md, MEMORY.md, MEMORY-CALL-GUIDE.md) |
| `C:\Users\RD\.claude\projects\D--agent-acceptance\memory\` | Empty (directory exists, no files) |
| `C:\Users\RD\.claude\projects\D--devFrame\memory\` | Active (4 entries: detailed_reports, archon_windows_blocked, gate-tools-evaluation, MEMORY.md) |
| `C:\Users\RD\.claude\ACTIVE.md` | Exists (global active rules) |
| `C:\Users\RD\.claude\MEMORY-CALL-GUIDE.md` | Exists |
| `C:\Users\RD\.claude\MEMORY.md` | Does NOT exist at user level |

## Approval Chain

```
Batch A1 (read-only inventory)
  → Reviewer audit (local spot-checks)
    → Corrections identified (dirty count, CodeGraph status)
      → Batch A2 approved with constraints
        → This document (source-of-truth-decision.md)
```

## Next Steps

1. **Batch A2 complete**: All 4 docs written under `docs/agent-runtime/`
2. **Batch E (COMPLETED)**: Fixed README.md path drift (`D:\devFrame` → `D:\dev-frame`) — README.md lines 7,11 corrected
3. **Batch B1 (proposed)**: Consolidate agent-acceptance clones
4. **Batch C1 (proposed)**: Evaluate dev-frame git initialization
