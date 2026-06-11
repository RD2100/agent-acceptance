## GPT Review Prompt — HUMAN-DECISION-RECORD-EVIDENCE-BIND-A1

You are reviewing the deliverables for task **HUMAN-DECISION-RECORD-EVIDENCE-BIND-A1**.

### Task Definition

Per the authorization from HUMAN-DECISION-RECORD-INTEGRATE-T10-A1: Add evidence file existence verification to `human_decision_record.py` so that `validate_record()` checks whether referenced evidence files actually exist on disk.

### Deliverables

1. **`scripts/human_decision_record.py`** (~225 lines, modified)
   - `validate_record()` now accepts optional `repo_root` parameter
   - When provided, checks each evidence file's existence on disk
   - Supports relative (resolved against repo_root) and absolute paths
   - New return field `evidence_binding`: {checked, all_exist, missing, found}
   - Missing files produce explicit error messages and fail validation

2. **`tests/test_human_decision_record.py`** (45 tests, +6 new)
   - `TestEvidenceBinding` (6 tests): no repo_root skips, all exist pass, missing fails, all missing fails, absolute path, empty list skips

### Review Criteria

1. **Evidence Binding Correctness**: Does the binding correctly resolve and verify evidence file paths?
2. **Backward Compatibility**: Does the addition of `repo_root` parameter maintain backward compatibility?
3. **Error Reporting**: Are missing evidence files reported with clear, actionable error messages?
4. **Test Coverage**: Are 6 new tests sufficient for the evidence binding feature?

### Expected Verdict Format

```
verdict: accepted | accepted_with_limitation | blocked | human_required
run_id: HUMAN_DECISION_RECORD_EVIDENCE_BIND_A1_20260609T212000_RD
findings: [list key findings]
next_task_authorization: [next task or "none"]
---END_OF_GPT_RESPONSE---
```
