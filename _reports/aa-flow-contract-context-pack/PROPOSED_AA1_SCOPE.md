# Proposed AA-1 Scope

> For GPT review: minimum viable Flow Contract integration

---

## Goal

Define the Flow Contract in agent-acceptance so that dev-frame-opencode's automation execution MUST follow unified schemas and gates.

## Proposed New Files

### Core Schemas (contracts/)

| File | Purpose |
|------|---------|
| `contracts/FLOW_OUTCOME.schema.json` | Three-layer state: transport → business → dispatch. Distinguishes `ready_to_dispatch` from `dispatched`. |
| `contracts/TASKSPEC.schema.json` | Machine-readable task specification. Not just Markdown. Defines `terminal_conditions`, `allowed_actions`, `forbidden_actions`. |
| `contracts/DISPATCH_RESULT.schema.json` | Dispatch outcome: `dispatch_status` enum, `should_execute_next`, `resume_command`. |

### Policies (policies/)

| File | Purpose |
|------|---------|
| `policies/TERMINAL_STATE_POLICY.md` | When `terminal=false`, agent MUST continue consuming `next_task_spec`. Only 6 states allow `terminal=true`. |
| `policies/DISPATCHER_POLICY.md` | Dispatcher must generate consumable dispatch result. Accepted+allow_next_stage → must progress. |
| `policies/AUTONOMOUS_PROGRESS_POLICY.md` | What can auto-advance vs. what requires human. |
| `policies/HUMAN_REQUIRED_TAXONOMY.md` | Structured taxonomy: `missing_baseline`, `destructive_action`, `sensitive_config`, `evidence_overwrite`, `scope_expansion`, `ambiguous_authority`, `external_secret`, `manual_attestation_required`. |
| `policies/STAGE_GATE_POLICY.md` | Gate definitions: `accepted`, `blocked`, `human_required`, `partial`, `unknown`. Stage advancement conditions. |
| `policies/EVIDENCE_PACK_CONTRACT.md` | Minimum evidence pack requirements. Must include manifest; missing evidence must be explicitly listed. |

### Tests (tests/)

| File | Purpose |
|------|---------|
| `tests/test_flow_outcome_schema.py` | Validate FLOW_OUTCOME schema rules |
| `tests/test_taskspec_schema.py` | Validate TASKSPEC schema rules |
| `tests/test_dispatch_result_schema.py` | Validate DISPATCH_RESULT schema rules |
| `tests/test_terminal_state_policy.py` | Validate terminal policy rules |
| `tests/test_dispatcher_policy.py` | Validate dispatcher policy rules |

## Out of Scope (Strictly Forbidden)

- Executing S3
- Modifying dev-frame-opencode execution scripts
- Modifying ai-workflow-hub business code
- Cleaning worktrees
- Deleting any files
- Moving any files
- Renaming any files
- Overwriting historical GPT review evidence
- Fabricating baselines or human attestations

## What Stays in dev-frame-opencode

- Chrome CDP handoff scripts
- GPT reply monitor
- Post-decision driver
- TaskSpec runner
- Evidence pack generator
- All operational scripts in `tools/oracle_*.py`

Dev-frame-opencode keeps execution. Agent-acceptance defines the contracts it must follow.

## What Stays in ai-workflow-hub

- Business logic
- Domain code
- All source files under `ai-workflow-hub/src/`

Untouched.

---

## Request to GPT

1. Is this scope correct?
2. Should any file be removed from scope?
3. Should any file be added?
4. Is any file incorrectly placed (should be in dev-frame-opencode instead)?
5. Should AA-1 proceed before S3 Phase 2?
