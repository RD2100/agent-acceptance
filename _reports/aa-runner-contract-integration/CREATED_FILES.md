# AA-2 Created Files

| Directory | File | Purpose |
|-----------|------|---------|
| contracts/ | RUNNER_CONTRACT.schema.json | Top-level runner invocation contract |
| contracts/ | RUNNER_STATE.schema.json | Runner state machine (persisted for recovery) |
| contracts/ | RUNNER_STEP_RESULT.schema.json | Per-step execution result |
| policies/ | FLOW_RUNNER_POLICY.md | Runner is dev-frame execution layer |
| policies/ | TASKSPEC_RUNNER_POLICY.md | TaskSpec must be machine-readable JSON |
| policies/ | RUN_UNTIL_TERMINAL_POLICY.md | terminal=false never stops |
| policies/ | NEXT_TASKSPEC_CONSUMPTION_POLICY.md | next_task_spec_path is mandatory |
| policies/ | RUNNER_FAILURE_POLICY.md | Fail-closed, high-risk→human_required |
| tests/ | test_runner_contract_schema.py | 6 tests |
| tests/ | test_runner_state_schema.py | 6 tests |
| tests/ | test_runner_step_result_schema.py | 6 tests |
| tests/ | test_run_until_terminal_policy.py | 6 tests |
| tests/ | test_next_taskspec_consumption_policy.py | 6 tests |
| tests/fixtures/ | 10 JSON fixtures | Valid/invalid runner states and step results |

### Updated Files

| File | Change |
|------|--------|
| contracts/README.md | Append-only: AA-2 runner schema index and relationship to AA-1 |
| policies/README.md | Append-only: AA-2 runner policy index and precedence |
