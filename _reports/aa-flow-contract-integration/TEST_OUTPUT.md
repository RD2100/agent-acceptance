# AA-1 Test Output

> Generated: 2026-06-02
> Total: 30/30 passed

---

## test_flow_outcome_schema.py — 8/8 passed

| # | Test | Result |
|---|------|--------|
| 1 | Valid fixture validates | PASS |
| 2 | terminal=false without next action (rejected) | PASS |
| 3 | human_required rules enforced | PASS |
| 4 | human_required missing next_action (rejected) | PASS |
| 5 | accepted+allow_next without next stage (rejected) | PASS |
| 6 | blocked must have next_action | PASS |
| 7 | transport success != business accepted (distinction validated) | PASS |
| 8 | ready_to_dispatch with terminal=true (rejected) | PASS |

## test_taskspec_schema.py — 5/5 passed

| # | Test | Result |
|---|------|--------|
| 1 | Valid fixture validates | PASS |
| 2 | Markdown-only TaskSpec (rejected) | PASS |
| 3 | high_risk=true requires human review | PASS |
| 4 | high_risk=true with gpt review (rejected) | PASS |
| 5 | Missing terminal_conditions (rejected) | PASS |

## test_dispatch_result_schema.py — 6/6 passed

| # | Test | Result |
|---|------|--------|
| 1 | Valid fixture validates | PASS |
| 2 | ready_to_dispatch treated as dispatched (rejected) | PASS |
| 3 | dispatched needs next_task_spec_path | PASS |
| 4 | stopped needs required_next_action | PASS |
| 5 | manual_confirm needs required_next_action | PASS |
| 6 | taskspec_generated must not be terminal | PASS |

## test_terminal_state_policy.py — 6/6 passed

| # | Test | Result |
|---|------|--------|
| 1 | Valid terminal reasons count | PASS |
| 2 | Non-terminal state validation | PASS |
| 3 | ready_to_dispatch vs dispatched distinct | PASS |
| 4 | Exactly 6 terminal states | PASS |
| 5 | TaskSpec generated is not terminal | PASS |
| 6 | stopped/failed are terminal in schema | PASS |

## test_dispatcher_policy.py — 5/5 passed

| # | Test | Result |
|---|------|--------|
| 1 | accepted must dispatch not stop | PASS |
| 2 | human_required must stop | PASS |
| 3 | unknown must fail-closed | PASS |
| 4 | must produce should_execute_next | PASS |
| 5 | empty dispatch rejected | PASS |

---

## Summary

30/30 tests PASSED. All schemas, policies, and fixtures work correctly.
