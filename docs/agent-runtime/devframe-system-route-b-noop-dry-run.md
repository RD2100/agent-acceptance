# Devframe-System Route B No-Op Dry-Run Checklist

Status: no-op checklist only
Related decision packet: `docs/agent-runtime/devframe-system-route-decision-packet.md`
Route: `ROUTE_B_DIRTY_AWARE_SKELETON`

## Purpose

This checklist describes how to rehearse Route B without side effects. It does
not authorize Route B execution and must not be treated as human approval.

Correct default verdict:

```text
HUMAN_REQUIRED: Route B is not active until the human explicitly chooses it.
```

## Zero-Side-Effect Rule

During this dry-run, the operator may read files and produce governance
reports. The operator must not change any source repository, create the
superproject directory, add submodules, or run external runtimes.

## Preflight Inputs

Required before even a no-op dry-run can be marked complete:

1. Human decision packet exists.
2. Activation gates document exists.
3. Draft contracts packet exists.
4. Latest freshness snapshot exists for current repository facts.
5. The operator confirms this is a no-op rehearsal, not Route B activation.
6. The operator confirms paper workflow remains paused.

Latest recorded source-status artifact:

`_reports/devframe-system-phase05-freshness-snapshot-a1/FRESHNESS_SNAPSHOT.md`

Older readiness and owner-action reports remain useful context, but they should
not be treated as the newest HEAD/count ledger.

## Explicitly Forbidden In No-Op Dry-Run

- `New-Item D:\devframe-system` or equivalent directory creation.
- `.gitmodules` creation or modification.
- `git submodule add`.
- `opencode run` or any `dev-frame-opencode` runtime command.
- Starting `devframe-control-plane`.
- Running `test-frame` builds, tests, or runtime commands.
- Running paper workflow commands.
- Cleaning, resetting, stashing, checking out, deleting, staging, or committing
  changes in `D:\dev-frame-opencode`, `D:\devframe-control-plane`, or
  `D:\test-frame`.
- Claiming a trusted baseline.
- Claiming `READY` runtime status.
- Treating `test-frame` output as GateResult authority.

## Dry-Run Steps

These are documentation and read-only planning steps. They do not create
`D:\devframe-system`.

1. Confirm current decision state:

   ```text
   HUMAN_REQUIRED unless the human copied the Route B decision block.
   ```

2. Confirm expected skeleton boundary:

   ```text
   local-only skeleton path: D:\devframe-system
   submodules: forbidden
   runtime execution: forbidden
   external repo mutation: forbidden
   source link status: HUMAN_REQUIRED
   ```

3. Prepare the future evidence names only:

   ```text
   RepoBaselineRecord: one per source repository
   SuperprojectLock: all dirty sources marked HUMAN_REQUIRED
   RuntimeExecutionRequest: absent
   FrameActivationRecord: absent
   VerificationRuntimeResult: absent
   ```

4. Confirm `test-frame` authority:

   ```text
   test-frame is a controlled verification runtime candidate.
   It is not a plugin.
   It cannot produce GateResult.
   ```

5. Produce a no-op report inside `D:\agent-acceptance` only.

## Pass Conditions

The dry-run can be marked `NOOP_DRY_RUN_READY` only if all statements are true:

- No `D:\devframe-system` directory exists after the dry-run.
- No `.gitmodules` file was created or modified.
- No submodule command was run.
- No external runtime/test/build/package-install command was run.
- No source repository was mutated.
- No trusted-baseline or runtime `READY` claim was made.
- `test-frame` is still documented as evidence-only and not GateResult
  authority.

## Fail Conditions

The dry-run must be marked `FAILED` or `HUMAN_REQUIRED` if any statement is true:

- `D:\devframe-system` exists because of this task.
- A submodule or `.gitmodules` action occurred.
- Any external runtime/test/build command ran.
- Any external source repository was cleaned, reset, stashed, checked out,
  deleted, staged, or committed.
- A report claims Route B is active without the human decision block.
- A report claims a trusted baseline from dirty repositories.

## Evidence Required For A Real Route B Later

A later real Route B task must create or reference:

- The exact human Route B approval text.
- The latest freshness snapshot, or a newer dirty snapshot for all four source
  repositories.
- A `SuperprojectLock` or successor record marking every dirty source
  `HUMAN_REQUIRED`.
- Confirmation that no submodules exist.
- Confirmation that runtime execution still requires a separate
  `RuntimeExecutionRequest`.
- Confirmation that paper workflow remains paused unless separately authorized.

## Abort Rule

If any planned action would write outside `D:\agent-acceptance` before explicit
Route B approval, abort and return:

```text
HUMAN_REQUIRED: proposed action is not no-op.
```
