task_id: t-workqueue-specialized-batches-20260607
review_type: blocked_scope_reassessment
status: ready_for_review
final_status: ready_for_review

# WorkQueue Specialized Batches Review Pack

This pack captures the current specialized-batch state.

What is fixed:
- cleanup / recovery / release queues no longer reference the shared batch-local-quality.json.
- all three specialized batch JSON files exist.
- all three specialized batches pass when executed directly.

What remains blocked:
- recovery-regression.queue.json and release-readiness.queue.json still fail when executed through Run-WorkQueue.ps1.
- The direct batch outputs and queue outputs diverge, which suggests a remaining runner/exit propagation defect outside the current task boundary.

Request:
- Review whether the correct next task should expand scope to include scripts/Run-WorkQueue.ps1 (and, if needed, Run-Batch.ps1) to resolve queue-level pass/fail propagation.
