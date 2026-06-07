Please review the attached GROUP-01 evidence pack R2.

Review focus:
- Verify this pack isolates only GROUP-01 files from the dirty worktree.
- Verify no whole-dirty-tree staging/commit is implied.
- Verify no historical evidence mutation is included: no runs/*/POST_REVIEW_ROUTE.json changes and no HANDOFF_REPLY_V4.txt deletion.
- Verify archive hook changes, tools governance changes, memory outputs, paper validator residuals, tmp/cache noise, and root scratch files are excluded.
- Verify targeted GROUP-01 tests now use real assertions and no longer produce PytestReturnNotNoneWarning in GROUP-01 test files.
- Verify full tests pass; note any remaining warnings are outside GROUP-01 scope.
- Verify bypass evidence is PASS for GROUP-01 selected files and scoped appropriately.
- Verify the pack is not summary-only and includes actual deliverables.
- Verify the backfill nature is clearly stated and not misrepresented as a new feature.

Return structured output:
overall_judgment: accepted|blocked
reviewer_type: gpt
task_id: GROUP-01
evidence_pack_reviewed: true
blocking_issues: []
required_fixes: []
next_task_authorization:
  authorized: yes|no
  execute_immediately: yes|no
  ask_before_starting: yes|no

End with END_OF_GPT_RESPONSE.
