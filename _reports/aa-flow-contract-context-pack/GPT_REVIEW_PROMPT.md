You are the Dev Frame OpenCode / agent-acceptance architecture review agent.

I am uploading the AA-1 Flow Contract Context Pack.

## Background

The current dev-frame-opencode framework has demonstrated Oracle GPT Review automation:
- Evidence pack generation and Chrome CDP upload
- GPT reply monitoring and parsing
- FLOW_OUTCOME writing
- Post-decision driver that generates next-stage TaskSpecs
- S3 Phase 2 TaskSpec generated and allowed by GPT

But the flow repeatedly halts due to structural contract gaps:
- `ready_to_dispatch` is written but never consumed
- TaskSpecs are generated but never auto-executed
- `terminal=false` flows produce terminal reports
- Markdown reports are used as the basis for automation decisions
- dev-frame-opencode self-defines acceptance rules that should come from agent-acceptance

## Current Judgment

These are not script bugs. They are acceptance-level contract gaps. The fix belongs in agent-acceptance, not in ad-hoc dev-frame-opencode patches.

## What You Must Judge

1. **Flow Contract ownership**: Should the Flow Contract (schemas, policies, gates) live in agent-acceptance?
   - yes: agent-acceptance defines normative layer
   - no: keep in dev-frame-opencode (explain why)

2. **dev-frame-opencode role**: Should dev-frame-opencode be a pure execution layer that reads agent-acceptance contracts?
   - yes: execution layer only
   - no: dev-frame-opencode may also define rules (explain which ones)

3. **AA-1 sequencing**: Should AA-1 (Flow Contract definition) execute before S3 Phase 2?
   - yes: define contracts first, then execute with contracts
   - no: execute S3 Phase 2 first (explain risk assessment)

4. **Minimum scope**: Is the proposed AA-1 scope correct?
   - Review PROPOSED_AA1_SCOPE.md
   - Are there files that should be removed?
   - Are there files missing that should be added?
   - Are any files misplaced (should be in dev-frame-opencode instead)?

5. **Schema requirements**: Should agent-acceptance define these schemas?
   - FLOW_OUTCOME.schema.json
   - TASKSPEC.schema.json
   - DISPATCH_RESULT.schema.json

6. **Policy requirements**: Should agent-acceptance define these policies?
   - TERMINAL_STATE_POLICY.md
   - DISPATCHER_POLICY.md
   - AUTONOMOUS_PROGRESS_POLICY.md
   - HUMAN_REQUIRED_TAXONOMY.md
   - STAGE_GATE_POLICY.md
   - EVIDENCE_PACK_CONTRACT.md

7. **Implementation permission**: May the agent-acceptance agent begin implementing AA-1?
   - accepted: proceed with full scope
   - partial: proceed with approved subset only
   - blocked: do not proceed (explain why)
   - human_required: cannot proceed without human (specify what is needed)

8. **Implementation boundaries**: If allowed, what are the hard boundaries?
   - Confirm: no S3 execution
   - Confirm: no dev-frame-opencode script modifications
   - Confirm: no ai-workflow-hub business code changes
   - Confirm: no file deletion, movement, or renaming
   - Confirm: no worktree cleanup
   - Confirm: no evidence overwrite

## Output Format Required

Please structure your response with these exact fields for machine parsing:

```
Overall Judgment: [accepted / partial / blocked / human_required]
Flow Contract Belongs To agent-acceptance: [yes / no]
AA-1 Should Proceed Before S3 Phase 2: [yes / no]
Dev-Frame Is Pure Execution Layer: [yes / no]

Approved Scope:
- [list approved files to create]

Rejected Scope:
- [list files that should NOT be created, with reasons]

Additional Files Needed:
- [list files that should be ADDED to scope]

Implementation May Begin: [yes / no]
If partial: allowed subset is [list]

Hard Boundaries Confirmed:
- No S3 execution: [yes]
- No dev-frame script modification: [yes]
- No ai-workflow-hub changes: [yes]
- No file deletion/movement/renaming: [yes]
- No worktree cleanup: [yes]
- No evidence overwrite: [yes]

Risks Identified:
- [risk items]

Required Next Action:
- [concrete next step]
```

## Rules

- If evidence is insufficient, do NOT return `accepted`
- If any operation involves deletion, movement, renaming, cleanup, or evidence overwrite → `human_required`
- If only partial implementation is safe → return `partial` with the allowed subset explicitly listed
- If the proposed approach is fundamentally wrong → return `blocked` with explanation
