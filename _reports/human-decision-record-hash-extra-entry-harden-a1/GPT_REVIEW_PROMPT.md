## GPT Review Prompt — HUMAN-DECISION-RECORD-HASH-EXTRA-ENTRY-HARDEN-A1

You are reviewing the deliverables for task **HUMAN-DECISION-RECORD-HASH-EXTRA-ENTRY-HARDEN-A1**.

### Task Definition

Per the authorization from HUMAN-DECISION-RECORD-MANIFEST-STRICT-BIND-A1 R1 (accepted_with_limitation): Address the limitation that `hash_completeness` only checked `evidence_files → evidence_hashes` but not `evidence_hashes → evidence_files`. Orphaned hash entries (keys in evidence_hashes not in evidence_files) could indicate tampering or data corruption.

### Deliverables

1. **`scripts/human_decision_record.py`** (~320 lines, modified)
   - `hash_completeness` now includes `orphaned_hash_entries` list
   - Bidirectional check: evidence_files↔evidence_hashes
   - `complete` requires both missing=[] AND orphaned=[]
   - Orphaned entries produce validation errors (fail-closed)

2. **`tests/test_human_decision_record.py`** (73 tests, +4 new)
   - TestOrphanedHashEntries (4):
     - Single orphaned entry detected
     - Multiple orphaned entries detected
     - Clean record has no orphaned entries
     - Both missing AND orphaned detected simultaneously

### Review Criteria

1. **Bidirectional Hash Check**: Does hash_completeness now check both directions?
2. **Fail-Closed**: Are orphaned entries enforced as errors?
3. **Backward Compatibility**: Do existing 69 tests still pass?
4. **Test Coverage**: Are 4 new tests sufficient for the orphaned hash scenario?
5. **Tamper Detection**: Can this detect a scenario where evidence_files were removed but hashes remain?

### Expected Verdict Format

```
verdict: accepted | accepted_with_limitation | blocked | human_required
run_id: HUMAN_DECISION_RECORD_HASH_EXTRA_ENTRY_HARDEN_A1_20260609T215000_RD
findings: [list key findings]
next_task_authorization: [next task or "none"]
---END_OF_GPT_RESPONSE---
```
