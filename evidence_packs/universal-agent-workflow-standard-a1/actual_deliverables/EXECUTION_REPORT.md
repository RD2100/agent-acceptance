# Execution Report: UNIVERSAL-AGENT-WORKFLOW-STANDARD-A1

## Task Definition

Per GPT authorization from HUMAN-DECISION-RECORD-MANIFEST-CONTENT-CROSSCHECK-A1 R1 (accepted_with_limitation):
Establish a universal agent workflow standard that addresses recurring limitations across all hardening tasks:
1. Run-ID consistency across pack artifacts (filename, prompt, GPT reply)
2. Prompt template standardization (use `{{RUN_ID}}` instead of hardcoded values)
3. Validation utility for detecting run_id inconsistencies

## Deliverables

### 1. `docs/AGENT_WORKFLOW_STANDARD.md` (new, ~50 lines)

Defines the canonical Agent Workflow Standard Protocol (AWSP) v1.0.0:
- Run-ID consistency rule: pack filename = run_id.txt = prompt {{RUN_ID}} = GPT reply run_id
- Evidence pack standard: PACK_MANIFEST.md with proper table, all files listed
- Prompt template standard: {{RUN_ID}}, {{TASK_ID}} variables, END_OF_GPT_RESPONSE marker
- Verification standard: post-reply run_id validation

### 2. `scripts/validate_run_id_consistency.py` (~172 lines)

Validation utility that checks (all fail-closed per AWSP v1.0.0):
- `run_id.txt` exists and contains non-empty run_id
- `R1_RUN_ID.txt` matches `run_id.txt`
- Evidence pack zip exists and filename contains run_id
- `GPT_REVIEW_PROMPT.md` uses `{{RUN_ID}}` template variable (detects hardcoded run_ids)
- `GPT_REVIEW_PROMPT.md` uses `{{TASK_ID}}` template variable
- PACK_MANIFEST.md exists in evidence pack directory
- PACK_MANIFEST.md run_id field matches run_id.txt
- PACK_MANIFEST.md run_id field present (fail if missing)
- GPT review result run_id matches submitted run_id

### 3. `tests/test_validate_run_id_consistency.py` (14 tests)

- `test_consistent_artifacts`: all matching → pass
- `test_missing_run_id_file`: no run_id.txt → fail
- `test_hardcoded_run_id_in_prompt`: hardcoded in prompt → fail
- `test_r1_run_id_mismatch`: R1_RUN_ID.txt differs → fail
- `test_gpt_reply_run_id_mismatch`: GPT reply differs → fail
- `test_gpt_reply_run_id_matches`: all match → pass
- `test_missing_run_id_template_var`: no {{RUN_ID}} → fail
- `test_missing_task_id_template_var`: no {{TASK_ID}} → fail
- `test_missing_evidence_pack_zip`: no zip → fail
- `test_manifest_run_id_mismatch`: manifest run_id differs → fail
- `test_pack_filename_mismatch`: zip name wrong → fail
- `test_empty_run_id_file`: empty run_id.txt → fail
- `test_missing_pack_manifest`: PACK_MANIFEST.md missing → fail
- `test_manifest_run_id_field_missing`: manifest has no run_id field → fail

## Iteration History

| Rev | Verdict | Key Changes |
|-----|---------|-------------|
| R1 | blocked | Initial: 7 tests, basic run_id checks. GPT found 5 gaps ({{TASK_ID}}, zip, manifest run_id). |
| R2 | blocked | Fixed R1 gaps: added {{TASK_ID}}, zip check, manifest run_id, 4 new tests. GPT found 2 more (missing PACK_MANIFEST.md). |
| R3 | blocked | Added PACK_MANIFEST.md absence check + test. GPT found 2 edge cases (manifest run_id field missing). |
| R4 | pending | Added manifest run_id field missing error + test. Full suite: 505 passed, 14 target tests. |

## Test Results

- **Total tests**: 505
- **Passed**: 505
- **Failed**: 0
- **Target tests**: 14 (validate_run_id_consistency)
