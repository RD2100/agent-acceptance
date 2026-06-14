# Devframe-System Contract-Only Plan

Task ID: devframe-system-contract-only-plan-a1
Generated: 2026-06-14
Verdict: CONTRACT_ONLY_READY

## Summary

Physical `D:\devframe-system` bootstrap remains blocked, but contract-only
planning can proceed safely inside `D:\agent-acceptance`. This plan defines the
minimum future contracts needed before any superproject directory, submodule, or
runtime execution is created.

This is not an active runtime integration.

## Boundary Decision

The integration shape remains:

- Repositories stay physically separate.
- `devframe-system` is a future local-only superproject control surface.
- `agent-acceptance` remains the governance source of truth during Phase 0.5.
- `dev-frame-opencode`, `devframe-control-plane`, and `test-frame` are inactive
  candidates with no GateResult authority.
- `test-frame` is a controlled verification runtime candidate, not a plugin.

## Minimum Future Contract Set

These contracts are planning names, not active schemas yet.

| Contract | Purpose | Producer | Consumer | Activation status |
|---|---|---|---|---|
| `RepoBaselineRecord` | Captures repo path, HEAD, branch, dirty status, and portability status before submodule pinning | agent-acceptance or future devframe-system preflight | human reviewer, superproject lock step | draft planning only |
| `SuperprojectLock` | Captures local submodule paths, pinned commits, and local-only portability limits | future devframe-system bootstrap | human reviewer, control plane | draft planning only |
| `RuntimeExecutionRequest` | Explicitly asks to run opencode/control-plane/test-frame with command, cwd, timeout, and evidence destination | human or planner | runtime executor | human-gated only |
| `FrameActivationRecord` | Promotes an inactive frame to activating/active with source lock and boundary envelope references | human reviewer | agent runtime registry | future only |
| `VerificationRuntimeResult` | Records test-frame outputs as evidence, never as GateResult | test-frame candidate after approved run | agent-acceptance reviewer | future only |

## Data Flow Rules

Allowed now:

- Read-only repository inventory.
- Governance reports in `D:\agent-acceptance`.
- Contract-only planning.
- Inactive frame registry updates.

Forbidden now:

- Creating `D:\devframe-system`.
- Adding `.gitmodules`.
- Running `git submodule add`.
- Running `opencode`.
- Starting `devframe-control-plane`.
- Running `test-frame` builds/tests/runtime.
- Running paper workflow.
- Treating historical or candidate evidence as current GateResult.

## Activation Gates

Physical bootstrap can only be reconsidered when one of these paths is chosen:

Path A: strict clean baseline

- `agent-acceptance` clean or explicitly owner-scoped for superproject work.
- `dev-frame-opencode` clean and paper CLI changes reviewed or de-scoped.
- `devframe-control-plane` clean after artifact policy decision.
- `test-frame` clean after blackboard/config drift resolution.
- Human approves `D:\devframe-system` directory creation.

Path B: dirty-aware skeleton

- Human explicitly authorizes skeleton without submodules.
- Skeleton records all dirty baselines as HUMAN_REQUIRED.
- No submodule pinning occurs.
- No runtime execution occurs.

## Inactive Registry Update

`docs/agent-runtime/inactive-frame-registry.md` was updated to include:

- `dev-frame-opencode` as `execution_runtime_candidate`.
- `devframe-control-plane` as `control_plane_candidate`.
- `test-frame` as `controlled_verification_runtime_candidate`.
- `devframe-system` as `future_superproject_control`.

## Non-Actions

The following actions were not performed:

- No `D:\devframe-system` creation.
- No `.gitmodules` creation.
- No `git submodule add`.
- No external repository mutation.
- No external runtime, build, package install, or test.
- No cleanup, reset, stash, checkout, or unstage in external repositories.
- No paper workflow execution.

## Acceptance Gate Evaluation

| Gate | Result | Evidence |
|---|---|---|
| Runner start/edit-check | PASS | Runner start and edit-check passed for registry/report/evidence/current-task files. |
| Minimal contract set defined | PASS | See Minimum Future Contract Set. |
| Inactive registry updated | PASS | Four relevant frames are registered with inactive boundaries. |
| Physical bootstrap remains blocked | PASS | See Boundary Decision and Activation Gates. |
| No external mutation/runtime | PASS | Only local governance files in `D:\agent-acceptance` were edited. |
| Final checks | PASS | Targeted tests: 22 passed. Diff check: exit 0 with LF/CRLF warning only. Registry boundary search matched required inactive frames. `D:\devframe-system`: absent. |
