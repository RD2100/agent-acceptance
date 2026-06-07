Please review the attached WorkQueue closure pack.

Review focus:
- Verify specialized batch JSONs exist for cleanup/recovery/release.
- Verify corresponding queues point to those specialized active batch files.
- Verify direct specialized batch runs pass.
- Verify cleanup/recovery/release queue executions pass after the runner exit propagation fix.
- Verify this closes the WorkQueue follow-on path without broadening into unrelated governance cleanup.

Return structured output:
overall_judgment: accepted|blocked
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
