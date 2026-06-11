You are the Dev Frame OpenCode / agent-acceptance review agent.

I am uploading the AA-1 Flow Contract Integration Review Pack.

## What Was Done

AA-1 Phase 1 has been completed in agent-acceptance. The following was created:

### Contracts (contracts/)
- FLOW_OUTCOME.schema.json — Three-layer flow state: transport → business → dispatch
- TASKSPEC.schema.json — Machine-readable task specification (not Markdown-only)
- DISPATCH_RESULT.schema.json — 6 dispatch states with ready_to_dispatch ≠ dispatched

### Policies (policies/)
- TERMINAL_STATE_POLICY.md — 6 terminal states; terminal=false must continue
- DISPATCHER_POLICY.md — Decision matrix: accepted→dispatch, human_required→stop
- AUTONOMOUS_PROGRESS_POLICY.md — What auto-advances vs requires human
- HUMAN_REQUIRED_TAXONOMY.md — 8-category taxonomy
- STAGE_GATE_POLICY.md — Gate definitions, GPT vs gate priority
- EVIDENCE_PACK_CONTRACT.md — Minimum pack requirements

### Tests (tests/)
- 5 test files, 30 tests, all passing
- 6 test fixtures (valid and invalid cases)

## What You Must Judge

1. Are the contracts complete? Do FLOW_OUTCOME, TASKSPEC, and DISPATCH_RESULT schemas cover the critical rules?

2. Are the policies complete? Do they address:
   - terminal=false must continue (not stop)
   - ready_to_dispatch vs dispatched distinction
   - transport success vs business accepted distinction
   - human_required taxonomy
   - autonomous progress boundaries

3. Are the tests sufficient? Do 30 tests adequately cover the critical rules?

4. Can dev-frame-opencode now integrate against these contracts?
   - Read FLOW_OUTCOME schema to validate output
   - Read DISPATCH_RESULT schema to produce correct dispatch states
   - Read TERMINAL_STATE_POLICY to know when to stop vs continue

5. May S3 Phase 2 resume now that AA-1 contracts exist?

6. Are there any gaps that must be addressed before S3 Phase 2?

## Output Format Required

```
Overall Judgment: [accepted / partial / blocked / human_required]
AA-1 Accepted: [yes / no]
Contracts Complete: [yes / no]
Policies Complete: [yes / no]
Tests Sufficient: [yes / no]
Dev-frame Integration Allowed: [yes / no]
S3 Phase 2 May Resume: [yes / no]

Identified Gaps:
- [list or "none"]

Required Next Action:
- [concrete step]
```

## Rules

- If schemas are missing critical fields → not accepted
- If policies fail to distinguish ready_to_dispatch from dispatched → not accepted
- If tests are insufficient → not accepted
- If deletion, movement, renaming, cleanup, or evidence overwrite occurred → human_required
- Safety check is included in the review pack — verify it
