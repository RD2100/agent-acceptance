## STATE-MACHINE-RUNTIME-INTEGRATE-A1 — Execution Report

| Field | Value |
|-------|-------|
| **task_id** | STATE-MACHINE-RUNTIME-INTEGRATE-A1 |
| **run_id** | STATE_MACHINE_RUNTIME_INTEGRATE_A1_20260609T124000_RD |
| **status** | complete |
| **generated_at** | 2026-06-09T20:40:00+08:00 |
| **author** | Agent (QoderWork) |
| **parent_task** | STARTUP-READ-GATE-DEFAULT-PATH-RUNID-HARDEN-A1 (GPT-authorized) |

### Scope

Create state machine runtime enforcement script that integrates startup_read_gate and pre_gpt_review_gate as guard conditions for state transitions, per PROCESS_STATE_MACHINE.json (8 states, 10 transitions, 8 invariants).

### Implementation Summary

**New: `scripts/state_machine_runtime.py`** (~280 lines)

- 8 states matching PROCESS_STATE_MACHINE.json: draft, gate_passing, gpt_reviewing, accepted, accepted_with_limitation, blocked, human_required, closed
- 10 transitions (T01-T10) with valid transition set
- `is_valid_transition()` — validates against defined transition set
- `check_draft_to_gate_passing()` — implements guard conditions for draft → gate_passing:
  - evidence_pack_linter_pass (via evidence_pack_linter.lint)
  - evidence_pack_complete (actual_deliverables non-empty)
  - startup_read_gate_pass (via startup_read_gate.gate with auto-detect)
- `check_transition()` — generic transition check dispatching to specific guards
- CLI: `--action check-transition|list-states|list-transitions`
- Integrates resolve_required_reads_path for auto-detection

**New: `tests/test_state_machine_runtime.py`** (22 tests)

- `TestStateDefinitions` (5): 8 states, 1 initial, 1 final, 10 transitions, all referenced states exist
- `TestValidTransitions` (8): T01, T02, T09, invalid, unknown, closed terminal, T10, T06
- `TestDraftToGatePassing` (6): no guards, valid pack, invalid pack, empty deliverables, startup proof, invalid proof
- `TestCheckTransition` (3): invalid blocked, valid non-draft, draft with pack

### Test Results

```
tests/test_state_machine_runtime.py: 23 passed (R1 blocked → R2 fix)
Full suite: 403 passed (380 + 23 new)
```

### R1 → R2 Fix

GPT R1 **blocked** — `check_draft_to_gate_passing()` returned `transition_allowed=True` when no guards provided (fail-open). Fixed to fail-closed:

- All guards must be explicitly checked and pass
- Any `None` guard (unchecked) → transition BLOCKED with error
- `test_no_guards_skipped` renamed to `test_no_guards_blocks_transition`
- Added `test_draft_gate_passing_pack_only_blocked` (pack without proof)
- `test_startup_proof_integration` now provides both pack and proof

### Coverage Matrix

| Capability | Status | Verified By |
|---|---|---|
| 8 states defined | Implemented | TestStateDefinitions (5 tests) |
| 10 transitions defined | Implemented | test_ten_transitions |
| draft→gate_passing guards | Implemented | TestDraftToGatePassing (6 tests) |
| evidence pack linter integration | Implemented | test_valid/invalid_pack |
| startup read gate integration | Implemented | test_startup_proof_integration |
| resolve_required_reads_path auto-detect | Used | check_draft_to_gate_passing |
| CLI interface | Implemented | main() with argparse |

### Known Limitations

1. Only draft → gate_passing guard conditions implemented; other transitions return validity-only
2. No persistent state storage — state must be tracked externally
3. No state machine visualization
4. human_required → gate_passing guard checks not yet implemented
5. gpt_reviewing exit condition guards not yet implemented
