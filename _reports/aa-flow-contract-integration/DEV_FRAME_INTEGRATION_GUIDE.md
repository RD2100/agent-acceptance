# Dev-Frame Integration Guide

> How dev-frame-opencode should consume agent-acceptance contracts

---

## Integration Points

### 1. Read FLOW_OUTCOME schema before writing FLOW_OUTCOME.json

Before `oracle_post_decision_driver.py` writes FLOW_OUTCOME.json, it must validate against `contracts/FLOW_OUTCOME.schema.json`:

```python
import json
from pathlib import Path

schema = json.loads(Path("contracts/FLOW_OUTCOME.schema.json").read_text())
# validate instance against schema
# if terminal=false and no next_task_spec_path → BLOCK
```

### 2. Read TASKSPEC schema when generating next TaskSpec

When `oracle_post_decision_driver.py` generates a next-stage TaskSpec, it must produce valid JSON (not Markdown-only) that satisfies `contracts/TASKSPEC.schema.json`.

### 3. Read DISPATCH_RESULT schema before executing dispatch

When `oracle_decision_dispatcher.py` or `oracle_flow_state.py` writes a dispatch result, it must validate against `contracts/DISPATCH_RESULT.schema.json`.

### 4. Read TERMINAL_STATE_POLICY before writing terminal reports

The runner must check `terminal` field in FLOW_OUTCOME. If `terminal=false`, do NOT output a final report — instead, consume `next_task_spec_path`.

### 5. Read DISPATCHER_POLICY for correct dispatch behavior

The dispatcher must follow the decision matrix in `policies/DISPATCHER_POLICY.md`:
- accepted + allow_next_stage → dispatch
- human_required → stop
- unknown → fail-closed

### 6. Read AUTONOMOUS_PROGRESS_POLICY before auto-advancing

Before automatically advancing to the next stage, check if any next-stage action requires human confirmation per `policies/AUTONOMOUS_PROGRESS_POLICY.md`.

---

## Recommended dev-frame changes (after AA-1 accepted)

1. Add schema validation to `oracle_post_decision_driver.py`
2. Add `should_execute_next` check to `oracle_decision_dispatcher.py`
3. Add terminal=false continuation logic to the runner
4. Add `dispatch_status` distinction (ready_to_dispatch vs dispatched) to all relevant scripts

These changes belong in dev-frame-opencode, NOT in agent-acceptance.
