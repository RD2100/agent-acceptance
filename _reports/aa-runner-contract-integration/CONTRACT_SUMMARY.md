# AA-2 Contract Summary

## RUNNER_CONTRACT.schema.json

**Purpose**: Interface between dispatcher and runner.

**Key rules**:
- terminal=false → input_taskspec_path or next_action required
- resume mode → input_outcome_path required
- safety_policy.high_risk_triggers_human_required always true
- safety_policy.fail_closed always true
- forbidden_actions min: delete, move, rename, clean_worktree, overwrite_evidence, fabricate_baseline, fabricate_attestation

## RUNNER_STATE.schema.json

**Purpose**: Persisted state machine for runner recovery.

**Key rules**:
- terminal=false → next_action required
- human_required + terminal=true → resume_command required
- accepted → terminal must be false (accepted implies continuation)
- heartbeat for liveness detection
- retries tracked per-step, per-round, total

## RUNNER_STEP_RESULT.schema.json

**Purpose**: Per-step execution outcome.

**Key rules**:
- 6 step statuses: step_success_continue, step_success_terminal, step_blocked, step_human_required, step_failed, step_partial
- step_success_continue → terminal=false, next_action required
- step_partial → terminal=false (not final)
- step_human_required/blocked/failed → terminal=true
- high-risk action detected → step_human_required with human_confirmed=false
- Three-layer model reused: transport_status, business_decision, dispatch_status
