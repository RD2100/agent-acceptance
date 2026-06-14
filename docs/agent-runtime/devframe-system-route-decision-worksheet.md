# Devframe-System Route Decision Worksheet

Status: human decision worksheet
Default verdict: HUMAN_REQUIRED
Canonical packet: `docs/agent-runtime/devframe-system-route-decision-packet.md`

## Purpose

Use this one-page worksheet immediately before asking a human or GPT-5.5 Pro to
choose the next `devframe-system` route. It summarizes what each route means,
what evidence is missing, and what actions remain forbidden.

This worksheet does not select a route by itself.

## Current Inputs

| Input | Artifact | Use |
|---|---|---|
| Canonical navigation | `docs/agent-runtime/devframe-system-phase05-index.md` | Start here for current Phase 0.5 ordering. |
| Copy-ready route blocks | `docs/agent-runtime/devframe-system-route-decision-packet.md` | Use for formal human route selection. |
| Latest recorded source status | `_reports/devframe-system-phase05-freshness-snapshot-a1/FRESHNESS_SNAPSHOT.md` | Latest recorded four-repository dirty snapshot. |
| Route A/B checklist source record | `_reports/devframe-system-phase05-route-checklist-source-refresh-a1/ROUTE_CHECKLIST_SOURCE_REFRESH.md` | Confirms checklists use the freshness snapshot as repository-fact source. |

Important: the freshness snapshot is the latest recorded source-status artifact,
not a live proof that the source repositories are clean now.

## Route Choice Matrix

| Choice | Can choose now? | Missing evidence or approval | Next allowed action after choice | Hard stop |
|---|---|---|---|---|
| `CONTINUE_CONTRACT_ONLY_PLANNING` | Yes | None | Keep work inside `D:\agent-acceptance` governance docs, draft contracts, reports, and read-only inventory. | Do not create `D:\devframe-system`. |
| `ROUTE_A_STRICT_CLEAN_BASELINE` | No | Clean baseline proof for all four source repositories plus explicit Route A approval. | After proof and approval, capture baseline records before any physical bootstrap. | If any source repo is dirty, return `HUMAN_REQUIRED`. |
| `ROUTE_B_DIRTY_AWARE_SKELETON` | No | Explicit human Route B approval accepting untrusted dirty sources. | After approval, create only the approved local skeleton scope and mark sources untrusted. | No submodule add, no trusted-baseline claim, no runtime execution. |
| `HUMAN_REQUIRED` | Current default | A route selection or missing evidence. | Ask for a route decision or continue contract-only planning. | Do not infer approval from discussion. |

## Source Frames

| Frame | Role | Current authority |
|---|---|---|
| `agent-acceptance` | Governance source of truth | Local governance only |
| `dev-frame-opencode` | Execution runtime candidate | No GateResult authority |
| `devframe-control-plane` | Control plane candidate | No GateResult authority |
| `test-frame` | Controlled verification runtime candidate | No GateResult authority |
| `devframe-system` | Future superproject control surface | No authority until activated |

`test-frame` is not a plugin. It is a controlled verification runtime
candidate. Its output can become evidence only after a separately approved run.

## Copy-Ready Human Question

```text
Please choose one devframe-system Phase 0.5 route:

1. CONTINUE_CONTRACT_ONLY_PLANNING
2. ROUTE_A_STRICT_CLEAN_BASELINE
3. ROUTE_B_DIRTY_AWARE_SKELETON

Current default remains HUMAN_REQUIRED.

If you choose Route A, you authorize only clean-baseline verification first.
If any source repo is dirty, stop and return HUMAN_REQUIRED.

If you choose Route B, you authorize only a dirty-aware local skeleton without
submodules and without runtime execution. All dirty sources remain untrusted.

No route choice authorizes external runtime execution, external tests, paper
workflow, cleanup, reset, stash, checkout, delete, or source-repo mutation.
```

## Decision Recording Requirement

Any future route selection must produce a human approval record that includes:

- exact route name;
- allowed file-system scope;
- whether `D:\devframe-system` creation is authorized;
- whether submodules remain forbidden;
- confirmation that runtime execution remains separately gated;
- confirmation that `test-frame` remains evidence-only until separately
  approved.
