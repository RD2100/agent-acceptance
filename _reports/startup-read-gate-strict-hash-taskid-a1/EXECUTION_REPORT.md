## STARTUP-READ-GATE-STRICT-HASH-TASKID-A1 — Execution Report

| Field | Value |
|-------|-------|
| **task_id** | STARTUP-READ-GATE-STRICT-HASH-TASKID-A1 |
| **run_id** | STARTUP_READ_GATE_STRICT_HASH_TASKID_A1_20260609T121957_RD |
| **status** | complete |
| **generated_at** | 2026-06-09T20:19:57+08:00 |
| **author** | Agent (QoderWork) |
| **parent_task** | STARTUP-READ-GATE-ENFORCE-A1 (GPT-authorized) |

### Scope

Address limitations identified in STARTUP-READ-GATE-ENFORCE-A1 GPT R1 review by adding strict mode to `startup_read_gate.py`:

1. P0/fail_closed files without summary_hash in proof → error in strict mode
2. Non-existent fail_closed files with proof hash → error in strict mode
3. task_id mismatch → error in strict mode (was warning only)
4. coverage_ratio uses matched required reads / must_read_count (was total proof entries / must_read_count)

### Implementation Summary

**Modified: `scripts/startup_read_gate.py`** (~350 lines, from ~253 lines)

Added:
- `strict: bool = False` parameter to `gate()` function
- `--strict` CLI flag
- `_normalize_path()` helper for cross-platform path matching
- `_find_proof_entry()` closure for normalized path lookup
- Step 5c: strict hash presence check for P0/fail_closed must_read files
- Step 6 enhancement: non-existent fail_closed files with proof hash → error in strict mode
- Step 8 enhancement: task_id mismatch promoted to error in strict mode
- Step 9 rewrite: coverage_ratio = matched_required / must_read_count

**Modified: `tests/test_startup_read_gate.py`** (19 tests, from 12)

Added:
- `TestGateExtraChecks::test_coverage_ratio_with_extra_proof_entries` — verifies matched-only coverage
- `TestStrictMode` class (6 tests):
  - `test_strict_task_id_mismatch_becomes_error`
  - `test_strict_p0_missing_hash_is_error`
  - `test_strict_p1_without_hash_is_ok`
  - `test_strict_fail_closed_nonexistent_file`
  - `test_strict_with_valid_p0_hash_passes`
  - `test_strict_coverage_ratio_capped_at_one`

### Test Results

```
tests/test_startup_read_gate.py: 19 passed (12 existing + 7 new)
Full suite: 366 passed (359 existing + 7 new)
```

### Coverage Matrix

| Capability | Status | Verified By |
|---|---|---|
| Strict task_id mismatch → error | Implemented | test_strict_task_id_mismatch_becomes_error |
| P0/fail_closed missing hash → error | Implemented | test_strict_p0_missing_hash_is_error |
| P1 without hash OK in strict | Implemented | test_strict_p1_without_hash_is_ok |
| Non-existent fail_closed → error | Implemented | test_strict_fail_closed_nonexistent_file |
| Valid P0 hash passes strict | Implemented | test_strict_with_valid_p0_hash_passes |
| Coverage matched/must_read | Implemented | test_strict_coverage_ratio_capped_at_one, test_coverage_ratio_with_extra_proof_entries |
| Backward compat (non-strict) | Preserved | All 12 existing tests still pass |

### Known Limitations

1. Gate not yet integrated into state machine runtime (standalone component)
2. `startup_timestamp` freshness check not yet implemented (mentioned in plan §5.7.2 item 4)
3. No integration with `pre_gpt_review_gate.py` yet (mentioned in plan §5.7.3)
4. Strict mode is opt-in via `--strict` flag — should be enabled by default for formal task workflows
5. `_find_proof_entry` closure defined inside `gate()` — could be extracted for reuse
