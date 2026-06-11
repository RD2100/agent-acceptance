# Runner Contract Traceability

> Mapping AA-2 runner contracts to the problems they solve

---

| Problem | AA-1 Contract | AA-2 Contract | How AA-2 Extends AA-1 |
|---------|--------------|---------------|----------------------|
| terminal=false still stops | TERMINAL_STATE_POLICY (defines rule) | RUN_UNTIL_TERMINAL_POLICY (enforces at runner level) | Runner mechanically checks terminal before each step and refuses to stop when false |
| TaskSpec generated, not consumed | DISPATCH_RESULT (defines taskspec_generated state) | NEXT_TASKSPEC_CONSUMPTION_POLICY + RUNNER_STATE.next_task_spec_path | Runner reads next_task_spec_path and consumes it before writing terminal=true |
| ready_to_dispatch != dispatched | DISPATCH_RESULT (defines enum) | RUNNER_STEP_RESULT (checks dispatch_status per step) | Runner reads dispatch_status from step result and only transitions to dispatched after execution |
| Markdown as source of truth | TASKSPEC (JSON schema) | TASKSPEC_RUNNER_POLICY (enforces JSON-only) | Runner validates TASKSPEC is machine-readable JSON before executing |
| Runner unclear stop/continue | FLOW_OUTCOME (defines terminal field) | RUNNER_STATE (persists terminal + next_action) | Runner reads terminal from state, executes next_action when false |
| High-risk auto-executed | AUTONOMOUS_PROGRESS_POLICY (defines human-required actions) | RUNNER_FAILURE_POLICY (fail-closed + high-risk detection) | Runner checks each action against human_required taxonomy, stops before execution |
| Long-running loop crashes | None | RUNNER_STATE (heartbeat + retries + resume) | Runner persists state every step; resume_command enables recovery |
| Partial treated as success | None | RUNNER_STEP_RESULT (step_partial != step_success_terminal) | Runner distinguishes partial progress from terminal completion |

---

## Coverage

- **AA-1 problems**: 4/8 addressed by AA-1 alone (schema definitions)
- **AA-2 extends**: 8/8 problems now have runner-level enforcement
- **Remaining for S3 Phase 3**: Actual runner implementation in dev-frame-opencode
