# Role Boundaries for AA-2

---

## agent-acceptance

**Responsible for:**
- Defining Runner Contract schema (what fields a runner must accept/produce)
- Defining Runner State schema (what state a runner must track)
- Defining Runner Step Result schema (what each step must report)
- Defining Flow Runner Policy (runner is dev-frame execution layer reading agent-acceptance rules)
- Defining TaskSpec Runner Policy (machine-readable TaskSpec enforcement)
- Defining Run-Until-Terminal Policy (terminal=false → continue)
- Defining Next TaskSpec Consumption Policy (next_task_spec_path is mandatory)
- Defining Runner Failure Policy (fail-closed semantics)
- Writing tests that validate all runner contract rules

**Forbidden from:**
- Implementing oracle_flow_runner.py
- Implementing oracle_taskspec_runner.py
- Modifying dev-frame-opencode scripts
- Executing S3 Phase 3

---

## dev-frame-opencode

**Responsible for:**
- Implementing oracle_flow_runner.py and oracle_taskspec_runner.py
- Reading agent-acceptance runner contracts at runtime
- Validating all states against schemas before executing
- Running TaskSpecs step-by-step
- Writing RUNNER_STATE.json after each step
- Submitting evidence to GPT when required
- Writing FLOW_OUTCOME after each round

**Forbidden from:**
- Inventing runner semantics (must read from agent-acceptance)
- Treating ready_to_dispatch as dispatched
- Stopping when terminal=false
- Executing high-risk actions without human_required

---

## GPT

**Responsible for:**
- Reviewing evidence packs
- Deciding accepted/blocked/human_required
- Setting allow_next_stage
- Identifying missing evidence

---

## Boundary Decision Needed

| Question | Why It Matters |
|----------|---------------|
| Runner Contract belongs to agent-acceptance? | Normative authority — who defines runner rules |
| Runner Implementation belongs to dev-frame-opencode? | Execution ownership — who builds the runner |
| AA-2 should proceed before S3 Phase 3? | Sequencing — contracts before implementation |
| AA-2 only defines contracts, not runner code? | Scope boundary — what AA-2 can create |
