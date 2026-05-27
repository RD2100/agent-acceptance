# Coding Agent Capability Prompt -- CR2

> Batch CR-A, 2026-05-27
> Mandatory pre-task and post-task capability routing template for executor agents.

## Pre-Task: Capability Selection (MUST complete before execution)

Before starting any non-trivial task, the agent MUST:

### 1. Identify Task Type

Classify the task into one of the 13 types from `task-capability-routing-matrix.md`. If the task spans multiple types, select the PRIMARY type.

```
TASK TYPE: <one of: code_structure, string_search, file_read, schema_validation, doc_policy, rule_enforcement, negative_test, blackboard, test_frame, dev_frame, local_skill, memory, script_queue>
```

### 2. Declare Expected Capabilities

```
EXPECTED CAPABILITY: <preferred capability name>
STATUS CHECK: <command to run or doc to check>
EXPECTED STATUS: <available/stale/empty/forbidden/unavailable>
```

If the preferred capability is not usable, declare the fallback:

```
FALLBACK CAPABILITY: <fallback name>
SKIP REASON: <why preferred was skipped>
```

### 3. Verify Forbidden Capabilities

```
FORBIDDEN FOR THIS TASK:
- <capability 1>: <why forbidden>
- <capability 2>: <why forbidden>
```

### 4. Confirm Phase Boundary

```
CURRENT PHASE: <Phase 0-5 / R0-R7 / Phase 6>
PHASE CONSTRAINTS APPLY: <relevant constraints from tool-policy.md>
```

## During Task: Capability Usage

- Use ONLY the declared capabilities (preferred or fallback)
- Do NOT add capabilities mid-task without re-declaring
- If a capability fails, log the failure and use fallback; do NOT try a third option without declaring

## Post-Task: Capability Routing Audit (MUST include in ExecutionReport)

Every ExecutionReport MUST include this section:

```markdown
## Capability Routing Audit

| Task Area | Expected Capability | Status | Used? | Reason If Not Used | Fallback | Evidence |
|---|---|---|---|---|---|---|
| <task type> | <preferred> | <status> | yes/no | <reason or N/A> | <fallback or N/A> | <evidence> |
```

### Field Definitions

| Field | Values | Description |
|-------|--------|-------------|
| Task Area | code_structure, string_search, file_read, schema_validation, doc_policy, rule_enforcement, negative_test, blackboard, test_frame, dev_frame, local_skill, memory, script_queue | Primary task type |
| Expected Capability | capability name from inventory | Preferred capability per routing matrix |
| Status | available, stale, empty, forbidden, unavailable | Result of pre-check |
| Used? | yes, no | Was preferred capability actually used? |
| Reason If Not Used | e.g., "index empty (0 files)", "R1-SNAPSHOT-MCP not authorized" | Required if Used?=no |
| Fallback | capability name or N/A | Fallback actually used |
| Evidence | e.g., "codegraph_status output", "R1 policy docs" | Evidence of status check |

### Example: Empty CodeGraph

```markdown
## Capability Routing Audit

| Task Area | Expected Capability | Status | Used? | Reason If Not Used | Fallback | Evidence |
|---|---|---|---|---|---|---|
| code_structure | CodeGraph | empty | no | agent-acceptance index: 0 files indexed | rg + Read | codegraph_status output |
```

### Example: Blackboard Task

```markdown
## Capability Routing Audit

| Task Area | Expected Capability | Status | Used? | Reason If Not Used | Fallback | Evidence |
|---|---|---|---|---|---|---|
| blackboard | N/A | forbidden | no | R1-SNAPSHOT-MCP not authorized | FS snapshot | R1 policy docs, state.json checksum |
```

### Example: All Preferred Available

```markdown
## Capability Routing Audit

| Task Area | Expected Capability | Status | Used? | Reason If Not Used | Fallback | Evidence |
|---|---|---|---|---|---|---|
| string_search | rg | available | yes | N/A | N/A | rg output |
| doc_policy | Runtime Docs + rg | available | yes | N/A | N/A | doc path reference |
```

## Hard Stop Conditions

If the Capability Routing Audit is **missing** from an ExecutionReport, the report is incomplete. Reviewer should mark `needs_revision`.

If a **forbidden capability** appears in the Used? column as `yes`, the batch is `blocked`.

If the **reason for skipping** a preferred capability is empty when `used?=no`, the report is `needs_revision`.
