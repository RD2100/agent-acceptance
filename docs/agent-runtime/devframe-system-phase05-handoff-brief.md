# Devframe-System Phase 0.5 Handoff Brief

Status: compact handoff
Canonical index: `docs/agent-runtime/devframe-system-phase05-index.md`
Current default: `HUMAN_REQUIRED`

## One-Minute State

`D:\devframe-system` now exists as a manually created local directory. It is
still only a future superproject control surface: it is not activated, not a
trusted baseline, and not proof that the four source repositories have been
merged.

Current safe mode is contract-only planning inside `D:\agent-acceptance`.

Do not mutate `D:\devframe-system` into a physical bootstrap unless a human
explicitly selects Route A or Route B from
`docs/agent-runtime/devframe-system-route-decision-packet.md`.

## Current Route Status

| Route | Status | Next requirement |
|---|---|---|
| `CONTINUE_CONTRACT_ONLY_PLANNING` | allowed | Keep work inside governance docs/reports. |
| `ROUTE_A_STRICT_CLEAN_BASELINE` | blocked | Prove clean baselines and get explicit human Route A approval. |
| `ROUTE_B_DIRTY_AWARE_SKELETON` | blocked | Get explicit human Route B approval. |
| `HUMAN_REQUIRED` | current default | Ask for a route decision if physical bootstrap is needed. |

## Must Read First

1. `docs/agent-runtime/devframe-system-phase05-index.md`
2. `docs/agent-runtime/devframe-system-route-decision-packet.md`
3. `docs/agent-runtime/devframe-system-route-decision-worksheet.md`
4. `docs/agent-runtime/devframe-system-route-approval-record-template.md`
5. `docs/agent-runtime/devframe-system-route-a-clean-baseline-checklist.md`
6. `docs/agent-runtime/devframe-system-route-b-noop-dry-run.md`

## Hard Stops

Do not perform any of these actions unless a later explicit human route decision
authorizes them:

- Treat the existing `D:\devframe-system` directory as an activated
  superproject, trusted baseline, or completed merge.
- Mutate `D:\devframe-system` into a physical bootstrap.
- Create or modify `.gitmodules`.
- Run `git submodule add`.
- Run external runtime commands.
- Run external tests, builds, or package installs.
- Run paper workflow commands.
- Clean, reset, stash, checkout, delete, stage, or commit changes in external
  repositories.
- Claim trusted baselines from dirty repositories.
- Treat external-frame output as GateResult authority.

## Frame Roles

| Frame | Role | GateResult authority |
|---|---|---|
| `agent-acceptance` | governance source of truth | local governance only |
| `dev-frame-opencode` | execution runtime candidate | no |
| `devframe-control-plane` | control plane candidate | no |
| `test-frame` | controlled verification runtime candidate | no |
| `devframe-system` | future superproject control surface | no, until activated |

`test-frame` is not a plugin. It is a controlled verification runtime candidate.
Its output can become evidence only after a separately approved run.

## Copy-Ready Prompt For GPT-5.5 Pro

```text
You are continuing devframe-system Phase 0.5 governance.

Start at:
- docs/agent-runtime/devframe-system-phase05-index.md
- docs/agent-runtime/devframe-system-route-decision-packet.md
- docs/agent-runtime/devframe-system-route-decision-worksheet.md
- docs/agent-runtime/devframe-system-route-approval-record-template.md
- docs/agent-runtime/devframe-system-route-a-clean-baseline-checklist.md
- docs/agent-runtime/devframe-system-route-b-noop-dry-run.md

Current default is HUMAN_REQUIRED.

Do not treat the existing D:\devframe-system directory as a completed merge or trusted baseline.
Do not create or modify .gitmodules.
Do not run git submodule add.
Do not run dev-frame-opencode, devframe-control-plane, test-frame, paper workflow, builds, tests, package installs, cleanup, reset, stash, checkout, delete, stage, or commit commands in external repositories.
Do not claim trusted baselines from dirty repositories.
Do not treat test-frame as a plugin or GateResult authority.

If no explicit human route decision is present, continue contract-only planning only.

Return:
1. Which route is currently valid.
2. Which evidence is missing before physical bootstrap.
3. The safest next no-op governance step.
4. Whether the human needs to choose a formal route block before any physical bootstrap.
5. Whether a filled approval record is present, and if so where.
```

## Recommended Next No-Op Step

The read-only freshness snapshot has been captured at:

`_reports/devframe-system-phase05-freshness-snapshot-a1/FRESHNESS_SNAPSHOT.md`

The Route A/B checklist source-maintenance record is:

`_reports/devframe-system-phase05-route-checklist-source-refresh-a1/ROUTE_CHECKLIST_SOURCE_REFRESH.md`

It confirms the no-op Route A and Route B checklists now point to the freshness
snapshot as the current repository-fact source.

The current gap tracker is:

`_reports/devframe-system-current-gap-tracker-a1/CURRENT_GAP_TRACKER.md`

It records the newer fact that `D:\devframe-system` exists while the operative
verdict remains `HUMAN_REQUIRED`.

The latest gap-status overlay is:

`_reports/devframe-system-gap-tracker-refresh-a1/CURRENT_GAP_REFRESH.md`

It records that the local registry/router stress-test blocker from the current
gap tracker has been resolved by commit `78689129`; targeted local governance
and router checks returned `50 passed`. This does not authorize Route A, Route
B, external runtime execution, submodules, or a completed-merge claim.

`devframe-control-plane` has reached clean baseline candidate status, but
`devframe-system` physical merge remains blocked until all source repos are
clean or a dirty-aware route is explicitly approved.

The latest Route A no-op preflight dashboard is:

`_reports/devframe-system-route-a-preflight-a1/MERGE_DASHBOARD.md`

It is generated by:

`scripts/devframe_system_route_a_preflight.py`

Current result: `HUMAN_REQUIRED`. `devframe-control-plane` is ready as a clean
baseline candidate; `agent-acceptance`, `dev-frame-opencode`, and `test-frame`
still have dirty state, and the existing empty `D:\devframe-system` directory
does not authorize physical bootstrap.

The one-page human route worksheet is:

`docs/agent-runtime/devframe-system-route-decision-worksheet.md`

Use it before asking the human to choose a formal route block from the route
decision packet.

The approval record template is:

`docs/agent-runtime/devframe-system-route-approval-record-template.md`

Use it only to record an explicit human route approval. A blank or partial copy
does not authorize any action.

Its inactive draft schema is:

`schemas/draft/devframe-system-contracts.schema.draft.json#/$defs/HumanRouteApprovalRecord`

The schema is for structural review and future validation planning only; it is
not an active runtime or gate validator.

If no route is selected, the next safe action is to continue contract-only
planning or ask the human to choose one of the route decision blocks. Repeat the
freshness snapshot only if there is reason to believe one of the four source
repository states changed.

Current physical-bootstrap verdict remains `HUMAN_REQUIRED`.
