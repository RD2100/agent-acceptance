Please review the attached WorkQueue specialized-batches evidence pack.

Review focus:
- Verify specialized batch JSONs now exist for cleanup, recovery, and release.
- Verify queue JSONs now point to specialized active batch files instead of the shared local-quality batch.
- Verify direct batch runs pass.
- Verify cleanup queue passes, while recovery/release queue execution still fails.
- Determine whether the correct next task should expand scope to scripts/Run-WorkQueue.ps1 (and possibly Run-Batch.ps1) for queue-level exit/result propagation.

Return structured output:
overall_judgment: accepted|blocked|human_required
reviewer_type: gpt
task_id: t-workqueue-specialized-batches-20260607
evidence_pack_reviewed: true
blocking_issues: []
required_fixes: []
next_task_authorization:
  authorized: yes|no
  execute_immediately: yes|no
  ask_before_starting: yes|no
  recommended_task_id: ""

End with END_OF_GPT_RESPONSE.
