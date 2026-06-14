# Devframe-System Route Decision Packet

Status: human decision required
Owner system: agent-acceptance
Related gate: `docs/agent-runtime/devframe-system-activation-gates.md`

## Purpose

This packet gives a human or later planner copy-ready language for choosing the
next `devframe-system` route. It does not select a route by itself.

The current safe default remains:

```text
HUMAN_REQUIRED: keep Phase 0.5 in contract-only planning mode.
```

## Current Evidence Sources

Use these artifacts when judging whether a physical bootstrap route can proceed:

1. `docs/agent-runtime/devframe-system-phase05-index.md` is the canonical
   navigation entrypoint.
2. `_reports/devframe-system-phase05-freshness-snapshot-a1/FRESHNESS_SNAPSHOT.md`
   is the latest recorded repository HEAD/count source.
3. `_reports/devframe-system-phase05-readiness-rollup-a1/READINESS_ROLLUP.md`
   is owner-action and prioritization context, not the latest source-status
   ledger.

## Decision Options

### Option 1: Continue Contract-Only Planning

Use this when no physical workspace should be created yet.

Copy-ready decision:

```text
I choose CONTINUE_CONTRACT_ONLY_PLANNING for devframe-system.
Do not create D:\devframe-system.
Do not add submodules.
Do not run dev-frame-opencode, devframe-control-plane, test-frame, or paper workflow.
Continue only with governance documents, draft contracts, and read-only inventory.
```

Allowed actions:

- Write governance documents inside `D:\agent-acceptance`.
- Update inactive registry and draft schemas.
- Capture read-only inventory reports.

Forbidden actions:

- Creating `D:\devframe-system`.
- Creating `.gitmodules`.
- Running `git submodule add`.
- Running external runtimes or tests.
- Cleaning, resetting, stashing, checking out, deleting, or staging external
  repository changes.

### Option 2: Route A Strict Clean-Baseline Bootstrap

Use this only after each source repository is clean or explicitly
owner-approved for the bootstrap scope.

Copy-ready decision:

```text
I choose ROUTE_A_STRICT_CLEAN_BASELINE for devframe-system.
Before creating D:\devframe-system, verify and record branch, HEAD, remote, and clean status for:
- D:\agent-acceptance
- D:\dev-frame-opencode
- D:\devframe-control-plane
- D:\test-frame
Do not run any external runtime during baseline capture.
If any source repository is dirty, stop and return HUMAN_REQUIRED.
```

Allowed actions after preflight passes:

- Create `D:\devframe-system` as a local-only superproject workspace.
- Create planning files that record source paths and pinned commits.
- Consider local submodule operations only after clean baselines are proven and
  separately approved.

Required evidence:

- `RepoBaselineRecord` for each source repository.
- Human approval record naming Route A.
- Confirmation that external runtimes were not executed during baseline capture.
- Confirmation that `test-frame` remains evidence-only, not GateResult authority.

Hard stop:

- If any source repository is dirty, Route A is blocked.

### Option 3: Route B Dirty-Aware Skeleton

Use this only if the human accepts that the workspace is not a trusted
submodule baseline.

Copy-ready decision:

```text
I choose ROUTE_B_DIRTY_AWARE_SKELETON for devframe-system.
You may create a local-only skeleton at D:\devframe-system, but you must not add submodules.
Record every source repository as dirty or untrusted until proven otherwise.
Do not run dev-frame-opencode, devframe-control-plane, test-frame, or paper workflow.
Do not clean, reset, stash, checkout, delete, or stage changes in external repositories.
Do not claim a trusted baseline or READY runtime status.
```

Allowed actions after explicit approval:

- Create a minimal local skeleton directory.
- Write planning-only baseline records inside the skeleton or
  `D:\agent-acceptance`, depending on the approved scope.
- Mark all source links as `HUMAN_REQUIRED` until clean baselines exist.

Forbidden actions:

- `git submodule add`.
- Runtime execution.
- External tests/builds/package installs.
- Cleanup/reset/stash/checkout/delete in source repositories.
- Trusted-baseline claims.
- GateResult claims from external frames.

Required evidence:

- Human approval record naming Route B.
- Dirty snapshot for all four source repositories.
- `SuperprojectLock` or successor record marking every dirty source as
  `HUMAN_REQUIRED`.
- Confirmation that no submodules exist.
- Confirmation that runtime execution still requires a separate
  `RuntimeExecutionRequest`.

## Frame Authority Reminder

| Frame | Role | Can produce GateResult? |
|---|---|---|
| `agent-acceptance` | governance source of truth | yes, for local governance only |
| `dev-frame-opencode` | execution runtime candidate | no |
| `devframe-control-plane` | control plane candidate | no |
| `test-frame` | controlled verification runtime candidate | no |
| `devframe-system` | future superproject control surface | no, until explicitly activated |

`test-frame` is not a plugin. It is a controlled verification runtime candidate.
Its outputs can be evidence only after a separate approved run.

## Default If No Option Is Selected

If the human has not copied one of the decision blocks above, the operative
state is:

```text
HUMAN_REQUIRED: no physical bootstrap, no runtime execution, no submodule add.
```

## Minimum Prompt For GPT-5.5 Pro

```text
You are reviewing the devframe-system Phase 0.5 route decision.
Read:
- docs/agent-runtime/devframe-system-activation-gates.md
- docs/agent-runtime/devframe-system-route-decision-packet.md
- docs/agent-runtime/devframe-system-phase05-index.md
- _reports/devframe-system-phase05-freshness-snapshot-a1/FRESHNESS_SNAPSHOT.md
- _reports/devframe-system-phase05-readiness-rollup-a1/READINESS_ROLLUP.md as owner-action context only

Do not create D:\devframe-system unless the human explicitly selected Route A or Route B.
Do not run external runtimes, tests, paper workflow, cleanup, reset, stash, checkout, or submodule commands.
Return one of:
- CONTINUE_CONTRACT_ONLY_PLANNING
- ROUTE_A_STRICT_CLEAN_BASELINE
- ROUTE_B_DIRTY_AWARE_SKELETON
- HUMAN_REQUIRED
Include the exact missing evidence before any physical bootstrap is allowed.
```
