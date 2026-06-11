# AA-2 Runner Contract Context Summary

> Generated: 2026-06-02
> Purpose: Context for GPT to decide whether AA-2 should proceed

---

## Current State

- **AA-1**: Accepted. agent-acceptance now has FLOW_OUTCOME, TASKSPEC, DISPATCH_RESULT schemas + 6 policies.
- **S3 Phase 2**: Accepted. dev-frame-opencode integrated with Oracle gate.
- **Remaining gap**: dev-frame-opencode can generate next TaskSpec but lacks a unified Flow Runner / TaskSpec Runner contract.

## Current Problems

1. **next_task_spec_path generated but not consumed**: No contractual requirement forces the runner to consume the next TaskSpec.
2. **terminal=false still stops**: No runner-level enforcement of "terminal=false means continue."
3. **Markdown-only TaskSpec**: Without runner contract, Markdown TaskSpecs may be used as execution authority.
4. **Runner unclear about stop/continue**: No contract defines what conditions trigger stop vs. continue at the runner level.
5. **dev-frame may re-invent runner semantics**: Execution layer may self-define rules without reading agent-acceptance contracts.
6. **Long-running automation lacks unified runner contract**: No contract for step-by-step runner state, recovery, or failure handling.

## What GPT Must Decide

1. Should Runner Contract be defined by agent-acceptance?
2. Should Runner implementation stay in dev-frame-opencode?
3. Should AA-2 proceed before S3 Phase 3?
4. Is the proposed AA-2 scope correct?
5. Which runner schemas, policies, and tests should be created?
6. What must NOT go into agent-acceptance?
7. May the agent begin implementing AA-2?

## Current Stage State

| Stage | Status |
|-------|--------|
| AA-1 Flow Contract | Accepted |
| S3 Phase 2 | Accepted |
| AA-2 Runner Contract | Pending GPT approval |
| S3 Phase 3 (runner impl) | Blocked on AA-2 |
