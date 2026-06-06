# GPT Review Prompt

Please review the attached PAPER-C2 evidence pack.

Required review focus:
- Verify the actual deliverables are included, especially the authorization/redaction gate contract, schemas, validator, fixtures, and tests.
- Verify positive synthetic authorization/redaction passes.
- Verify negative synthetic fixtures fail closed for missing, stale, ambiguous, and overbroad authorization and missing redaction.
- Verify the implementation remains synthetic-only and does not enable real-paper execution, external upload, live CDP, memory write with paper content, raw transcript, user private text, or real paper full text.
- Verify DIFF_PAPER_C2.patch, CHANGED_FILES, TEST_OUTPUT, and manifest/hash evidence are internally consistent.

Return a structured result with:
overall_judgment: accepted|blocked
reviewer_type: gpt
task_id: PAPER-C2
review_run_id: paper-c2-authorization-redaction-gate-review-v1
evidence_pack_reviewed: true
blocking_issues: []
required_fixes: []
next_task_authorization:
  authorized: yes|no
  execute_immediately: yes|no
  ask_before_starting: yes|no
