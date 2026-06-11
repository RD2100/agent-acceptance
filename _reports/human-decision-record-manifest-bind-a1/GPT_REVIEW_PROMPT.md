## GPT Review Prompt — HUMAN-DECISION-RECORD-MANIFEST-BIND-A1

You are reviewing the deliverables for task **HUMAN-DECISION-RECORD-MANIFEST-BIND-A1**.

### Task Definition

Per the authorization from HUMAN-DECISION-RECORD-CLI-T10-HASH-INTEGRATE-A1: Harden `human_decision_record.py` by adding: (1) empty task_id rejection at create time, (2) manifest binding verification that PACK_MANIFEST.md is referenced in evidence_files, (3) full repo_root propagation through T10 guard chain.

### Deliverables

1. **`scripts/human_decision_record.py`** (~310 lines, modified)
   - `create_record()` rejects empty/whitespace/None task_id
   - `validate_record()` returns `manifest_binding` field checking PACK_MANIFEST in evidence_files
   - `repo_root` propagation maintained

2. **`tests/test_human_decision_record.py`** (59 tests, +5 new)
   - TestTaskIdValidation (3): empty, whitespace, None
   - TestManifestBinding (2): included/not-included

### Review Criteria

1. **Task ID Validation**: Is empty task_id properly rejected at creation time?
2. **Manifest Binding**: Does the manifest_binding check correctly detect PACK_MANIFEST presence?
3. **Fail-Closed**: Are all validation paths fail-closed?
4. **Test Coverage**: Are 5 new tests sufficient?

### Expected Verdict Format

```
verdict: accepted | accepted_with_limitation | blocked | human_required
run_id: HUMAN_DECISION_RECORD_MANIFEST_BIND_A1_20260609T215000_RD
findings: [list key findings]
next_task_authorization: [next task or "none"]
---END_OF_GPT_RESPONSE---
```
