# Proposed AA-2 Scope

> For GPT review: minimum viable Runner Contract integration

---

## Goal

Define Flow Runner / TaskSpec Runner contracts in agent-acceptance so that dev-frame-opencode's S3 Phase 3 runner implementation has a clear normative foundation.

## Proposed Files

### Contracts (contracts/)

| File | Purpose |
|------|---------|
| `contracts/RUNNER_CONTRACT.schema.json` | Top-level runner invocation contract: runner_id, mode, terminal, next_action, allowed/forbidden actions, safety |
| `contracts/RUNNER_STATE.schema.json` | Runner state machine: current_step, current_round, terminal, heartbeat, resume_command |
| `contracts/RUNNER_STEP_RESULT.schema.json` | Per-step result: step_success_continue, step_human_required, step_blocked, step_failed |

### Policies (policies/)

| File | Purpose |
|------|---------|
| `policies/FLOW_RUNNER_POLICY.md` | Runner is dev-frame execution layer reading agent-acceptance rules. Only terminal=true produces final report. |
| `policies/TASKSPEC_RUNNER_POLICY.md` | TaskSpec must be machine-readable. Markdown-only is rejected. Must validate against TASKSPEC.schema.json. |
| `policies/RUN_UNTIL_TERMINAL_POLICY.md` | Default mode: run-until-terminal. terminal=false never stops. Only 6 terminal reasons. |
| `policies/NEXT_TASKSPEC_CONSUMPTION_POLICY.md` | next_task_spec_path is mandatory consumption. ready_to_dispatch != dispatched. |
| `policies/RUNNER_FAILURE_POLICY.md` | Fail-closed on schema missing/invalid, outcome missing, GPT unknown, CDP failure. high-risk → human_required. |

### Tests (tests/)

| File | Purpose |
|------|---------|
| `tests/test_runner_contract_schema.py` | Validate RUNNER_CONTRACT rules |
| `tests/test_runner_state_schema.py` | Validate RUNNER_STATE rules |
| `tests/test_runner_step_result_schema.py` | Validate RUNNER_STEP_RESULT rules |
| `tests/test_run_until_terminal_policy.py` | Validate terminal policy enforcement |
| `tests/test_next_taskspec_consumption_policy.py` | Validate consumption policy enforcement |

### Fixtures (tests/fixtures/)

| File | Purpose |
|------|---------|
| `runner_state_terminal_false_valid.json` | Valid: terminal=false with next_action |
| `runner_state_terminal_false_missing_next_action.json` | Invalid: terminal=false without next_action |
| `runner_state_terminal_true_human_required.json` | Valid: terminal=true with human_required |
| `runner_step_result_continue.json` | Valid: step_success_continue |
| `runner_step_result_stop.json` | Valid: step_human_required |
| `runner_step_result_high_risk_human_required.json` | Valid: high-risk → human_required |

## Out of Scope (Strictly Forbidden)

- Implementing `oracle_flow_runner.py` or `oracle_taskspec_runner.py`
- Modifying dev-frame-opencode execution scripts
- Modifying ai-workflow-hub business code
- Executing S3 Phase 3
- Cleaning worktrees
- Deleting, moving, or renaming files
- Modifying existing AA-1 contracts/policies core semantics

## What Stays in dev-frame-opencode

- Runner implementation (oracle_flow_runner.py, oracle_taskspec_runner.py)
- All operational scripts in tools/
- Chrome CDP handoff
- GPT reply monitoring

## Request to GPT

1. Is AA-2 scope correct?
2. Are the proposed schemas sufficient?
3. Are the proposed policies sufficient?
4. Should any file be moved to dev-frame-opencode scope?
5. May AA-2 proceed before S3 Phase 3?
