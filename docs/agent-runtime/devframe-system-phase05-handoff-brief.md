# Devframe-System Phase 0.5 Handoff Brief

Status: compact handoff
Canonical index: `docs/agent-runtime/devframe-system-phase05-index.md`
Current default: `HUMAN_REQUIRED`

## One-Minute State

`devframe-system` is still a future local-only superproject control surface.
It has not been physically created.

Current safe mode is contract-only planning inside `D:\agent-acceptance`.

Do not create `D:\devframe-system` unless a human explicitly selects Route A or
Route B from `docs/agent-runtime/devframe-system-route-decision-packet.md`.

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
3. `docs/agent-runtime/devframe-system-route-a-clean-baseline-checklist.md`
4. `docs/agent-runtime/devframe-system-route-b-noop-dry-run.md`

## Hard Stops

Do not perform any of these actions unless a later explicit human route decision
authorizes them:

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
- docs/agent-runtime/devframe-system-route-a-clean-baseline-checklist.md
- docs/agent-runtime/devframe-system-route-b-noop-dry-run.md

Current default is HUMAN_REQUIRED.

Do not create D:\devframe-system.
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
```

## Recommended Next No-Op Step

If no route is selected, the next safe action is a read-only freshness snapshot
of the four source repository states, recorded inside `D:\agent-acceptance`
only. It must not clean or mutate those repositories.
