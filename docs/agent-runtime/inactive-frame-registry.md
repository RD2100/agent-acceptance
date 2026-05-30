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

### test-frame

```yaml
status: inactive
role: evidence_provider_candidate
path: D:\test-frame
data_flow: none
execution: forbidden
may_produce: { EvidenceIndex: historical_observation_only, GateResult: forbidden }
may_consume: { TaskSpec: "1.0.0" }
notes: R2 evidence provider. 23 forbidden actions. All evidence is historical only.
```

**Activation triggers** (any one):
- Current evidence requested (not historical)
- Approved run requested and human-gated
- Attribution execution requested
- Orchestrator/CLI scheduled for execution

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
