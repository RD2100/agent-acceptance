# Capability Selection Policy -- CR1

> Batch CR-A, 2026-05-27
> Defines the mandatory capability selection workflow for agent task execution.

## Selection Workflow

Every agent task must follow this sequence BEFORE execution:

```
1. IDENTIFY task type from routing matrix
2. LOOKUP preferred capability
3. CHECK preferred capability status (available/stale/forbidden)
4. DECLARE expected capabilities for this task
5. EXECUTE using preferred (if available) or fallback (if not)
6. RECORD in Capability Routing Audit
```

## Step Detail

### Step 1: Identify Task Type

Classify the task into one of the 13 types in the routing matrix. If a task spans multiple types, select the PRIMARY type. Secondary types should also be recorded but the primary type determines the main routing decision.

### Step 2: Lookup Preferred Capability

Consult `task-capability-routing-matrix.md`. The preferred capability is the first-choice tool for this task type.

### Step 3: Check Capability Status

| Status | Condition | Action |
|--------|-----------|--------|
| available | Capability is accessible and meets pre-check | Use preferred capability |
| stale | Capability exists but freshness cannot be confirmed | Use fallback; record reason |
| empty | Capability exists but has no usable data (e.g., CodeGraph 0 files) | Use fallback; record reason |
| forbidden | Capability is not authorized in current phase | Use fallback; record reason; do NOT attempt to use |
| unavailable | Capability tool is not present or not accessible | Use fallback; record reason |

### Step 4: Declare Expected Capabilities

Before task execution, explicitly state:
- What capability is expected for this task type
- What status check was performed
- What capability will actually be used
- If using fallback, why preferred was not used

### Step 5: Execute

Use the declared capability. If using fallback, ensure the fallback is listed in the routing matrix and is not in the forbidden list.

### Step 6: Record

At task completion, populate the Capability Routing Audit table in the ExecutionReport.

## Decision Rules

| Rule | Description |
|------|-------------|
| **Preferred first** | Always attempt preferred capability before fallback |
| **Status gate** | Check status before use; stale/empty/forbidden -> fallback |
| **Explain skip** | If must_explain_if_skipped=true for preferred capability, explanation is required |
| **Evidence required** | Evidence of status check must be included (e.g., codegraph_status output) |
| **No forbidden** | Forbidden capability must never be used, even as fallback |
| **No auto-trigger** | No capability may be auto-triggered; all require explicit selection |
| **Human gate** | Capabilities with requires_human_gate=true need approval before first use |
| **Freshness first** | Capabilities with freshness_required=true must have freshness verified before each use |

## Skipped Capability Log

When a preferred capability is skipped, the agent MUST log:

```
CAPABILITY SKIPPED: <capability_name>
REASON: <stale/empty/forbidden/unavailable>
EVIDENCE: <status check output>
FALLBACK: <fallback capability used>
```

## Audit Format

Every ExecutionReport must include:

```markdown
## Capability Routing Audit

| Task Area | Expected Capability | Status | Used? | Reason If Not Used | Fallback | Evidence |
|---|---|---|---|---|---|---|
| <task type> | <preferred> | <available/stale/empty/forbidden> | <yes/no> | <reason or N/A> | <fallback or N/A> | <evidence reference> |
```
