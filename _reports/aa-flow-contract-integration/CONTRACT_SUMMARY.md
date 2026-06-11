# AA-1 Contract Summary

## FLOW_OUTCOME.schema.json

**Purpose**: Single machine-readable source of truth for automation decisions.

**Three-layer model**:
1. **transport_status** (Layer 1): Did upload/submission succeed? Values: success/failed/partial/pending
2. **business_decision** (Layer 2): What did reviewer decide? Values: accepted/blocked/human_required/partial/unknown
3. **dispatch_status** (Layer 3): What is the execution state? Values: ready_to_dispatch/dispatched/taskspec_generated/manual_confirm_required/stopped/failed

**Key rules**:
- terminal=false must have next_task_spec_path or required_next_action
- human_required → terminal=true, allow_next_stage=false
- accepted + allow_next_stage=true → must have next_stage or next_task_spec_path
- blocked → must have required_next_action

## TASKSPEC.schema.json

**Purpose**: Machine-readable task specification. TaskSpecs must NOT be Markdown-only.

**Key rules**:
- 8 required fields including terminal_conditions
- high_risk=true → review_by must be "human"
- terminal_conditions define when terminal=true is valid

## DISPATCH_RESULT.schema.json

**Purpose**: Dispatch operation result with 6-state enum.

**Key rules**:
- ready_to_dispatch ≠ dispatched (explicit distinction)
- dispatched → must have next_task_spec_path, terminal=false
- stopped/failed → terminal=true, should_execute_next=false
- taskspec_generated → terminal=false
- manual_confirm_required → must have required_next_action
