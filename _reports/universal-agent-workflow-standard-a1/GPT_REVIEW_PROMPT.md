## GPT Review Prompt — UNIVERSAL-AGENT-WORKFLOW-STANDARD-A1 R4

You are reviewing the R4 deliverables for task **UNIVERSAL-AGENT-WORKFLOW-STANDARD-A1**.

**Task ID**: {{TASK_ID}}
**Run ID**: {{RUN_ID}}

### R3 Blocking Issues Fixed

1. **PACK_MANIFEST.md missing run_id field now fails**: When PACK_MANIFEST.md exists but has no `run_id` field, the validator now adds an error and returns `consistent=false` (line 128 in validate_run_id_consistency.py). Previously it only set `manifest_run_id_found=false` without adding an error.

2. **New test added**: `test_manifest_run_id_field_missing` — creates a PACK_MANIFEST.md with a `task_id` field but no `run_id` field, asserts the validator returns `consistent=false` with a "run_id field not found" error.

### R4 Deliverables

1. **scripts/validate_run_id_consistency.py** (~172 lines)
   - All R1 blocking issues fixed ({{RUN_ID}}, {{TASK_ID}}, zip, manifest run_id, empty run_id)
   - All R2 blocking issues fixed (missing PACK_MANIFEST.md detection)
   - All R3 blocking issues fixed (manifest run_id field missing now fails)
   - Multi-level evidence_packs directory search (parent.parent and parent)
   - 9 distinct error checks, all fail-closed per AWSP v1.0.0

2. **tests/test_validate_run_id_consistency.py** (14 tests)
   - All 14 tests pass individually
   - Covers: consistent, missing run_id.txt, hardcoded run_id, R1 mismatch, GPT reply mismatch/match, missing {{RUN_ID}}, missing {{TASK_ID}}, missing zip, manifest mismatch, pack filename mismatch, empty run_id, missing PACK_MANIFEST.md, manifest run_id field missing

3. **docs/AGENT_WORKFLOW_STANDARD.md** — AWSP v1.0.0 protocol definition

### Validation Results

- **Target tests**: 14 passed / 14 total
- **Full suite**: 505 passed / 505 total
- **Run-ID consistency validator**: All 9 checks implemented and tested

### Review Criteria

1. All R3 blocking issues resolved? (manifest run_id field missing → error added + test added)
2. All edge cases now covered with fail-closed behavior?
3. 14 tests sufficient for the validator's scope?

### Expected Verdict Format

```
verdict: accepted | accepted_with_limitation | blocked | human_required
run_id: {{RUN_ID}}
findings: [list key findings]
next_task_authorization: [next task or "none"]
---END_OF_GPT_RESPONSE---
```
