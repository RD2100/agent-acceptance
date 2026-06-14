# Devframe-System Route A Clean-Baseline Checklist

Status: no-op checklist only
Related decision packet: `docs/agent-runtime/devframe-system-route-decision-packet.md`
Route: `ROUTE_A_STRICT_CLEAN_BASELINE`

## Purpose

This checklist describes how to rehearse Route A baseline verification without
side effects. It does not authorize Route A execution and must not be treated as
human approval to create `D:\devframe-system`.

Correct default verdict:

```text
HUMAN_REQUIRED: Route A is not active until clean baselines are proven and the human explicitly chooses it.
```

## Zero-Side-Effect Rule

During this checklist, the operator may collect read-only status facts and write
governance reports in `D:\agent-acceptance`. The operator must not clean,
reset, stash, checkout, delete, stage, commit, or otherwise modify any source
repository.

## Baseline Inputs

Route A requires read-only baseline facts for all four source repositories:

| Repository | Required facts | Clean required? |
|---|---|---|
| `D:\agent-acceptance` | path, branch, HEAD, remote, dirty status | yes or owner-scoped exception |
| `D:\dev-frame-opencode` | path, branch, HEAD, remote, dirty status | yes |
| `D:\devframe-control-plane` | path, branch, HEAD, remote, dirty status | yes or owner-approved artifact policy |
| `D:\test-frame` | path, branch, HEAD, remote, dirty status | yes |

## Read-Only Commands Allowed Later

These commands are examples for a later authorized inventory task. They are
read-only and must be run from each target repository when allowed:

```powershell
git branch --show-current
git rev-parse HEAD
git remote -v
git status --short
```

Do not run tests, builds, package managers, runtime commands, cleanup commands,
or submodule commands during baseline capture.

## Clean-State Decision

Route A can proceed only if every source is clean or has a specifically
documented owner-approved exception accepted by the human.

Decision rules:

- If all repositories are clean and human Route A approval exists, status can
  move to `ROUTE_A_PREFLIGHT_READY`.
- If any repository is dirty without an approved exception, status remains
  `HUMAN_REQUIRED`.
- If any read-only inventory cannot be collected, status remains
  `HUMAN_REQUIRED`.
- If any command would mutate a source repository, abort.

## Explicitly Forbidden In This Checklist

- Creating `D:\devframe-system`.
- Creating or modifying `.gitmodules`.
- Running `git submodule add`.
- Running external runtime commands.
- Running external tests, builds, or package installs.
- Running paper workflow commands.
- Cleaning, resetting, stashing, checking out, deleting, staging, or committing
  changes in any source repository.
- Claiming a trusted baseline from a dirty repository.
- Treating `test-frame` output as GateResult authority.

## Pass Conditions

The checklist can be marked `ROUTE_A_CHECKLIST_READY` only if all statements are
true:

- The checklist itself did not create `D:\devframe-system`.
- The checklist did not execute external commands.
- The checklist did not mutate external repositories.
- It names the four required source repositories.
- It states dirty repositories keep Route A at `HUMAN_REQUIRED`.
- It preserves `test-frame` as evidence-only and not GateResult authority.

## Fail Conditions

The checklist must be marked `FAILED` or `HUMAN_REQUIRED` if any statement is
true:

- A report claims Route A is active without human approval.
- A dirty source repository is accepted as a trusted baseline without explicit
  owner-approved exception.
- A submodule or `.gitmodules` action occurred.
- A runtime/test/build/package-install command ran.
- A source repository was cleaned, reset, stashed, checked out, deleted, staged,
  or committed.

## Evidence Required For A Real Route A Later

A later real Route A task must create or reference:

- The exact human Route A approval text.
- A `RepoBaselineRecord` for each source repository.
- Clean status evidence or owner-approved scoped exception for each source.
- A `SuperprojectLock` or successor record with intended local paths and
  source commits.
- Confirmation that no external runtime was executed during baseline capture.
- Confirmation that `test-frame` remains evidence-only, not GateResult
  authority.

## Abort Rule

If any planned action would mutate a source repository or create
`D:\devframe-system` before explicit Route A approval, abort and return:

```text
HUMAN_REQUIRED: proposed action is not a clean-baseline no-op.
```
