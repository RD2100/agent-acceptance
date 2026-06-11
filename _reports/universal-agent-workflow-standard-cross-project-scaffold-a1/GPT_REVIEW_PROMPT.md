## GPT Review Prompt — UNIVERSAL-AGENT-WORKFLOW-STANDARD-CROSS-PROJECT-SCAFFOLD-A1 R3

You are reviewing the R3 deliverables for task **UNIVERSAL-AGENT-WORKFLOW-STANDARD-CROSS-PROJECT-SCAFFOLD-A1**.

**Task ID**: {{TASK_ID}}
**Run ID**: {{RUN_ID}}

### R2 Blocking Issues Fixed

1. **Indented verdict detection**: Verdict regex changed from `^verdict:` to `^\s*verdict:` to catch verdict fields with leading whitespace (e.g., `  verdict: accepted`). New test: `test_indented_verdict_fails`.

2. **Validation values fail-closed**: `validate_scaffold()` now checks that all 5 `require_*` validation config values are `true`. Setting any to `false` fails validation. New test: `test_false_validation_values_fails`.

3. **Directories field check**: `validate_scaffold()` now verifies `.awsp.json` `directories` field matches `AWSP_DIRECTORIES` constant. Mismatch fails validation. New test: `test_directories_mismatch_fails`.

### R3 Deliverables

1. **scripts/validate_run_id_consistency.py** (~195 lines)
   - Parameterized config, prompt-template checks (END marker, overall_judgment, strict verdict)
   - R3: indented verdict detection (`^\s*verdict:`)
   - 14 tests

2. **scripts/awsp_scaffold.py** (~225 lines)
   - create_scaffold, validate_scaffold
   - R3: validate_scaffold checks validation values are true, directories match AWSP_DIRECTORIES
   - 21 tests in test_cross_project_scaffold.py

3. **tests/test_cross_project_scaffold.py** (24 tests)
   - TestCrossProjectParameterization (3)
   - TestPromptTemplateValidation (4)
   - TestAWSPScaffold (8)
   - TestValidateScaffoldContent (6): valid, version mismatch, missing fields, missing validation, false values, directories mismatch
   - TestStrictVerdictCheck (3): bare verdict, overall_judgment only, indented verdict

4. **docs/AGENT_WORKFLOW_STANDARD.md** — AWSP v1.1.0

### Validation Results

- **Target tests**: 38 passed / 38 total
- **Full suite**: 529 passed / 529 total

### Review Criteria

1. Indented verdict detection catches `  verdict:` with whitespace?
2. Validation values fail-closed when set to false?
3. Directories field mismatch detected?
4. 38 target tests sufficient?
5. Full suite 529 tests pass?

### Expected Verdict Format

```
overall_judgment: accepted | accepted_with_limitation | blocked | human_required
run_id: {{RUN_ID}}
findings: [list key findings]
next_task_authorization: [next task or "none"]
---END_OF_GPT_RESPONSE---
```
