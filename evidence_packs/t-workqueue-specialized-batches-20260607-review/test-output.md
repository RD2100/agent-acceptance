# Test Output

## 1. WorkQueue self-test
- Command: `powershell -ExecutionPolicy Bypass -File scripts/Test-WorkQueue.ps1`
- Result: PASS
- Evidence: runs/powershell-acceptance/Test-WorkQueue stdout

## 2. Specialized batch executions
- `batch-cleanup-dryrun.json`: PASS
- `batch-recovery-regression.json`: PASS
- `batch-release-readiness.json`: PASS

## 3. Queue executions
- `cleanup-dryrun.queue.json`: PASS
- `recovery-regression.queue.json`: FAILED (exit 2)
- `release-readiness.queue.json`: FAILED (exit 2)

## 4. Key finding
- Specialized batch files now exist and run successfully.
- Queue references for cleanup/recovery/release now point to dedicated active batch files.
- The remaining blocker is queue-runner behavior: queue item `stdout.log` and `exit.code` for recovery/release still reflect failed exit 2 even when the corresponding batch runs pass on direct invocation.
- This indicates the next task should expand scope to `scripts/Run-WorkQueue.ps1` (and possibly batch/exit propagation behavior) rather than continue editing batch JSON only.
