# Devframe-System Phase 0.5 Index

Status: canonical navigation entrypoint
Current verdict: HUMAN_REQUIRED
Default action: continue contract-only planning

## Purpose

This index is the starting point for any future work on `devframe-system`.
It orders the Phase 0.5 governance artifacts and states what can and cannot be
done next.

## Current State

`D:\devframe-system` does not exist and must not be created unless the human
explicitly chooses Route A or Route B from the route decision packet.

The active default remains:

```text
HUMAN_REQUIRED: no physical bootstrap, no runtime execution, no submodule add.
```

## Reading Order

| Step | Artifact | Purpose | Current use |
|---:|---|---|---|
| 1 | `_reports/devframe-system-phase05-strict-gate-a1/PREFLIGHT_REPORT.md` | Establishes why physical bootstrap was blocked. | Strict gate preflight |
| 2 | `_reports/devframe-system-dirty-baseline-triage-a1/TRIAGE_REPORT.md` | Classifies dirty source repositories. | Dirty baseline context |
| 3 | `_reports/devframe-system-phase05-readiness-rollup-a1/READINESS_ROLLUP.md` | Summarizes current readiness and owner actions. | Current readiness snapshot |
| 4 | `_reports/devframe-system-contract-only-plan-a1/CONTRACT_ONLY_PLAN.md` | Defines contract-only planning boundary. | Safe planning mode |
| 5 | `schemas/draft/devframe-system-contracts.schema.draft.json` | Captures draft contract packet. | Inactive schema only |
| 6 | `docs/agent-runtime/devframe-system-activation-gates.md` | Defines Route A and Route B activation gates. | Gate reference |
| 7 | `docs/agent-runtime/devframe-system-route-decision-packet.md` | Provides copy-ready human decision blocks. | Human decision entrypoint |
| 8 | `docs/agent-runtime/devframe-system-route-b-noop-dry-run.md` | Rehearses Route B with zero side effects. | Route B no-op checklist |

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

- Create `D:\devframe-system`.
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

Requires explicit human route selection:

- Creating `D:\devframe-system`.
- Any Route A or Route B physical bootstrap step.
- Any external runtime execution.
- Any source repository cleanup or baseline mutation.

## Minimal Prompt For The Next Agent

```text
Start at docs/agent-runtime/devframe-system-phase05-index.md.
Current default is HUMAN_REQUIRED.
Do not create D:\devframe-system.
Do not run external runtimes, tests, paper workflow, cleanup, reset, stash, checkout, or submodule commands.
Use docs/agent-runtime/devframe-system-route-decision-packet.md if a human route decision is needed.
If no route is explicitly selected, continue contract-only planning only.
```
