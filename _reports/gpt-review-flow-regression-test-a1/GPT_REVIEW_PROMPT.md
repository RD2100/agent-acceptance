# GPT Review Prompt — GPT-REVIEW-FLOW-REGRESSION-TEST-A1

**task_id**: `GPT-REVIEW-FLOW-REGRESSION-TEST-A1`
**run_id**: `{{RUN_ID}}`
**generated_at**: `{{TIMESTAMP}}`

---

You are reviewing the deliverables for task `GPT-REVIEW-FLOW-REGRESSION-TEST-A1` (hardening plan P1-2, Task 4).

## Task Objective

Create a regression test suite for the GPT review flow guard scripts (`verify_gpt_reply.py`, `pre_gpt_review_gate.py`, `evidence_pack_linter.py`). The test suite must cover all specified test cases in hardening plan Section 5.5, including valid replies, missing fields, verdict validation, blocked verdicts, task_id matching, edge cases, evidence pack linting, and pre-submission gate checks.

## Expected Deliverables

1. `tests/conftest.py` — Shared pytest fixtures for all regression tests
2. `tests/test_verify_gpt_reply.py` — 18 test cases for verify_gpt_reply.py (VRT-001 through VRT-012 + extras)
3. `tests/test_pre_gpt_review_gate.py` — 15 test cases for pre_gpt_review_gate.py + evidence_pack_linter.py (PGT-001 through PGT-006 + extras)
4. `EXECUTION_REPORT.md` — Execution report with full test output

## Review Criteria

Please evaluate:

1. **Test Coverage**: Do the tests cover all VRT and PGT cases specified in Section 5.5?
2. **Fixture Quality**: Are fixtures well-structured, reusable, and correctly simulating real GPT reply formats?
3. **Assertion Accuracy**: Do assertions correctly verify expected PASS/FAIL behavior for each test case?
4. **Edge Case Handling**: Are Unicode content, whitespace variations, and boundary conditions tested?
5. **Known Limitation Documentation**: Are unimplemented test cases (VRT-008, PGT-003, PGT-005) clearly documented with explanations?
6. **Code Quality**: Is the test code clean, well-documented, and following pytest best practices?
7. **task_id Regex Workaround**: Are fixtures properly ordered to work around the known `re.search` first-match limitation in `verify_gpt_reply.py`?

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
task_id: GPT-REVIEW-FLOW-REGRESSION-TEST-A1

END_OF_GPT_RESPONSE
