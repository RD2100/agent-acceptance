# Command Cheatsheet

Copy-paste verification commands. All run from the **target project root**.

## Self-Test

Verify the constraint pack itself is intact:

```powershell
powershell -ExecutionPolicy Bypass -File D:\agent-acceptance\scripts\Test-WorkQueue.ps1
```

**Expected**: `PASS=26 FAILED=0 TOTAL=26`. Exit code 0.

## Single Batch

Run one batch task file:

```powershell
powershell -ExecutionPolicy Bypass -File D:\agent-acceptance\scripts\Run-Batch.ps1 -TaskFile D:\agent-acceptance\scripts\examples\batch-local-quality.json
```

Replace `batch-local-quality.json` with your project's batch file.

**Exit codes**: 0 = all passed, 1 = blocked/escalated, 2 = failed.

## Single Queue

Run one queue item:

```powershell
powershell -ExecutionPolicy Bypass -File D:\agent-acceptance\scripts\Run-WorkQueue.ps1 -QueueFile D:\agent-acceptance\agent-workqueue\local-quality.queue.json
```

## Queue Group (Serial)

Run multiple queues one after another:

```powershell
powershell -ExecutionPolicy Bypass -Command "& 'D:\agent-acceptance\scripts\Run-QueueGroup.ps1' -QueueFiles @('D:\agent-acceptance\agent-workqueue\local-quality.queue.json','D:\agent-acceptance\agent-workqueue\docs-quality.queue.json')"
```

## Queue Group (Parallel-safe)

Run queues that are safe to run in parallel:

```powershell
powershell -ExecutionPolicy Bypass -Command "& 'D:\agent-acceptance\scripts\Run-QueueGroup.ps1' -Parallel -MaxParallel 2 -QueueFiles @('D:\agent-acceptance\agent-workqueue\docs-quality.queue.json','D:\agent-acceptance\agent-workqueue\release-readiness.queue.json')"
```

Only mark these queues as parallel-safe:
- `docs-quality` — read-only doc checks
- `release-readiness` — read-only quality checks
- `cleanup-dryrun` — dry-run, no delete

## Smoke Test

Quick project health check:

```powershell
powershell -ExecutionPolicy Bypass -File D:\agent-acceptance\scripts\Run-Smoke.ps1 -ProjectPath .
```

## All Queues (Full Verification)

Run all registered queues:

```powershell
powershell -ExecutionPolicy Bypass -Command "& 'D:\agent-acceptance\scripts\Run-AllQueues.ps1'"
```

## Report Output Locations

| Runner | Report Path |
|--------|------------|
| `Run-Batch.ps1` | `runs/powershell-acceptance/batch-<id>/batch-report.md` |
| `Run-WorkQueue.ps1` | `runs/powershell-acceptance/workqueue/<queue-id>/` |
| `Run-QueueGroup.ps1` | `runs/powershell-acceptance/workqueue-groups/group-<timestamp>/group-report.md` |
| `Run-AllQueues.ps1` | `runs/powershell-acceptance/workqueue/all-queues/all-queues-report.md` |
| `Run-Smoke.ps1` | `%TEMP%\acceptance-smoke-<timestamp>\acceptance-report.md` |
| `Test-WorkQueue.ps1` | stdout only |

## Exit Code Quick Reference

| Code | Meaning | Action |
|------|---------|--------|
| 0 | All passed | Proceed |
| 1 | Blocked / escalated | Generate summary, escalate to reviewer |
| 2 | Failed | Stop queue, report all failed items |

## Project-Specific Queues

When you add your own queue to `agent-workqueue/`, `Test-WorkQueue.ps1` auto-discovers it. The self-test count increases accordingly. The pilot project confirmed: one new queue → 5 additional checks (PASS=26 → PASS=31).

Run your project queue:
```powershell
powershell -ExecutionPolicy Bypass -File D:\agent-acceptance\scripts\Run-WorkQueue.ps1 -QueueFile agent-workqueue\project-quality.queue.json
```

## Common Patterns

**Default agent flow** (after any code change):
```powershell
powershell -ExecutionPolicy Bypass -File D:\agent-acceptance\scripts\Test-WorkQueue.ps1
```

**Pre-commit check** (Tier 0 only):
```powershell
powershell -ExecutionPolicy Bypass -File D:\agent-acceptance\scripts\Run-Batch.ps1 -TaskFile D:\agent-acceptance\scripts\examples\batch-local-quality.json
```

**Pre-release check** (aggregate queues):
```powershell
powershell -ExecutionPolicy Bypass -Command "& 'D:\agent-acceptance\scripts\Run-QueueGroup.ps1' -QueueFiles @('D:\agent-acceptance\agent-workqueue\local-quality.queue.json','D:\agent-acceptance\agent-workqueue\docs-quality.queue.json','D:\agent-acceptance\agent-workqueue\release-readiness.queue.json')"
```
