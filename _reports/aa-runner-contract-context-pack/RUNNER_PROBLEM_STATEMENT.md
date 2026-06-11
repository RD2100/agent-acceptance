# Runner Problem Statement

> Structural issues addressed by the Runner Contract

---

## Problem Matrix

| # | Problem | Concrete Example | Required Contract |
|---|---------|-----------------|-------------------|
| 1 | **next_task_spec generated but not consumed** | S3_PHASE2_TASKSPEC.md generated after GPT acceptance → automation halted instead of executing it | `NEXT_TASKSPEC_CONSUMPTION_POLICY` + `RUNNER_STATE.schema.json` |
| 2 | **terminal=false still stops** | Agent writes a final summary report when `terminal=false` and a next task spec is waiting | `RUN_UNTIL_TERMINAL_POLICY` + `RUNNER_CONTRACT.schema.json` |
| 3 | **Markdown-only TaskSpec** | No machine-readable TaskSpec JSON exists; only Markdown report is available | `TASKSPEC_RUNNER_POLICY` |
| 4 | **Runner unclear when to stop vs continue** | Post-decision driver writes `ready_to_dispatch` but nothing picks it up — runner doesn't know it should run | `FLOW_RUNNER_POLICY` |
| 5 | **high-risk action boundary unclear** | Runner might delete, move, rename files without human confirmation because no contract says it must stop | `RUNNER_FAILURE_POLICY` |
| 6 | **dev-frame self-defines runner semantics** | Execution layer invents its own interpretation of "accepted means continue" instead of reading agent-acceptance | `RUNNER_CONTRACT.schema.json` |
| 7 | **Long-running loop cannot recover** | If runner crashes mid-loop, there's no state file to resume from | `RUNNER_STATE.schema.json` |
| 8 | **Step partial success treated as final success** | A partially-completed step is reported as "done" — runner continues without addressing remaining gaps | `RUNNER_STEP_RESULT.schema.json` |

---

## Root Cause

AA-1 defined the **what** (schemas for flow outcomes, task specs, dispatch results) and the **when** (policies for terminal state, autonomous progress, stage gates).

But AA-1 did not define the **how** — the runner-level execution contract that binds these schemas together into a runnable loop. That is what AA-2 provides.

Without a runner contract:
- Schemas exist but aren't enforced at runtime
- Policies are documented but not mechanically applied
- The gap between "GPT accepted" and "next task spec executed" remains
