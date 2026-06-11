# AA-2 Policy Summary

## FLOW_RUNNER_POLICY.md

Runner is dev-frame execution layer. Its sole normative authority is agent-acceptance. Validates schemas before execution. Final report only at terminal=true. Persists RUNNER_STATE after every step.

## TASKSPEC_RUNNER_POLICY.md

TaskSpec must be machine-readable JSON. Markdown-only is rejected. Validates against TASKSPEC.schema.json. high_risk=true stops with step_human_required. forbidden_actions blocked at schema level.

## RUN_UNTIL_TERMINAL_POLICY.md

Default: run-until-terminal. terminal=false NEVER means stop. Only 6 valid terminal reasons. TaskSpec generation ≠ terminal. Terminal=false with no next_action is a schema-level violation.

## NEXT_TASKSPEC_CONSUMPTION_POLICY.md

next_task_spec_path is mandatory consumption (P0). ready_to_dispatch ≠ dispatched. taskspec_generated is non-terminal. Unconsumed TaskSpec = policy violation.

## RUNNER_FAILURE_POLICY.md

Fail-closed on: schema missing, schema invalid, outcome missing, TaskSpec invalid, GPT unknown, CDP failure. High-risk actions → human_required. Repeated failure escalation (3 strikes).
