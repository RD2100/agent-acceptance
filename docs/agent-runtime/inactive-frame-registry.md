# Inactive Frame Registry — RD2100 Agent Runtime v2

> 2026-05-30 | Phase 0-5
> Purpose: Prevent misuse. Register external projects that are referenced but NOT integrated.
> These are NOT active runtime participants. They have no data flow, no execution rights, no gate authority.

## Core Principle

**Registered ≠ Integrated.** These frames are documented as potential future participants.
They have no active data flow, no execution privileges, and no GateResult authority.
Their status is `inactive` until explicit activation conditions are met.

## Registry

### dev-frame

```yaml
status: inactive
role: orchestration_adapter_candidate
path: D:\dev-frame
data_flow: none
execution: forbidden
may_produce: { RunSpec: candidate_only, EvidenceIndex: historical_only, GateResult: forbidden }
may_consume: { TaskSpec: "1.0.0" }
notes: Not a git repo. R3 adapter_dry_run authorized but never executed.
```

**Activation triggers** (any one):
- dev-frame becomes a git repo with versioned commits
- Begins producing RunSpec records
- Adapter dry-run requested and approved
- Active consumption by agent-acceptance requested

### dev-frame-opencode

```yaml
status: inactive
role: execution_runtime_candidate
path: D:\dev-frame-opencode
data_flow: none
execution: forbidden
may_produce: { RunSpec: candidate_only, EvidenceIndex: historical_only, GateResult: forbidden }
may_consume: { TaskSpec: "1.0.0", RuntimeExecutionRequest: future_candidate }
notes: Dirty baseline as of 2026-06-14. Contains real source/config changes, paper CLI expansion, large tasks.yaml delta, and large untracked workspace. Not eligible for submodule pinning.
```

**Activation triggers** (all required):
- Worktree reaches an owner-approved clean commit
- Paper-domain CLI changes receive separate review or are explicitly de-scoped
- Runtime execution request is created and human-gated
- Boundary envelope and source lock are defined for any data flow

### devframe-control-plane

```yaml
status: inactive
role: control_plane_candidate
path: D:\devframe-control-plane
data_flow: none
execution: forbidden
may_produce: { RunSpec: candidate_only, EvidenceIndex: historical_only, GateResult: forbidden }
may_consume: { RepoBaselineRecord: future_candidate, RuntimeExecutionRequest: future_candidate }
notes: Dirty baseline as of 2026-06-14 is artifact-policy focused: run_history.jsonl, .coverage, and CLI test JSON artifacts. Not eligible for submodule pinning until owner policy is applied.
```

**Activation triggers** (all required):
- Worktree reaches an owner-approved clean commit
- Artifact ignore/archive/commit policy is resolved
- Control-plane execution is explicitly human-gated
- Boundary envelope and source lock are defined for any data flow

### test-frame

```yaml
status: inactive
role: controlled_verification_runtime_candidate
path: D:\test-frame
data_flow: none
execution: forbidden
may_produce: { EvidenceIndex: historical_observation_only, GateResult: forbidden }
may_consume: { TaskSpec: "1.0.0" }
notes: Bootstrap package was externally committed at 215d1e4. Remaining dirty state exists as of 2026-06-14. It is not a plugin, not a governance source of truth, and not a verdict authority.
```

**Activation triggers** (any one):
- Current evidence requested (not historical)
- Approved run requested and human-gated
- Attribution execution requested
- Orchestrator/CLI scheduled for execution

### devframe-system

```yaml
status: inactive
role: future_superproject_control
path: D:\devframe-system
data_flow: none
execution: forbidden
may_produce: { RepoBaselineRecord: future_candidate, SuperprojectLock: future_candidate, GateResult: forbidden }
may_consume: { RepoBaselineRecord: future_candidate, BoundaryEnvelope: future_candidate }
notes: Target directory does not exist as of 2026-06-14. Physical bootstrap and submodule add remain blocked by dirty source repositories. Contract-only planning is allowed in agent-acceptance reports.
```

**Activation triggers** (all required):
- All source repositories reach owner-approved clean commits, or human explicitly authorizes dirty-aware skeleton without submodules
- Local-only portability status is documented
- Source lock records are defined
- Human approves physical directory creation

---

## Hard Boundaries (Active Regardless of Status)

These rules apply even to inactive frames:

1. **GateResult**: External frames MUST NOT produce GateResult. Only agent-acceptance may sign pass/fail.
2. **Historical evidence**: Evidence from inactive frames is historical only. Cannot be used as current GateResult evidence.
3. **Execution**: No external frame may execute code, scripts, tests, aggregators, or CLI without human gate.
4. **Evidence freshness**: `freshness=current` requires an `approved_run_id`. Historical artifacts default to `stale_or_unknown`.

---

## Activation Process

When a frame meets any activation trigger:

1. Create `frame-manifest.yaml` (schema: `schemas/draft/frame-manifest.schema.draft.json`)
2. Update this registry: status → `activating`
3. Define data flow contract using `boundary-envelope.schema.draft.json`
4. Human reviewer approves the transition
5. Status → `active`

---

## Why This Registry Exists (Instead of a Runtime Checker)

We deliberately chose a lightweight registry over a runtime compatibility checker because:

1. **No active data flow exists** — a checker would validate interactions that never happen
2. **Checker creates governance illusion** — "we have a mechanism" when it checks nothing real
3. **Registry prevents misuse without pretending integration** — it says "these are NOT integrated"
4. **Activation triggers are explicit** — no accidental promotion from inactive to active
