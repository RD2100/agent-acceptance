# Existing Context Index

> Evidence available at the time of AA-2 initiation

---

## AA-1 Evidence (agent-acceptance)

| Evidence | Expected Path | Exists | Purpose |
|----------|--------------|--------|---------|
| AA-1 GPT Phase 0 decision | `_reports/aa-flow-contract-context-pack/GPT_REVIEW_DECISION.md` | yes | Proves AA-1 Phase 0 accepted |
| AA-1 GPT Phase 2 decision | `_reports/aa-flow-contract-integration/GPT_REVIEW_DECISION.md` | yes | Proves AA-1 final accepted |
| FLOW_OUTCOME schema | `contracts/FLOW_OUTCOME.schema.json` | yes | Existing contract — runner must validate against this |
| TASKSPEC schema | `contracts/TASKSPEC.schema.json` | yes | Existing contract — runner must validate TaskSpecs against this |
| DISPATCH_RESULT schema | `contracts/DISPATCH_RESULT.schema.json` | yes | Existing contract — runner reads dispatch state |
| Terminal state policy | `policies/TERMINAL_STATE_POLICY.md` | yes | Existing policy — runner inherits terminal rules |
| Dispatcher policy | `policies/DISPATCHER_POLICY.md` | yes | Existing policy — upstream of runner |
| Autonomous progress policy | `policies/AUTONOMOUS_PROGRESS_POLICY.md` | yes | Existing policy — runner checks before auto-advancing |
| AA-1 tests | `tests/test_flow_outcome_schema.py` etc. | yes | Existing tests — runner tests build on these |

## S3 Evidence (dev-frame-opencode)

| Evidence | Expected Path | Exists | Purpose |
|----------|--------------|--------|---------|
| S3 Phase 2 GPT decision | `/d/dev-frame-opencode/_reports/gpt-reviews/` | unknown | Proves S3 Phase 2 accepted |
| FLOW_OUTCOME.json (latest) | `/d/dev-frame-opencode/_reports/` | missing | Current flow state in dev-frame |
| ACTION_LOG.md (latest) | `/d/dev-frame-opencode/_reports/` | missing | Current action log in dev-frame |

## Oracle Tools (dev-frame-opencode)

| Evidence | Expected Path | Exists | Purpose |
|----------|--------------|--------|---------|
| oracle_gpt_full_review_flow.py | `/d/dev-frame-opencode/tools/` | yes | Used for GPT submission |
| oracle_flow_state.py | `/d/dev-frame-opencode/tools/` | yes | Flow state management |
| oracle_decision_dispatcher.py | `/d/dev-frame-opencode/tools/` | yes | Decision → dispatch |
| oracle_post_decision_driver.py | `/d/dev-frame-opencode/tools/` | yes | Post-GPT decision driver |

## Key Gap

No runner-level scripts exist yet in dev-frame-opencode (no `oracle_flow_runner.py`, no `oracle_taskspec_runner.py`). This is expected — AA-2 defines the contracts, S3 Phase 3 implements.
