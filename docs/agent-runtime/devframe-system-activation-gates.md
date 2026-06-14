# Devframe-System Activation Gates

Status: Phase 0.5 governance boundary
Owner system: agent-acceptance
Applies to: future local-only `D:\devframe-system`

## Purpose

This document defines the gates that must pass before any future
`devframe-system` bootstrap can move from contract-only planning to physical
workspace creation.

It does not activate a runtime. It does not register external frames as
GateResult authorities. It does not permit submodule creation.

## Current Verdict

Verdict: HUMAN_REQUIRED

Reason: the four source repositories are not clean enough to freeze as trusted
submodule baselines. A human must choose either strict clean-baseline bootstrap
or dirty-aware skeleton bootstrap.

## Source Frame Roles

| Frame | Current role | GateResult authority | Runtime status |
|---|---|---|---|
| `agent-acceptance` | governance source of truth | allowed for governance gates | active local governance only |
| `dev-frame-opencode` | execution runtime candidate | forbidden | inactive |
| `devframe-control-plane` | control plane candidate | forbidden | inactive |
| `test-frame` | controlled verification runtime candidate | forbidden | inactive |
| `devframe-system` | future superproject control surface | forbidden until separately approved | absent |

`test-frame` is not a plugin. It is a controlled verification runtime candidate.
Its future outputs may become evidence only; they must not directly produce
GateResult or final acceptance decisions.

## Route A: Strict Clean-Baseline Bootstrap

Strict bootstrap is allowed only when all conditions below are true:

1. `agent-acceptance` has an owner-approved clean or scoped baseline for this
   bootstrap.
2. `dev-frame-opencode` is clean, or every remaining dirty file has an
   owner-approved baseline record that explicitly blocks submodule pinning until
   resolved.
3. `devframe-control-plane` is clean, or its remaining files are classified by
   an owner-approved artifact policy.
4. `test-frame` is clean, including blackboard/config drift resolution.
5. A `RepoBaselineRecord` exists for each source repository.
6. A human explicitly approves creation of `D:\devframe-system`.
7. No external runtime is executed during the bootstrap commit itself.

Required evidence:

- Git branch, HEAD, remote, and dirty status for all four source repositories.
- Human approval record naming Route A.
- `SuperprojectLock` draft or successor record listing intended local paths and
  source commits.
- Post-action confirmation that `D:\devframe-system` exists only after approval.

## Route B: Dirty-Aware Skeleton

Dirty-aware skeleton is allowed only when a human explicitly accepts that the
workspace is not yet submodule-pinnable.

Route B may create only a local skeleton and planning records. It must not add
submodules, run external runtimes, clean source repositories, or claim a trusted
baseline.

Required evidence:

- Human approval record naming Route B.
- Dirty snapshot for each source repository.
- `SuperprojectLock` record with every source marked `HUMAN_REQUIRED`.
- Explicit statement that no submodule pins exist.
- Explicit statement that future runtime execution still requires a separate
  `RuntimeExecutionRequest`.

## Phase 0.5 Hard Stops

These actions remain forbidden unless a later human approval explicitly changes
the route:

- Creating `D:\devframe-system`.
- Creating or modifying `.gitmodules`.
- Running `git submodule add`.
- Running `opencode` or any `dev-frame-opencode` runtime command.
- Starting `devframe-control-plane`.
- Running `test-frame` builds, tests, or runtime commands.
- Running paper workflow commands.
- Cleaning, resetting, stashing, checking out, or deleting source-repository
  changes.
- Treating external-frame output as GateResult authority.

## Contract Mapping

| Contract | Used by Route A | Used by Route B | Notes |
|---|---:|---:|---|
| `RepoBaselineRecord` | yes | yes | Captures source branch, HEAD, dirty status, and runtime authorization status. |
| `SuperprojectLock` | yes | yes | Route A may pin clean commits; Route B must mark sources `HUMAN_REQUIRED`. |
| `RuntimeExecutionRequest` | later only | later only | Separate human gate before any external runtime command. |
| `FrameActivationRecord` | later only | later only | Required before inactive frames become active participants. |
| `VerificationRuntimeResult` | later only | later only | Evidence from `test-frame`; not GateResult. |

## Minimum Next Decision

The next human decision must choose one of:

1. Continue owner cleanup until Route A is possible.
2. Authorize Route B dirty-aware skeleton without submodules.
3. Keep Phase 0.5 in contract-only planning mode.

Until one is selected, the correct system state is `HUMAN_REQUIRED`.
