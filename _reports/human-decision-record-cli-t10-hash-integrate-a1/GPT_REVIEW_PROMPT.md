## GPT Review Prompt — HUMAN-DECISION-RECORD-CLI-T10-HASH-INTEGRATE-A1

You are reviewing the deliverables for task **HUMAN-DECISION-RECORD-CLI-T10-HASH-INTEGRATE-A1**.

### Task Definition

Per the authorization from HUMAN-DECISION-RECORD-HASH-MANIFEST-BIND-A1: Integrate hash computation into the CLI create subcommand, hash verification into the CLI validate subcommand, and propagate repo_root through the T10 state machine runtime guard. This completes the end-to-end evidence integrity chain.

### Deliverables

1. **`scripts/human_decision_record.py`** (~300 lines) — CLI --compute-hashes, --repo-root flags
2. **`scripts/state_machine_runtime.py`** (~360 lines) — T10 repo_root propagation
3. **`tests/test_human_decision_record.py`** (54 tests, +2 CLI integration)
4. **`tests/test_state_machine_runtime.py`** (33 tests, +2 T10 hash integration)

### Review Criteria

1. **End-to-End Chain**: create(hash) → validate(hash) → T10(hash) fully connected?
2. **Tamper Detection**: Does the chain correctly detect evidence file tampering?
3. **CLI Usability**: Are the new CLI flags intuitive and properly wired?
4. **Test Coverage**: 4 new tests sufficient for CLI+T10 hash integration?

### Expected Verdict Format

```
verdict: accepted | accepted_with_limitation | blocked | human_required
run_id: HUMAN_DECISION_RECORD_CLI_T10_HASH_INTEGRATE_A1_20260609T214000_RD
findings: [list key findings]
next_task_authorization: [next task or "none"]
---END_OF_GPT_RESPONSE---
```
