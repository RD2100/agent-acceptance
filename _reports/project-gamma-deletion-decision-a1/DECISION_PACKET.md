# Project-Gamma Deletion Decision Packet A1

Date: 2026-06-14
Created at: 2026-06-14T15:15:05.1827255+08:00
Task: project-gamma-deletion-decision-a1
Verdict: HUMAN_REQUIRED

## Decision Record Draft

```yaml
decision_record:
  id: DECISION-20260614-PROJECT-GAMMA-DELETION-A1
  timestamp: "2026-06-14T15:15:05.1827255+08:00"
  trigger: "Large tracked baseline deletion / protected governance content mutation"
  decision_required: "Decide whether the current _projects/project-gamma deletion set should be restored, accepted through a dedicated review task, or deferred."
  context: >
    The current agent-acceptance worktree contains 188 tracked deletions under
    _projects/project-gamma, totaling 14301 deleted lines. Deleted files include
    AGENTS.md, docs/agent-runtime governance documents, rules, schemas, and
    runtime-bootstrap templates. These deletions are not covered by the current
    task and must not be broad-staged.
  affected_files:
    - path: "_projects/project-gamma/**"
      reason: "188 tracked deletions, including governance docs, rules, schemas, and templates."
  options:
    - label: "Restore deletion set"
      description: "Run a dedicated scoped restore task for _projects/project-gamma only, returning the tracked files to the committed baseline."
      risk: "low"
      impact: "Removes the immediate deletion risk from the worktree. Any intentional cleanup would need a new planned task later."
    - label: "Accept through dedicated deletion review"
      description: "Create a separate deletion-review TaskSpec that inventories the 188 files, explains why each deletion is intended, runs relevant validation, and commits only after review."
      risk: "high"
      impact: "May remove a large project fixture/baseline from agent-acceptance, but only with explicit evidence and review."
    - label: "Defer"
      description: "Leave the deletion set unstaged while other higher-priority work continues."
      risk: "medium"
      impact: "Avoids unauthorized mutation, but the dirty worktree remains noisy and broad staging remains dangerous."
  agent_recommendation: >
    Restore deletion set unless the owner can identify a concrete reason to
    remove project-gamma now. The deletion set is large, governance-heavy, and
    currently lacks evidence of intentional cleanup.
  human_decision: "PENDING_HUMAN_RESPONSE"
  authorization: "PENDING_HUMAN_RESPONSE"
  committed_with: "PENDING_FUTURE_AUTHORIZED_COMMIT"
```

## Current Deletion Evidence

`git status --short -- _projects/project-gamma`:

- 188 entries
- all observed entries are tracked deletions

`git diff --stat -- _projects/project-gamma`:

- 188 files changed
- 14301 deletions

Sample deleted paths:

- `_projects/project-gamma/.agent/CONVERSATION_BINDING.json`
- `_projects/project-gamma/AGENTS.md`
- `_projects/project-gamma/docs/agent-runtime/capability-inventory.md`
- `_projects/project-gamma/docs/agent-runtime/integration-contracts.md`
- `_projects/project-gamma/docs/agent-runtime/runtime-invariants.md`
- `_projects/project-gamma/docs/agent-runtime/sub-agent-dispatch-protocol.md`
- `_projects/project-gamma/rules/core.md`
- `_projects/project-gamma/schemas/agent-runtime/task-spec.schema.json`
- `_projects/project-gamma/templates/runtime-bootstrap/bootstrap.ps1`

## Authority Boundary

This packet does not authorize deletion, restoration, or staging. It only
records that the current deletion set needs a human decision.

Accepting the deletion would mutate a large tracked baseline. Restoring it would
also mutate the current worktree. Either route needs an explicit scoped task and
approval.

## Explicit Non-Actions

- `_projects/project-gamma` deletions are not staged by this task.
- `.agent/PROJECT_REGISTRY.json` is not staged by this task.
- No cleanup, reset, stash, checkout, restore, delete, or broad staging is performed.
- No external repository runtime or test is executed.
- No paper workflow is executed.

## Copy-Ready Human Decision Blocks

Restore:

```text
I approve DECISION-20260614-PROJECT-GAMMA-DELETION-A1 Option: Restore deletion set. Prepare and execute a scoped restore task for _projects/project-gamma only. Do not touch other dirty worktree changes.
```

Accept through dedicated review:

```text
I approve DECISION-20260614-PROJECT-GAMMA-DELETION-A1 Option: Accept through dedicated deletion review. Create a deletion-review TaskSpec for _projects/project-gamma, inventory the 188 deletions, and do not commit until the review evidence is complete.
```

Defer:

```text
I choose DECISION-20260614-PROJECT-GAMMA-DELETION-A1 Option: Defer. Do not stage or restore _projects/project-gamma in this session.
```
