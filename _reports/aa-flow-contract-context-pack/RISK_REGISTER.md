# Risk Register — AA-1 Flow Contract Integration

---

| # | Risk | Severity | Current Symptom | Proposed Contract Mitigation |
|---|------|----------|----------------|------------------------------|
| 1 | **terminal=false still stops** | P0 | Agent writes final report even when flow is not terminal | `TERMINAL_STATE_POLICY`: only 6 terminal states; `terminal=false` MUST continue |
| 2 | **ready_to_dispatch treated as dispatched** | P0 | Post-decision driver writes `ready_to_dispatch` → automation considers it done | `DISPATCH_RESULT` schema: separate `dispatch_status` enum with `ready_to_dispatch` ≠ `dispatched` |
| 3 | **TaskSpec generated but not consumed** | P0 | Next task spec exists on disk → no runner executes it → gap in automation | `TASKSPEC` schema: `terminal_conditions` field; runner contract in `DISPATCHER_POLICY` |
| 4 | **human_required bypassed** | P0 | Automation proceeds without human attestation when GPT says `human_required` | `HUMAN_REQUIRED_TAXONOMY`: structured categorization; `FLOW_OUTCOME` schema enforces stop |
| 5 | **Markdown used as automation truth** | P1 | Reports drive decisions instead of machine-readable JSON | `FLOW_OUTCOME` schema: JSON single source of truth; `EVIDENCE_PACK_CONTRACT` requires JSON |
| 6 | **dev-frame-opencode self-defines gate** | P1 | Execution layer contains its own acceptance logic | `STAGE_GATE_POLICY`: gate definitions in agent-acceptance; dev-frame reads, doesn't define |
| 7 | **transport success masks business rejection** | P1 | Upload success → assumed acceptance; GPT may say `blocked` | `FLOW_OUTCOME` schema: three-layer model (transport / business_decision / dispatch_status) |
| 8 | **Ambiguous authority on stage advancement** | P1 | No policy says who decides whether to advance stages | `STAGE_GATE_POLICY` + `AUTONOMOUS_PROGRESS_POLICY` |
| 9 | **Evidence pack missing manifest** | P2 | Pack generated without manifest → receiver cannot verify completeness | `EVIDENCE_PACK_CONTRACT`: manifest mandatory |
| 10 | **Missing evidence silently ignored** | P2 | Evidence pack with gaps submitted to GPT without flagging | `EVIDENCE_PACK_CONTRACT`: missing evidence MUST be explicitly listed |
