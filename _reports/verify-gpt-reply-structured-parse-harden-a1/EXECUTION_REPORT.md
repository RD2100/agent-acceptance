# EXECUTION_REPORT — VERIFY-GPT-REPLY-STRUCTURED-PARSE-HARDEN-A1

**task_id**: `VERIFY-GPT-REPLY-STRUCTURED-PARSE-HARDEN-A1`
**authorized_by**: GPT-REVIEW-FLOW-REGRESSION-TEST-A1 R2 review
**executed_at**: 2026-06-09T12:10:00+08:00
**status**: COMPLETED

---

## Objective

Fix the known `task_id` regex first-match fragility in `verify_gpt_reply.py`. The verifier used `re.search(r"task_id:\s*(\S+)")` which returns the FIRST occurrence of `task_id:` in the reply. When the `next_task_authorization:` block contains its own `task_id:` before the reply footer's `task_id:`, the regex matches the wrong value, causing a false positive mismatch.

## Root Cause Analysis

The GPT reply format includes a `next_task_authorization:` block with a nested `task_id:` field:

```
next_task_authorization:
task_id: NEXT-TASK-ID        ← re.search matched THIS (wrong)
authorized: yes

run_id: ACTUAL_RUN_ID
task_id: ACTUAL-TASK-ID       ← Should match THIS (correct)

END_OF_GPT_RESPONSE
```

`re.search` returns the first match, which is inside the auth block.

## Fix Implementation

Added `_extract_field_outside_auth_block()` function to `verify_gpt_reply.py`:

1. **Locates** the `next_task_authorization:` block boundaries (start → next blank line or END_OF_GPT_RESPONSE)
2. **Iterates** all `field: value` matches at line start using `re.finditer`
3. **Skips** any match whose position falls inside the auth block
4. **Returns** the first match outside the auth block
5. **Fallback**: if all matches are inside the auth block, returns the last match

This approach works regardless of field ordering — whether the footer `task_id:` appears before or after the auth block.

## Changes Made

### scripts/verify_gpt_reply.py
- Added `_extract_field_outside_auth_block(content, field)` helper function
- Replaced `re.search` for `task_id` extraction with structured extraction
- Replaced `re.search` for `run_id` extraction with structured extraction (for consistency)

### tests/test_verify_gpt_reply.py
- Added `TestStructuredParse` test class with 4 new test cases:
  - `test_task_id_before_auth_block` — footer task_id before auth block
  - `test_task_id_after_auth_block` — footer task_id after auth block (original failure case)
  - `test_task_id_only_in_auth_block` — fallback when only auth block has task_id
  - `test_real_gpt_reply_format` — exact format from real GPT reply that caused false positive

## Test Results

```
============================= test session starts =============================
platform win32 -- Python 3.10.11, pytest-9.0.3, pluggy-1.6.0
collected 38 items

tests/test_verify_gpt_reply.py — 23 tests PASSED
tests/test_pre_gpt_review_gate.py — 15 tests PASSED

============================== 38 passed in 0.24s ==============================
```

**Result: 38/38 PASS**

## Verification Against Real Reply

Verified the fix resolves the actual false positive from GPT-REVIEW-FLOW-REGRESSION-TEST-A1 R2:

```
Before fix: valid=false, task_id mismatch (matched VERIFY-GPT-REPLY-STRUCTURED-PARSE-HARDEN-A1)
After fix:  valid=true,  task_id=GPT-REVIEW-FLOW-REGRESSION-TEST-A1, closure_ready=true
```

## Known Limitations

1. The auth block boundary detection uses blank line heuristic. If GPT formats the reply without blank lines between the auth block and footer, the extraction may not skip correctly. However, all observed GPT replies use blank line separation.
2. `overall_judgment` and `evidence_pack_reviewed` still use simple `re.search` since they don't appear inside the auth block and have no ambiguity.
