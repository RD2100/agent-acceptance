You are the Dev Frame OpenCode / agent-acceptance architecture review agent.

I am uploading the AA-2 Runner Contract Context Pack.

## Background

AA-1 Flow Contract Integration is **accepted**. agent-acceptance now defines:
- FLOW_OUTCOME.schema.json — three-layer flow state
- TASKSPEC.schema.json — machine-readable task specification
- DISPATCH_RESULT.schema.json — 6 state dispatch result
- TERMINAL_STATE_POLICY — 6 terminal states, terminal=false must continue
- DISPATCHER_POLICY — decision matrix: accepted→dispatch, human_required→stop
- AUTONOMOUS_PROGRESS_POLICY — what auto-advances vs requires human
- HUMAN_REQUIRED_TAXONOMY — 8-category classification
- STAGE_GATE_POLICY — gate definitions, GPT vs gate priority
- EVIDENCE_PACK_CONTRACT — minimum pack requirements

S3 Phase 2 is **accepted**. dev-frame-opencode has integrated with Oracle gate.

## Remaining Structural Gap

dev-frame-opencode can generate next TaskSpec, but has no **Runner Contract** — the layer that:
1. Binds FLOW_OUTCOME + TASKSPEC + DISPATCH_RESULT into a runnable loop
2. Enforces terminal=false → continue at runtime
3. Consumes next_task_spec_path automatically
4. Produces step-by-step runner state for recovery
5. Fail-closes on schema violations
6. Triggers human_required on high-risk actions

Without a runner contract, the same structural failures can recur at the execution layer.

## What You Must Judge

1. **Runner Contract ownership**: Should agent-acceptance define the Runner Contract?
   - yes: agent-acceptance defines schemas/policies for runner behavior
   - no: explain why

2. **Runner Implementation ownership**: Should dev-frame-opencode implement the runner?
   - yes: dev-frame builds oracle_flow_runner.py / oracle_taskspec_runner.py
   - no: explain why

3. **AA-2 sequencing**: Should AA-2 proceed before S3 Phase 3?
   - yes: define contracts before implementing runner
   - no: explain risk

4. **AA-2 scope**: Is the proposed scope correct?
   - Review PROPOSED_AA2_SCOPE.md
   - Are 3 schemas sufficient? (RUNNER_CONTRACT, RUNNER_STATE, RUNNER_STEP_RESULT)
   - Are 5 policies sufficient? (FLOW_RUNNER, TASKSPEC_RUNNER, RUN_UNTIL_TERMINAL, NEXT_TASKSPEC_CONSUMPTION, RUNNER_FAILURE)
   - Are 5 test files + 6 fixtures sufficient?

5. **Implementation permission**: May the agent begin AA-2 Phase 1?
   - accepted: full scope
   - partial: approved subset only
   - blocked: do not proceed
   - human_required: cannot proceed

## Output Format Required

```
Overall Judgment: [accepted / partial / blocked / human_required]
Runner Contract Belongs To agent-acceptance: [yes / no]
Runner Implementation Belongs To dev-frame-opencode: [yes / no]
AA-2 Should Proceed Before S3 Phase 3: [yes / no]

Approved Scope:
- [list approved files]

Rejected Scope:
- [list rejected files with reasons]

Additional Files Needed:
- [list or "none"]

Implementation May Begin: [yes / no]
If partial: allowed subset is [list]

Hard Boundaries:
- No S3 Phase 3 execution: [yes]
- No dev-frame script modification: [yes]
- No ai-workflow-hub changes: [yes]
- No file deletion/movement/renaming: [yes]
- No worktree cleanup: [yes]
- No evidence overwrite: [yes]
- No runner implementation (only contracts): [yes]
- No modification of existing AA-1 contracts/policies: [yes]

Risks Identified:
- [risk items]

Required Next Action:
- [concrete step]
```

## Rules

- AA-2 defines runner CONTRACTS only, never implements runner code
- If evidence is insufficient → do NOT return accepted
- If any operation involves deletion, movement, renaming, cleanup → human_required
- If only partial implementation is safe → partial with explicit allowed subset
- Existing AA-1 contracts/policies must not be modified in core semantics
