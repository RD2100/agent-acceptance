# Core Rules -- RD2100 Agent Runtime v2

> Domain: runtime core
> Phase 0-5: all P0/P1 rules active

---

## RULE core-001: No Destructive Git Without Approval

- **Priority**: P0 (Hard Stop)
- **Trigger**: Any git command that mutates history or discards work
- **Scope**: All phases
- **Rule**: Do not execute `git reset --hard`, `git clean -fd`, `git push --force`, `git checkout --`, `git stash drop`, `git branch -D` without explicit human approval.
- **Verification**: `git reflog` shows no unapproved destructive entries since session start.
- **Conflict Handling**: Even if a task plan says "reset to clean state", stop and ask.

---

## RULE core-002: No Secret Exposure

- **Priority**: P0 (Hard Stop)
- **Trigger**: Reading or writing any file
- **Scope**: All phases
- **Rule**: Do not read `.env`, `*.key`, `*.pem`, `*token*`, `*credential*`, SSH private keys, or any file that appears to contain secrets. Do not include secrets in output, logs, or reports.
- **Verification**: Grep output/logs for secret patterns (`BEGIN PRIVATE KEY`, `api_key=`, `token:`, `password=`).
- **Conflict Handling**: If a task requires reading a file that might contain secrets, stop and ask.

---

## RULE core-003: Phase Boundary Enforcement

- **Priority**: P0 (Hard Stop)
- **Trigger**: Any action
- **Scope**: Phase 0-5 bootstrap
- **Rule**: Do not perform actions forbidden in the current phase. See `docs/agent-runtime/tool-policy.md` for the active Phase 0-5 policy. Key prohibitions: no package install, no MCP config mutation, no hook registration, no external skill execution, no memory writes, no `bb_solidify_knowledge`.
- **Verification**: Cross-reference action list with Phase 0-5 forbidden list.
- **Conflict Handling**: If a batch plan requests a forbidden action, flag in ExecutionReport, do not execute.

---

## RULE core-004: Exit Code Contract

- **Priority**: P1 (Scope Control)
- **Trigger**: Any task completion
- **Scope**: All agent-acceptance runner tasks
- **Rule**: Exit 0 = PASS, Exit 1 = BLOCKED, Exit 2 = FAILED. Never report FAILED or BLOCKED as PASS ("no fake green").
- **Verification**: Exit code matches reported status.
- **Conflict Handling**: If a check fails but is a known flaky test, report as BLOCKED with known-issue reference, not PASS.

---

## RULE core-005: Dirty Baseline Protection

- **Priority**: P1 (Scope Control)
- **Trigger**: Any file modification
- **Scope**: Phase 0-5
- **Rule**: Do not modify existing dirty files (currently 13 modified + 6 untracked at baseline) unless explicitly approved in batch plan. New work must only touch approved scope.
- **Verification**: `git status --short` before and after each batch. Diff must only show approved changes.
- **Conflict Handling**: If a task accidentally touches a dirty baseline file, report immediately, do not continue.

---

## RULE core-006: Evidence Before Claim

- **Priority**: P2 (Evidence)
- **Trigger**: Making any claim about system state or task completion
- **Scope**: All phases
- **Rule**: Every claim must be backed by evidence. "X works" requires a test result, file listing, or command output. "Y exists" requires `test -f` or equivalent.
- **Verification**: Each claim in ExecutionReport has a corresponding evidence reference.
- **Conflict Handling**: If evidence cannot be collected (e.g., tool unavailable), note the limitation, downgrade claim confidence.
