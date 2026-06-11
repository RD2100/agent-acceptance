## GPT Review Prompt — UNIVERSAL-AGENT-WORKFLOW-STANDARD-AGENT-CONFIG-SCAFFOLD-A1 R3

You are reviewing the R3 deliverables for task **UNIVERSAL-AGENT-WORKFLOW-STANDARD-AGENT-CONFIG-SCAFFOLD-A1**.

**Task ID**: {{TASK_ID}}
**Run ID**: {{RUN_ID}}

### R2 Blocking Issues Fixed

1. **PROJECT_AGENT_CONFIG awsp_version fail-closed (R2 blocking #1)**: `validate_scaffold()` now explicitly checks if `.agent/PROJECT_AGENT_CONFIG.json` has `awsp_version` field. If missing, adds error. If present but wrong value, also adds error. Fail-closed on both absence and mismatch.

2. **New test (R2 blocking #2)**: `test_project_agent_config_missing_awsp_version_fails` deletes awsp_version from PROJECT_AGENT_CONFIG.json and asserts validate_scaffold() returns valid=false with specific error message "missing required field: awsp_version".

### R3 Deliverables

1. **scripts/awsp_scaffold.py** (~475 lines)
   - R3: awsp_version missing check in PROJECT_AGENT_CONFIG validation (fail-closed)
   - 42 tests

2. **tests/test_cross_project_scaffold.py** (42 tests)
   - TestCrossProjectParameterization (3)
   - TestPromptTemplateValidation (4)
   - TestAWSPScaffold (8)
   - TestValidateScaffoldContent (6)
   - TestStrictVerdictCheck (3)
   - TestAgentConfigScaffold (5)
   - TestValidateAgentConfig (6)
   - TestR2AgentConfigContentValidation (7): relative path, awsp_version mismatch, awsp_version missing, governance flags, gates, required_reads, self-validation

### Validation Results

- **Target tests**: 56 passed / 56 total
- **Full suite**: 547 passed / 547 total

### Review Criteria

1. validate_scaffold() fail-closed when PROJECT_AGENT_CONFIG.json missing awsp_version?
2. New test confirms missing awsp_version → valid=false?
3. 56 target tests pass? Full suite 547 passes?

### Expected Verdict Format

```
overall_judgment: accepted | accepted_with_limitation | blocked | human_required
run_id: {{RUN_ID}}
findings: [list key findings]
next_task_authorization: [next task or "none"]
---END_OF_GPT_RESPONSE---
```
