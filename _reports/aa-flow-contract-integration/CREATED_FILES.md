# AA-1 Created Files

## contracts/

| File | Purpose |
|------|---------|
| `contracts/FLOW_OUTCOME.schema.json` | Three-layer flow state schema (transport/business/dispatch) |
| `contracts/TASKSPEC.schema.json` | Machine-readable task specification schema |
| `contracts/DISPATCH_RESULT.schema.json` | Dispatch operation result schema with 6-state enum |
| `contracts/README.md` | Contract index and usage guide |

## policies/

| File | Purpose |
|------|---------|
| `policies/TERMINAL_STATE_POLICY.md` | 6 valid terminal states; terminal=false must continue |
| `policies/DISPATCHER_POLICY.md` | Dispatcher decision matrix; accepted→dispatch, human_required→stop |
| `policies/AUTONOMOUS_PROGRESS_POLICY.md` | Allowed autonomous actions vs human-required actions |
| `policies/HUMAN_REQUIRED_TAXONOMY.md` | 8-category taxonomy for human_required reasons |
| `policies/STAGE_GATE_POLICY.md` | Gate definitions, stage advancement conditions, GPT vs gate priority |
| `policies/EVIDENCE_PACK_CONTRACT.md` | Minimum evidence pack requirements with manifest format |
| `policies/README.md` | Policy index and precedence rules |

## tests/

| File | Purpose | Tests |
|------|---------|-------|
| `tests/test_flow_outcome_schema.py` | FLOW_OUTCOME validation | 8 |
| `tests/test_taskspec_schema.py` | TASKSPEC validation | 5 |
| `tests/test_dispatch_result_schema.py` | DISPATCH_RESULT validation | 6 |
| `tests/test_terminal_state_policy.py` | Terminal state policy enforcement | 6 |
| `tests/test_dispatcher_policy.py` | Dispatcher policy enforcement | 5 |

## tests/fixtures/

| File | Purpose |
|------|---------|
| `tests/fixtures/valid_flow_outcome.json` | Valid FLOW_OUTCOME for testing |
| `tests/fixtures/invalid_terminal_false_no_next_action.json` | terminal=false without next action |
| `tests/fixtures/valid_taskspec.json` | Valid TASKSPEC for testing |
| `tests/fixtures/invalid_markdown_only_taskspec.json` | Markdown-only TaskSpec (invalid) |
| `tests/fixtures/valid_dispatch_result.json` | Valid DISPATCH_RESULT for testing |
| `tests/fixtures/invalid_ready_to_dispatch_as_dispatched.json` | ready_to_dispatch treated as terminal |

## _reports/aa-flow-contract-integration/

| File | Purpose |
|------|---------|
| `AA1_IMPLEMENTATION_REPORT.md` | This implementation report |
| `CREATED_FILES.md` | This file list |
| `UPDATED_FILES.md` | List of updated files (none) |
| `TEST_OUTPUT.md` | Test execution results (30/30) |
| `SAFETY_CHECK.md` | Safety compliance verification |
| `CONTRACT_SUMMARY.md` | Contract summary |
| `POLICY_SUMMARY.md` | Policy summary |
| `DEV_FRAME_INTEGRATION_GUIDE.md` | How dev-frame-opencode reads these contracts |
| `GPT_REVIEW_PROMPT.md` | Prompt for GPT Phase 2 review |

## Total

- 3 schemas + 1 README (contracts/)
- 6 policies + 1 README (policies/)
- 5 test files + 6 fixtures (tests/)
- 9 report files (_reports/aa-flow-contract-integration/)
- **Total: 31 files created**
