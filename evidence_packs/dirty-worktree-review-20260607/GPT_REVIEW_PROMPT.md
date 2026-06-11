Please review the attached dirty-worktree evidence pack for agent-acceptance.

This is not a closure acceptance request. It is a triage/review request for current uncommitted modifications.

Review focus:
- Determine which tracked changes and selected untracked files appear coherent and should be grouped into tasks.
- Identify stale/noisy/generated files that should not be committed.
- Identify blockers: missing tests, unsafe governance edits, evidence gaps, privacy/security risks, or dirty-baseline hazards.
- Recommend the next concrete action order.
- Pay special attention to dirty baseline handling: do not ask to delete historical evidence; propose safe commit grouping or further evidence generation.

Return structured output:
overall_judgment: accepted|blocked|triage_only
reviewer_type: gpt
task_id: DIRTY-WORKTREE-REVIEW-20260607
evidence_pack_reviewed: true
review_scope: dirty_worktree_triage
blocking_issues: []
recommended_groups: []
required_fixes: []
next_task_authorization:
  authorized: yes|no
  execute_immediately: yes|no
  ask_before_starting: yes|no

End with END_OF_GPT_RESPONSE.
