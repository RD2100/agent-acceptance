## GPT Review Prompt — HUMAN-DECISION-RECORD-MANIFEST-STRICT-BIND-A1

You are reviewing the deliverables for task **HUMAN-DECISION-RECORD-MANIFEST-STRICT-BIND-A1**.

### Task Definition

Per the authorization from HUMAN-DECISION-RECORD-MANIFEST-BIND-A1 R2 (accepted_with_limitation): Address 5 limitations in `human_decision_record.py`:
1. Strict filename matching for PACK_MANIFEST.md (exact `Path.name`, not substring)
2. Make `pack_manifest_file_exists` fail-closed when repo_root provided
3. Make `pack_manifest_hash_bound` fail-closed when repo_root provided
4. Add hash completeness check (all evidence_files must have evidence_hashes entries)
5. Bump schema version

### Deliverables

1. **`scripts/human_decision_record.py`** (~310 lines, modified)
   - Schema version: 1.1.0 → 1.2.0
   - Manifest binding: `Path(ef).name == "PACK_MANIFEST.md"` (exact filename match)
   - `pack_manifest_file_exists`: enforced as error when repo_root provided and manifest file not found
   - `pack_manifest_hash_bound`: enforced as error when repo_root provided and manifest not in evidence_hashes
   - New `hash_completeness` field: checks all evidence_files have hash entries when evidence_hashes non-empty

2. **`tests/test_human_decision_record.py`** (69 tests, +10 new)
   - TestStrictManifestBinding (6): substring rejected, case-sensitive, subdirectory OK, file missing fails, not hash-bound fails, full pass
   - TestHashCompleteness (4): all present complete, missing hash entry fails, no hashes skips, schema version 1.2.0

### Review Criteria

1. **Strict Filename Matching**: Is `"PACK_MANIFEST"` substring matching replaced with exact `Path.name == "PACK_MANIFEST.md"`?
2. **Fail-Closed Enforcement**: Are `pack_manifest_file_exists` and `pack_manifest_hash_bound` enforced as errors when repo_root provided?
3. **Hash Completeness**: Does the new check ensure all evidence_files have hash entries?
4. **Backward Compatibility**: Do existing tests still pass?
5. **Test Coverage**: Are 10 new tests sufficient?

### Expected Verdict Format

```
verdict: accepted | accepted_with_limitation | blocked | human_required
run_id: HUMAN_DECISION_RECORD_MANIFEST_STRICT_BIND_A1_20260609T215000_RD
findings: [list key findings]
next_task_authorization: [next task or "none"]
---END_OF_GPT_RESPONSE---
```
