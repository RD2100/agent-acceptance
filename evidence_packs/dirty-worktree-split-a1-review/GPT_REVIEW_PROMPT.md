Please review the attached DIRTY-WORKTREE-SPLIT-A1 staging plan evidence pack in the same conversation thread.

This is a review of the split plan generated from your DIRTY-WORKTREE-REVIEW-20260607 triage result, not a code implementation closure request.

Review focus:
- Verify the staging plan follows the prior GPT triage result.
- Verify it blocks whole-dirty-tree commits.
- Verify it protects historical evidence: no direct commits of HANDOFF_REPLY_V4.txt deletion or runs/*/POST_REVIEW_ROUTE.json rewrites.
- Verify it excludes .tmpconfig, .tmpdata, __pycache__, pyc, root scratch GPT files, and dirty review pack content from normal commits.
- Verify the recommended first group GROUP-01 is a reasonable next execution unit.
- Identify any missing guardrails before starting GROUP-01.

Return structured output:
overall_judgment: accepted|blocked|triage_only
reviewer_type: gpt
task_id: DIRTY-WORKTREE-SPLIT-A1
evidence_pack_reviewed: true
review_scope: staging_plan_review
blocking_issues: []
required_fixes: []
next_task_authorization:
  authorized: yes|no
  execute_immediately: yes|no
  ask_before_starting: yes|no
  recommended_task_id: GROUP-01|other

End with END_OF_GPT_RESPONSE.
