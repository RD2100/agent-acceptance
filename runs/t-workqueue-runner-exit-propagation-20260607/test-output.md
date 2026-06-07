# Test Output

## 1. Queue executions after runner fix
- Command: `powershell -ExecutionPolicy Bypass -File scripts/Run-WorkQueue.ps1 -QueueFile agent-workqueue/cleanup-dryrun.queue.json`
- Result: PASS
- Evidence: runs/powershell-acceptance/workqueue/cleanup-dryrun-queue/queue-report.md

- Command: `powershell -ExecutionPolicy Bypass -File scripts/Run-WorkQueue.ps1 -QueueFile agent-workqueue/recovery-regression.queue.json`
- Result: PASS
- Evidence: runs/powershell-acceptance/workqueue/recovery-regression-queue/queue-report.md

- Command: `powershell -ExecutionPolicy Bypass -File scripts/Run-WorkQueue.ps1 -QueueFile agent-workqueue/release-readiness.queue.json`
- Result: PASS
- Evidence: runs/powershell-acceptance/workqueue/release-readiness-queue/queue-report.md

## 2. Conclusion
- Queue-level exit/result propagation now matches direct batch outcomes.
- The queue runner no longer reports false FAILED for recovery/release when the underlying specialized batches pass.
- The WorkQueue specialized-batches follow-on can now be completed without expanding scope further.
