# WorkQueue Index

| Queue | File | Purpose | Run When | Review Focus |
|-------|------|---------|----------|-------------|
| local-quality | `local-quality.queue.json` | Base quality gate: shared active Tier 0 local quality batch (10 checks) | Every round, default first | All green |
| docs-quality | `docs-quality.queue.json` | Doc presence: release pack, runbook, recovery, powershell-acceptance, workqueue, status-machine | Doc changes, handoff | Missing/stale docs |
| recovery-regression | `recovery-regression.queue.json` | Dedicated active recovery-regression batch: recovery docs, closure/chain tests, existing run evidence | Recovery code changes | Evidence chain |
| release-readiness | `release-readiness.queue.json` | Dedicated active release-readiness batch: release docs, compile checks, dispatch/runner policy tests | Pre-release | Config/doc consistency |
| cleanup-dryrun | `cleanup-dryrun.queue.json` | Dedicated active cleanup dry-run batch: retention docs, queue safety, self-test | Cleanup code changes | No false delete candidates |

## Default Entry

```powershell
# Serial (default, safe)
powershell -ExecutionPolicy Bypass -File scripts/Run-QueueGroup.ps1 `
  -QueueFiles agent-workqueue/local-quality.queue.json,agent-workqueue/docs-quality.queue.json,agent-workqueue/recovery-regression.queue.json,agent-workqueue/release-readiness.queue.json,agent-workqueue/cleanup-dryrun.queue.json

# Parallel (3 parallel-safe queues)
powershell -ExecutionPolicy Bypass -File scripts/Run-QueueGroup.ps1 `
  -Parallel -MaxParallel 2 `
  -QueueFiles agent-workqueue/docs-quality.queue.json,agent-workqueue/release-readiness.queue.json,agent-workqueue/cleanup-dryrun.queue.json
```

## Parallel Policy

| Queue | Parallel Safe | Reason |
|-------|--------------|--------|
| docs-quality | yes | Read-only doc checks |
| release-readiness | yes | Read-only quality checks |
| cleanup-dryrun | yes | Dry-run, no delete |
| local-quality | conditional | Multiple suites; prefer serial or limit concurrency |
| recovery-regression | no | Recovery fixtures; serial required |

## For Code Agent

Default: serial Run-QueueGroup with all 5 queues.
Only use -Parallel with explicitly marked parallel-safe queues (docs, release, cleanup).

## For Reviewer
