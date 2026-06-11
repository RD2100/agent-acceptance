Please review this closure pack attachment for task_id: GLOBAL-PROJECT-EVIDENCE-BINDING-A1
run_id: GLOBAL_EVIDENCE_BINDING_A1_20260608_233124

Required response format:
run_id: GLOBAL_EVIDENCE_BINDING_A1_20260608_233124
task_id: GLOBAL-PROJECT-EVIDENCE-BINDING-A1
overall_judgment: accepted | accepted_with_limitation | blocked | review_unverified
evidence_pack_reviewed: true|false
attachment_reviewed: true|false
required_fixes:
- ...
limitations:
- ...
next_task_authorization:
  task_id: ...
  authorized: yes|no
  execute_immediately: yes|no
  ask_before_starting: yes|no
END_OF_GPT_RESPONSE

Review focus:
1. Does the pack include explicit git status / changed-files evidence?
2. Does it independently show legacy PROJECT_HISTORY / HANDOFF / PASTE_BLOCK-related protected files were not deleted, moved, renamed, or rewritten in the current worktree/index?
3. Does it expand safety scanning over the generated closure pack contents rather than only selected files?
4. Does it preserve limitations: whole-project status partial/needs_more_evidence, production promotion not approved, 296 PASS unverified, accepted_with_limitation not flattened?
