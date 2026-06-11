## GPT Review Prompt — HUMAN-DECISION-RECORD-INTEGRATE-T10-A1

You are reviewing the deliverables for task **HUMAN-DECISION-RECORD-INTEGRATE-T10-A1**.

### Task Definition

Per HANDOFF_WORKFLOW_HARDENING_PLAN.md and the authorization from the previous task (HUMAN-REQUIRED-DECISION-RECORD-TEMPLATE-A1):

Integrate `human_decision_record.py` into `state_machine_runtime.py` to enforce the T10 transition guard for `human_required → gate_passing`.

**PROCESS_STATE_MACHINE.json T10 guard**: `human_decision_recorded AND decision_evidence_attached`

### Deliverables

This evidence pack contains:

1. **`scripts/state_machine_runtime.py`** (~350 lines, modified)
   - New `check_human_required_to_gate_passing(decision_record_path)` function
   - Validates T10 guards by calling `human_decision_record.validate_record()`
   - Extracts exit_conditions: human_decision_recorded, decision_evidence_attached
   - Fail-closed: both guards must be explicitly checked and pass
   - Updated `check_transition()` dispatches to T10 for human_required → gate_passing
   - New CLI `--decision-record-path` argument

2. **`tests/test_state_machine_runtime.py`** (31 tests, +8 new)
   - `TestHumanRequiredToGatePassing` (8 tests):
     - Fail-closed without record
     - Valid record passes both guards
     - No evidence blocks
     - Nonexistent record blocks
     - Invalid JSON blocks
     - Tampered exit_conditions detected
     - check_transition T10 dispatch
     - check_transition T10 without record blocked

### Review Criteria

Please evaluate:

1. **T10 Guard Integration**: Does `check_human_required_to_gate_passing()` correctly enforce both `human_decision_recorded` AND `decision_evidence_attached`?

2. **Fail-Closed Behavior**: When no record is provided, or the record is invalid/incomplete, does the system correctly block T10 transition?

3. **Integration with human_decision_record**: Is the call to `validate_record()` correct? Are exit_conditions properly extracted?

4. **Test Coverage**: Are 8 new T10 tests sufficient? Are there missing edge cases?

5. **State Machine Completeness**: With T01 and T10 now having guard implementations, is the state machine runtime progressing toward full enforcement?

### Expected Verdict Format

```
verdict: accepted | accepted_with_limitation | blocked | human_required
run_id: HUMAN_DECISION_RECORD_INTEGRATE_T10_A1_20260609T211000_RD
findings: [list key findings]
next_task_authorization: [next task or "none"]
---END_OF_GPT_RESPONSE---
```
