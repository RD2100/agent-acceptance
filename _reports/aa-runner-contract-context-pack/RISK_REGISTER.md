# Risk Register — AA-2 Runner Contract

---

| # | Risk | Severity | Current Symptom | Proposed Mitigation |
|---|------|----------|----------------|---------------------|
| 1 | **terminal=false still stops** | P0 | Agent outputs final report when flow is non-terminal | `RUN_UNTIL_TERMINAL_POLICY` + `RUNNER_CONTRACT.schema.json` |
| 2 | **TaskSpec generated but not executed** | P0 | Next TaskSpec on disk but no runner picks it up | `NEXT_TASKSPEC_CONSUMPTION_POLICY` |
| 3 | **Runner invents local semantics** | P0 | Execution layer self-defines stop/continue rules | `FLOW_RUNNER_POLICY` establishes agent-acceptance as authority |
| 4 | **High-risk action auto-executed** | P0 | Runner deletes/moves/renames without human confirmation | `RUNNER_FAILURE_POLICY`: high-risk → human_required |
| 5 | **Markdown used as execution authority** | P1 | Runner reads .md report instead of .json schema | `TASKSPEC_RUNNER_POLICY`: reject Markdown-only |
| 6 | **Partial step treated as final success** | P1 | Runner continues after incomplete step | `RUNNER_STEP_RESULT.schema.json`: step_partial ≠ step_success |
| 7 | **Long-running loop cannot recover** | P2 | Runner crashes, no state to resume from | `RUNNER_STATE.schema.json`: heartbeat + resume_command |
| 8 | **Schema missing → runner proceeds** | P0 | Runner doesn't validate inputs before executing | `RUNNER_FAILURE_POLICY`: fail-closed on schema missing |
| 9 | **Schema invalid → runner proceeds** | P0 | Runner accepts malformed data | `RUNNER_FAILURE_POLICY`: fail-closed on schema invalid |
| 10 | **ready_to_dispatch treated as dispatched** | P0 | Post-decision driver output consumed as final | `NEXT_TASKSPEC_CONSUMPTION_POLICY`: explicit distinction |
