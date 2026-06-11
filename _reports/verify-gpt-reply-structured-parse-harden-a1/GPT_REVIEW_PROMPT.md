# GPT Review Prompt — VERIFY-GPT-REPLY-STRUCTURED-PARSE-HARDEN-A1

**task_id**: `VERIFY-GPT-REPLY-STRUCTURED-PARSE-HARDEN-A1`
**run_id**: `{{RUN_ID}}`
**generated_at**: `{{TIMESTAMP}}`

---

You are reviewing the deliverables for task `VERIFY-GPT-REPLY-STRUCTURED-PARSE-HARDEN-A1` (authorized by GPT-REVIEW-FLOW-REGRESSION-TEST-A1 R2 review).

## Task Objective

Fix the known `task_id` regex first-match fragility in `verify_gpt_reply.py`. The verifier used `re.search(r"task_id:\s*(\S+)")` which returns the FIRST occurrence of `task_id:` in the reply, causing false positive mismatches when `next_task_authorization:` block contains its own `task_id:` before the footer's `task_id:`.

## Expected Deliverables

1. `scripts/verify_gpt_reply.py` — Updated with `_extract_field_outside_auth_block()` structured extraction
2. `tests/test_verify_gpt_reply.py` — Updated with `TestStructuredParse` test class (4 new cases)
3. `EXECUTION_REPORT.md` — Execution report with test output and verification evidence

## Review Criteria

Please evaluate:

1. **Correctness**: Does the structured extraction correctly skip `task_id:` inside `next_task_authorization:` block?
2. **Backward Compatibility**: Do all existing 34 tests still pass?
3. **Edge Cases**: Are all ordering scenarios covered (task_id before auth, after auth, only in auth)?
4. **Real-world Verification**: Does the fix resolve the actual false positive from GPT-REVIEW-FLOW-REGRESSION-TEST-A1 R2?
5. **Code Quality**: Is the implementation clean, well-documented, and minimal?
6. **Test Coverage**: Are the new `TestStructuredParse` cases comprehensive?
7. **Limitation Documentation**: Are remaining limitations (blank line heuristic) clearly documented?

## Evidence Pack Manifest

{{PACK_MANIFEST}}

## Response Format

Please respond with:
1. `overall_judgment`: accepted | accepted_with_limitation | blocked | human_required
2. `evidence_pack_reviewed: true`
3. `attachment_reviewed: true`
4. `blocking_issues`: list or "none"
5. `required_fixes`: list or "none"
6. `limitations`: list (if any)
7. `next_task_authorization`: { task_id, authorized, execute_immediately, ask_before_starting }

run_id: {{RUN_ID}}
task_id: VERIFY-GPT-REPLY-STRUCTURED-PARSE-HARDEN-A1

END_OF_GPT_RESPONSE
