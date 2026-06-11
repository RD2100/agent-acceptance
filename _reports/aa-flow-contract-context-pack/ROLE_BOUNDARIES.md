# Role Boundaries

> AA-1 preliminary role boundary definition for GPT review

---

## GPT

**Responsible for:**
- Planning (what stages, what order)
- Reviewing (evidence inspection, gate evaluation)
- Re-reviewing (after fixes, re-evaluate)
- Arbitration (when evidence is ambiguous)
- Deciding: `accepted` / `blocked` / `human_required`
- Deciding: `allow_next_stage` true/false

**Forbidden from:**
- Directly modifying local files
- Directly executing S3 (that's dev-frame-opencode's job)
- Fabricating baseline
- Substituting for agent-acceptance's schema definitions

---

## agent-acceptance

**Responsible for:**
- Defining normative layer: schemas, policies, gates
- FLOW_OUTCOME schema
- TASKSPEC schema
- DISPATCH_RESULT schema
- Terminal state policy
- Dispatcher contract
- Autonomous progress policy
- Human_required taxonomy
- Stage gate policy
- Evidence pack minimum contract
- Acceptance gate tests

**Forbidden from:**
- Directly operating a browser
- Directly executing dev-frame-opencode business modifications
- Deleting, moving, or renaming dev-frame-opencode files
- Modifying ai-workflow-hub business code
- Fabricating GPT `accepted` decisions

---

## dev-frame-opencode

**Responsible for:**
- Local execution of tasks
- Generating evidence packs
- Chrome CDP handoff to GPT
- Monitoring GPT replies
- Writing FLOW_OUTCOME.json
- Running post-decision driver
- Executing TaskSpecs
- Following agent-acceptance contracts

**Forbidden from:**
- Inventing its own acceptance rules
- Bypassing agent-acceptance gates
- Treating `ready_to_dispatch` as `dispatched`
- Outputting final report when `terminal=false`
- Self-defining stage gate logic

---

## Boundary Decision Needed

| Question | Why It Matters |
|----------|---------------|
| Should Flow Contract enter agent-acceptance? | Ownership of normative authority |
| Should runner stay in dev-frame-opencode? | Execution vs. definition boundary |
| Should TaskSpec schema be in agent-acceptance? | Machine-readable contract authorship |
| Should FLOW_OUTCOME schema be in agent-acceptance? | Source of truth for automation decisions |
| Should terminal policy be in agent-acceptance? | Prevents execution layer from self-deciding stop |

Please GPT: confirm or revise these boundaries.
