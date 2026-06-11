# AA-2 Test Output

> Total: 30/30 passed

---

## test_runner_contract_schema.py — 6/6

| # | Test | Result |
|---|------|--------|
| 1 | Valid contract passes | PASS |
| 2 | terminal=false without input (rejected) | PASS |
| 3 | terminal=false with next_action valid | PASS |
| 4 | resume mode without outcome_path (rejected) | PASS |
| 5 | high-risk contract fixture | PASS |
| 6 | missing safety_policy (rejected) | PASS |

## test_runner_state_schema.py — 6/6

| # | Test | Result |
|---|------|--------|
| 1 | Valid terminal=false | PASS |
| 2 | terminal=false missing next_action (rejected) | PASS |
| 3 | human_required with resume | PASS |
| 4 | human_required without resume (rejected) | PASS |
| 5 | accepted cannot be terminal (rejected) | PASS |
| 6 | Recoverable failure state | PASS |

## test_runner_step_result_schema.py — 6/6

| # | Test | Result |
|---|------|--------|
| 1 | Valid step_success_continue | PASS |
| 2 | Valid step_human_required | PASS |
| 3 | Valid high-risk human_required | PASS |
| 4 | continue without next_action (rejected) | PASS |
| 5 | step_partial as terminal (rejected) | PASS |
| 6 | transport success != business accepted | PASS |

## test_run_until_terminal_policy.py — 6/6

| # | Test | Result |
|---|------|--------|
| 1 | 6 valid terminal reasons | PASS |
| 2 | terminal=false no final report | PASS |
| 3 | accepted cannot be terminal | PASS |
| 4 | high-risk triggers human_required | PASS |
| 5 | TaskSpec invalid fail-closed | PASS |
| 6 | schema missing fail-closed | PASS |

## test_next_taskspec_consumption_policy.py — 6/6

| # | Test | Result |
|---|------|--------|
| 1 | next_action required when terminal=false | PASS |
| 2 | ready_to_dispatch != dispatched | PASS |
| 3 | valid state has next_action | PASS |
| 4 | invalid fixture missing next_action | PASS |
| 5 | consumption policy exists | PASS |
| 6 | taskspec_generated is non-terminal | PASS |
