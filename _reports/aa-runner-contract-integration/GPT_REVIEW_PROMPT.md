You are the Dev Frame OpenCode / agent-acceptance joint review agent.

I am uploading the AA-2 Runner Contract Integration Review Pack.

## What Was Done

AA-2 Phase 1 has been completed in agent-acceptance:

### Runner Contracts (contracts/)
- RUNNER_CONTRACT.schema.json — top-level runner invocation with fail-closed + high_risk_detection
- RUNNER_STATE.schema.json — persisted state machine with heartbeat, retries, resume_command
- RUNNER_STEP_RESULT.schema.json — 6 step statuses, three-layer model, high-risk detection

### Runner Policies (policies/)
- FLOW_RUNNER_POLICY.md — runner is dev-frame execution layer; validates schemas first; only terminal=true produces final report
- TASKSPEC_RUNNER_POLICY.md — JSON-only TaskSpec; high_risk → human_required; forbidden_actions blocked
- RUN_UNTIL_TERMINAL_POLICY.md — terminal=false NEVER stops; only 6 terminal reasons; TaskSpec generation ≠ terminal
- NEXT_TASKSPEC_CONSUMPTION_POLICY.md — next_task_spec_path is P0 mandatory consumption; ready_to_dispatch ≠ dispatched
- RUNNER_FAILURE_POLICY.md — fail-closed matrix; high-risk taxonomy mapped; repeated failure escalation

### Tests (tests/)
- 5 test files, 30/30 tests passing
- 10 fixtures (valid + invalid runner states, step results)

## What You Must Judge

1. Is RUNNER_CONTRACT complete? Does terminal=false require input_taskspec_path or next_action?
2. Is RUNNER_STATE complete? Can it recover from crash? Does human_required require resume_command?
3. Is RUNNER_STEP_RESULT complete? Does it distinguish step_success_continue from step_success_terminal? Does step_partial reject terminal=true?
4. Do policies clearly state dev-frame is execution layer?
5. Is run-until-terminal enforced?
6. Is next_task_spec consumption mandatory?
7. Is fail-closed behavior defined for all failure modes?
8. Are 30 tests sufficient?
9. Can dev-frame-opencode implement S3 Phase 3 oracle_flow_runner.py against these contracts?
10. May S3 Phase 3 resume?

## Output Format

```
Overall Judgment: [accepted / partial / blocked / human_required]
AA-2 Accepted: [yes / no]
Runner Contracts Complete: [yes / no]
Runner Policies Complete: [yes / no]
Tests Sufficient: [yes / no]
Dev-frame Runner Implementation Allowed: [yes / no]
S3 Phase 3 May Resume: [yes / no]
Identified Gaps: [list or "none"]
Required Next Action: [concrete step]
```

## Rules

- If terminal=false rules missing → not accepted
- If next_task_spec consumption rules unclear → not accepted
- If tests insufficient → not accepted
- If any evidence of deletion/movement/renaming → human_required
