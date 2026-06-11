## GPT Review Prompt — HUMAN-DECISION-RECORD-MANIFEST-CONTENT-CROSSCHECK-A1

You are reviewing the deliverables for task **HUMAN-DECISION-RECORD-MANIFEST-CONTENT-CROSSCHECK-A1**.

### Task Definition

Per the authorization from HUMAN-DECISION-RECORD-HASH-EXTRA-ENTRY-HARDEN-A1 R1 (accepted_with_limitation): Address the limitation that PACK_MANIFEST.md content was not parsed to verify that all evidence_files are actually listed in the manifest. This is a manifest content cross-check.

### Deliverables

1. **`scripts/human_decision_record.py`** (~400 lines, modified)
   - New `parse_manifest_paths()`: extracts backtick-wrapped paths from markdown table rows
   - New `crosscheck_manifest_content()`: reads PACK_MANIFEST.md on disk, parses paths, checks all evidence_files listed
   - `_normalize_path()`: cross-platform path normalization (backslash→forward slash, lowercase)
   - `validate_record()` returns new `manifest_crosscheck` field
   - Crosscheck enforced when repo_root provided + manifest has parseable table rows

2. **`tests/test_human_decision_record.py`** (78 tests, +5 new)
   - TestManifestContentCrosscheck (5):
     - All evidence listed → pass
     - Extra file not listed → fail
     - No repo_root → skip
     - Manifest file missing → skip
     - Backslash paths normalized

### Review Criteria

1. **Content Parsing**: Does `parse_manifest_paths()` correctly extract paths from markdown tables?
2. **Cross-Platform**: Does normalization handle Windows backslash paths?
3. **Fail-Closed**: Are unlisted evidence files flagged as errors?
4. **Graceful Degradation**: Is the check skipped when manifest has no table rows?
5. **Backward Compatibility**: Do existing 73 tests still pass?
6. **Test Coverage**: Are 5 new tests sufficient?

### Expected Verdict Format

```
verdict: accepted | accepted_with_limitation | blocked | human_required
run_id: HUMAN_DECISION_RECORD_MANIFEST_CONTENT_CROSSCHECK_A1_20260609T215000_RD
findings: [list key findings]
next_task_authorization: [next task or "none"]
---END_OF_GPT_RESPONSE---
```
