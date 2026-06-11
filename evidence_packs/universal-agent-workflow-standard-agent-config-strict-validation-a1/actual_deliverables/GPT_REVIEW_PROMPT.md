# GPT Review Prompt

**Task ID**: {{TASK_ID}}
**Run ID**: {{RUN_ID}}

## Review Instructions

You are reviewing the implementation of strict validation logic for the AWSP (Agent Workflow Standard Project) agent configuration scaffold. The task adds fail-closed validation checks to `validate_scaffold()` in `scripts/awsp_scaffold.py`.

### Focus Areas

1. **Governance Boolean Checks**
   - Verify that governance flags are checked for strict boolean `True` (not just truthy values).
   - Confirm that `False`, `None`, missing keys, and non-boolean truthy values (e.g. `1`, `"yes"`) all correctly trigger fail-closed errors.
   - Check that the error messages clearly identify which flag failed validation.

2. **GATE_CONFIG Depth Validation**
   - Verify that each gate in `GATE_CONFIG` is checked for `enabled=True` and `block_on_failure=True`.
   - Confirm that the `startup_read_gate` is additionally checked for `strict_mode=True`.
   - Check that missing gates or missing fields within gates produce appropriate errors.

3. **REQUIRED_READS Structure Validation**
   - Verify that each entry must have `path`, `evidence_level`, `must_read_at_startup`, and `fail_closed_if_missing`.
   - Confirm that P0 entries enforce strict flags (all strict fields must be `True`).
   - Check that `evidence_level` is restricted to `P0` or `P1` only.
   - Verify that malformed entries (missing fields, wrong types, invalid evidence levels) are all rejected.

### Review Checklist

- [ ] Validation logic is fail-closed: invalid configs are rejected, not silently accepted.
- [ ] Error messages are descriptive and identify the specific failing field.
- [ ] No validation gaps: all three areas (governance, gates, reads) are covered.
- [ ] Test coverage includes positive (valid config passes) and negative (invalid config fails) cases.
- [ ] No secrets, credentials, or destructive operations in the code.
- [ ] Changes are minimal and focused on the validation task.

### Test Adequacy

- 9 new tests in `TestStrictValidation` class.
- 51 total tests in `test_cross_project_scaffold.py` all passing.
- 556 full suite tests all passing with no regressions.

Assess whether the test coverage is sufficient for the validation logic added. Identify any edge cases that may be missing.

## Response Format

Provide your review in the following format:

```
overall_judgment: PASS | CONDITIONAL_PASS | FAIL
confidence: HIGH | MEDIUM | LOW
findings:
  - category: <governance | gates | reads | tests | other>
    severity: <critical | major | minor | info>
    description: <finding description>
recommendations:
  - <recommendation text>
```

---END_OF_GPT_RESPONSE---
