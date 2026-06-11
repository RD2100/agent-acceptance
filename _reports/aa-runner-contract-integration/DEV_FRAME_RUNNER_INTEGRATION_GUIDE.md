# Dev-Frame Runner Integration Guide

> How dev-frame-opencode should implement oracle_flow_runner.py in S3 Phase 3

---

## What to Build

1. **oracle_flow_runner.py**: Reads RUNNER_CONTRACT, runs step loop, persists RUNNER_STATE
2. **oracle_taskspec_runner.py**: Reads TASKSPEC, validates against schema, executes allowed actions

---

## Integration Points

### 1. Load Contracts at Startup

```python
runner_contract = json.loads(Path("contracts/RUNNER_CONTRACT.schema.json").read_text())
runner_state_schema = json.loads(Path("contracts/RUNNER_STATE.schema.json").read_text())
step_result_schema = json.loads(Path("contracts/RUNNER_STEP_RESULT.schema.json").read_text())
```

### 2. Validate All Inputs Before Execution

```python
# Before executing any step:
validate(input_outcome, FLOW_OUTCOME.schema.json)
validate(input_taskspec, TASKSPEC.schema.json)
validate(dispatch_result, DISPATCH_RESULT.schema.json)
```

### 3. Run-Until-Terminal Loop

```python
while runner_state["terminal"] == False:
    step_result = execute_step(runner_state["next_action"])
    write_step_result(step_result)
    runner_state["current_step"] += 1
    runner_state["terminal"] = step_result["terminal"]
    runner_state["next_action"] = step_result.get("next_action")
    runner_state["heartbeat"] = datetime.utcnow().isoformat()
    write_runner_state(runner_state)
```

### 4. Fail-Closed on Schema Violations

```python
if schema_missing or schema_invalid or outcome_missing or taskspec_invalid:
    write_step_result({
        "status": "step_failed",
        "terminal": True,
        "reason": f"Schema validation failed: {reason}"
    })
    sys.exit(1)
```

### 5. High-Risk Detection

```python
HIGH_RISK_ACTIONS = {"delete", "move", "rename", "clean_worktree", "overwrite_evidence"}
if any(a in task["allowed_actions"] for a in HIGH_RISK_ACTIONS) or task.get("high_risk"):
    write_step_result({
        "status": "step_human_required",
        "terminal": True,
        "reason": "High-risk action requires human confirmation"
    })
    sys.exit(2)
```

### 6. Resume After Crash

```python
if Path(state_path).exists():
    runner_state = json.loads(Path(state_path).read_text())
    if runner_state["terminal"] == False:
        resume_from_step(runner_state["current_step"])
```

---

## Reference Contracts

The runner must read these agent-acceptance files as normative authority:

| Contract | Path |
|----------|------|
| FLOW_OUTCOME schema | contracts/FLOW_OUTCOME.schema.json |
| TASKSPEC schema | contracts/TASKSPEC.schema.json |
| DISPATCH_RESULT schema | contracts/DISPATCH_RESULT.schema.json |
| RUNNER_CONTRACT schema | contracts/RUNNER_CONTRACT.schema.json |
| RUNNER_STATE schema | contracts/RUNNER_STATE.schema.json |
| RUNNER_STEP_RESULT schema | contracts/RUNNER_STEP_RESULT.schema.json |
| Terminal policy | policies/TERMINAL_STATE_POLICY.md |
| Autonomous progress | policies/AUTONOMOUS_PROGRESS_POLICY.md |
| Human required taxonomy | policies/HUMAN_REQUIRED_TAXONOMY.md |
