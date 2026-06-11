# AA-1 Flow Contract Context Summary

> Generated: 2026-06-02
> Purpose: Context for GPT to decide whether AA-1 should proceed

---

## 1. Current Problem

Dev Frame OpenCode automation framework has demonstrated these capabilities:

- Evidence pack generation
- Chrome CDP auto-upload to GPT
- GPT reply monitoring
- Decision parsing from GPT reply
- FLOW_OUTCOME.json writing
- Post-decision driver generating next-stage TaskSpec

But structural problems persist:

- **terminal=false yet the agent stops**: S2 Round-3 was accepted, S3 Phase 1 was accepted, S3 Phase 2 TaskSpec was generated — yet the automation halted instead of consuming it
- **next_task_spec generated but not consumed**: The TaskSpec exists on disk but no contract forces its execution
- **ready_to_dispatch vs dispatched semantic confusion**: Post-decision driver writes `ready_to_dispatch` but there's no contract forcing actual dispatch
- **transport success vs business accepted**: Upload to GPT succeeds, but GPT's reply may be `human_required` or `blocked` — yet transport success is sometimes treated as acceptance
- **Markdown reports used as automation truth**: Reports drive decisions instead of machine-readable schemas
- **dev-frame-opencode over-decides**: The execution layer self-defines gate logic instead of reading it from agent-acceptance

## 2. Core Judgment

These are NOT script-level bugs. They are acceptance-level contract gaps.

The solution is to define a unified Flow Contract in agent-acceptance, making dev-frame-opencode a pure execution layer that reads schemas, policies, and gates from agent-acceptance.

## 3. What GPT Must Decide

- Should Flow Contract live in agent-acceptance?
- Should AA-1 execute before S3 Phase 2?
- What is the minimum viable scope for AA-1?
- Which schemas, policies, and tests should be created?
- What must stay in dev-frame-opencode (execution layer)?
- Is the proposed AA-1 scope correct, or should it be adjusted?

## 4. Current Stage State

| Stage | Status |
|-------|--------|
| S2 human_required | Resolved (human attestation done) |
| S3 Phase 1 | GPT accepted |
| S3 Phase 2 | GPT allowed but not yet executed |
| Current blocker | Lack of acceptance-level flow contract |
