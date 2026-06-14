# Devframe-System Phase 0.5 Index

Status: canonical navigation entrypoint
Current verdict: HUMAN_REQUIRED
Default action: continue contract-only planning

## Purpose

This index is the starting point for any future work on `devframe-system`.
It orders the Phase 0.5 governance artifacts and states what can and cannot be
done next.

## Current State

`D:\devframe-system` now exists as a manually created local directory, but it is
not an activated superproject, not a trusted baseline, and not proof that the
four source repositories have been merged. No submodule, runtime, or baseline
claim may rely on it until Route A or Route B is explicitly selected and
verified.

The active default remains:

```text
HUMAN_REQUIRED: no physical bootstrap, no runtime execution, no submodule add.
```

## Reading Order

| Step | Artifact | Purpose | Current use |
|---:|---|---|---|
| 1 | `_reports/devframe-system-phase05-strict-gate-a1/PREFLIGHT_REPORT.md` | Establishes why physical bootstrap was blocked. | Strict gate preflight |
| 2 | `_reports/devframe-system-dirty-baseline-triage-a1/TRIAGE_REPORT.md` | Classifies dirty source repositories. | Dirty baseline context |
| 3 | `_reports/devframe-system-phase05-readiness-rollup-a1/READINESS_ROLLUP.md` | Summarizes readiness and owner actions from an earlier snapshot. | Owner-action rollup; use the freshness snapshot for current repository facts |
| 4 | `_reports/devframe-system-contract-only-plan-a1/CONTRACT_ONLY_PLAN.md` | Defines contract-only planning boundary. | Safe planning mode |
| 5 | `schemas/draft/devframe-system-contracts.schema.draft.json` | Captures draft contract packet, including inactive `HumanRouteApprovalRecord` structure. | Inactive schema only |
| 6 | `docs/agent-runtime/devframe-system-activation-gates.md` | Defines Route A and Route B activation gates. | Gate reference |
| 7 | `docs/agent-runtime/devframe-system-route-decision-packet.md` | Provides copy-ready human decision blocks. | Human decision entrypoint |
| 8 | `docs/agent-runtime/devframe-system-route-decision-worksheet.md` | Compresses route choice, missing evidence, and forbidden actions into a one-page human decision worksheet. | Human decision worksheet |
| 9 | `docs/agent-runtime/devframe-system-route-approval-record-template.md` | Defines the copy-ready human approval record fields required before Route A or Route B can proceed. | Approval evidence template |
| 10 | `docs/agent-runtime/devframe-system-route-a-clean-baseline-checklist.md` | Rehearses Route A clean-baseline checks with zero side effects. | Route A no-op checklist |
| 11 | `docs/agent-runtime/devframe-system-route-b-noop-dry-run.md` | Rehearses Route B with zero side effects. | Route B no-op checklist |
| 12 | `docs/agent-runtime/devframe-system-phase05-handoff-brief.md` | Gives GPT-5.5 Pro or a future agent a compact safe handoff. | Handoff brief |
| 13 | `_reports/devframe-system-phase05-freshness-snapshot-a1/FRESHNESS_SNAPSHOT.md` | Captures the latest read-only four-repository state. | Current freshness snapshot |
| 14 | `_reports/devframe-system-phase05-route-checklist-source-refresh-a1/ROUTE_CHECKLIST_SOURCE_REFRESH.md` | Records that Route A/B checklists now point to the freshness snapshot as the current repository-fact source. | Checklist source-maintenance evidence |
| 15 | `_reports/devframe-system-current-gap-tracker-a1/CURRENT_GAP_TRACKER.md` | Records the current gap list after `D:\devframe-system` was manually created while source repositories remain dirty. | Current gap tracker |
| 16 | `_reports/devframe-system-gap-tracker-refresh-a1/CURRENT_GAP_REFRESH.md` | Records that the local router stress blocker from the previous gap tracker has been resolved while Route A/B remain blocked. | Latest gap-status overlay |
| 17 | `_reports/devframe-system-route-a-preflight-a1/MERGE_DASHBOARD.md` | Records the current Route A no-op preflight result from the read-only validator. | Latest merge dashboard |

## Route Summary

| Route | Meaning | Current status |
|---|---|---|
| `CONTINUE_CONTRACT_ONLY_PLANNING` | Keep work inside `D:\agent-acceptance` governance docs and reports. | allowed |
| `ROUTE_A_STRICT_CLEAN_BASELINE` | Create physical superproject only after clean source baselines are proven. | blocked until clean baselines |
| `ROUTE_B_DIRTY_AWARE_SKELETON` | Create a local skeleton without submodules while marking sources untrusted. | blocked until explicit human approval |
| `HUMAN_REQUIRED` | No route selected or required evidence missing. | current default |

## Frame Roles

| Frame | Role | Can produce GateResult? |
|---|---|---|
| `agent-acceptance` | governance source of truth | yes, for local governance only |
| `dev-frame-opencode` | execution runtime candidate | no |
| `devframe-control-plane` | control plane candidate | no |
| `test-frame` | controlled verification runtime candidate | no |
| `devframe-system` | future superproject control surface | no, until explicitly activated |

`test-frame` is not a plugin. It is a controlled verification runtime candidate.
Its output can become evidence only after a separately approved run.

## Always Forbidden In Phase 0.5

Unless a later explicit human decision changes the route, do not:

- Treat the existing `D:\devframe-system` directory as an activated
  superproject, trusted baseline, or completed merge.
- Mutate `D:\devframe-system` into a physical bootstrap without explicit Route A
  or Route B approval.
- Create or modify `.gitmodules`.
- Run `git submodule add`.
- Run external runtime commands.
- Run external tests, builds, or package installs.
- Run paper workflow commands.
- Clean, reset, stash, checkout, delete, stage, or commit changes in external
  repositories.
- Claim trusted baselines from dirty repositories.
- Treat external-frame output as GateResult authority.

## Next Allowed Work

Allowed without new human route selection:

- More contract-only governance documentation inside `D:\agent-acceptance`.
- Read-only inventory snapshots.
- Owner-action reports that classify existing dirty state without modifying it.
- Navigation, checklist, and review improvements.
- Refreshing this index or the handoff brief when a completed governance
  artifact changes the current reading order.

Requires explicit human route selection:

- Creating `D:\devframe-system`.
- Any Route A or Route B physical bootstrap step.
- Any external runtime execution.
- Any source repository cleanup or baseline mutation.

## Latest Snapshot

The latest recorded read-only repository freshness snapshot is:

`_reports/devframe-system-phase05-freshness-snapshot-a1/FRESHNESS_SNAPSHOT.md`

It preserves the operative verdict as `HUMAN_REQUIRED` because all four source
repositories remain dirty. It was captured before the manually created
`D:\devframe-system` directory existed, so use the current gap tracker for the
latest directory-existence fact.

For current repository HEAD/count facts, prefer this freshness snapshot over
older readiness or owner-action reports. Older reports remain useful for
history, prioritization, and owner-action context.

The latest checklist source-maintenance artifact is:

`_reports/devframe-system-phase05-route-checklist-source-refresh-a1/ROUTE_CHECKLIST_SOURCE_REFRESH.md`

It does not select Route A or Route B. It only records that the Route A and
Route B no-op checklists now point future operators to the freshness snapshot
for repository facts.

The latest current-gap artifact is:

`_reports/devframe-system-current-gap-tracker-a1/CURRENT_GAP_TRACKER.md`

It records that `D:\devframe-system` exists, but the correct verdict remains
`HUMAN_REQUIRED` until source repositories are clean or a dirty-aware Route B
approval is recorded.

The latest gap-status overlay is:

`_reports/devframe-system-gap-tracker-refresh-a1/CURRENT_GAP_REFRESH.md`

It records that the local router stress blocker in the earlier current-gap
artifact was resolved by commit `78689129`, with targeted local tests returning
`50 passed`. This does not change the physical-bootstrap verdict: Route A and
Route B remain blocked for the reasons listed above.

`devframe-control-plane` has reached clean baseline candidate status, but
`devframe-system` physical merge remains blocked until all source repos are
clean or a dirty-aware route is explicitly approved.

The latest Route A no-op preflight dashboard is:

`_reports/devframe-system-route-a-preflight-a1/MERGE_DASHBOARD.md`

It is produced by the read-only validator:

`scripts/devframe_system_route_a_preflight.py`

The current validator result is `HUMAN_REQUIRED`: `devframe-control-plane` is
ready as a clean baseline candidate, while `agent-acceptance`,
`dev-frame-opencode`, and `test-frame` still have dirty state and the existing
empty `D:\devframe-system` target directory still requires route approval.

## Minimal Prompt For The Next Agent

```text
Start at docs/agent-runtime/devframe-system-phase05-index.md.
Current default is HUMAN_REQUIRED.
Do not treat the existing D:\devframe-system directory as a completed merge or trusted baseline.
Do not run external runtimes, tests, paper workflow, cleanup, reset, stash, checkout, or submodule commands.
Use docs/agent-runtime/devframe-system-route-decision-packet.md if a human route decision is needed.
Use docs/agent-runtime/devframe-system-route-decision-worksheet.md to compare the valid choices before asking for the formal decision block.
Use docs/agent-runtime/devframe-system-route-approval-record-template.md to record any explicit human route approval.
If no route is explicitly selected, continue contract-only planning only.
```
