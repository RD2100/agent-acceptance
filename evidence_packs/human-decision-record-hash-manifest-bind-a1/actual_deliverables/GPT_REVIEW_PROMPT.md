## GPT Review Prompt — HUMAN-DECISION-RECORD-HASH-MANIFEST-BIND-A1

You are reviewing the deliverables for task **HUMAN-DECISION-RECORD-HASH-MANIFEST-BIND-A1**.

### Task Definition

Per the authorization from HUMAN-DECISION-RECORD-EVIDENCE-BIND-A1: Add SHA-256 hash computation and verification for evidence files in human decision records. This enables tamper detection — if an evidence file is modified after the decision record is created, validation will fail.

### Deliverables

1. **`scripts/human_decision_record.py`** (~280 lines, modified)
   - `compute_evidence_hashes()` — SHA-256 for each evidence file
   - `verify_evidence_hashes()` — compare stored vs current hashes
   - `create_record()` enhanced: `repo_root` + `compute_hashes` params, stores hashes in `evidence_hashes` field, schema 1.1.0
   - `validate_record()` enhanced: verifies hash integrity, new `hash_verification` return field

2. **`tests/test_human_decision_record.py`** (52 tests, +7 new)
   - `TestHashVerification`: compute hashes, missing files, create with/without hashes, match/mismatch verification, backward compat

### Review Criteria

1. **Hash Integrity**: Does the hash computation/verification correctly detect tampering?
2. **Backward Compatibility**: Records without `evidence_hashes` should still validate (hash check skipped)
3. **Schema Evolution**: Is the version bump from 1.0.0 to 1.1.0 appropriate?
4. **Test Coverage**: Are 7 new tests sufficient?

### Expected Verdict Format

```
verdict: accepted | accepted_with_limitation | blocked | human_required
run_id: HUMAN_DECISION_RECORD_HASH_MANIFEST_BIND_A1_20260609T213000_RD
findings: [list key findings]
next_task_authorization: [next task or "none"]
---END_OF_GPT_RESPONSE---
```
