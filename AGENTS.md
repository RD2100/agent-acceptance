# AGENTS.md -- RD2100 Agent Runtime v2

> Canonical root: D:\agent-acceptance
> Phase: 0-5 (bootstrap)
> Generated: Batch C2A, 2026-05-27

## Quick Start

New to this runtime? Read in this order:

1. [Operating Model](docs/agent-runtime/operating-model.md) -- execution layers, tiers, exit codes
2. [Integration Contracts](docs/agent-runtime/integration-contracts.md) -- 8 core data contracts
3. [Verification Gates](docs/agent-runtime/verification-gates.md) -- P0-P3 gate hierarchy

## Default Development Process: Sub-Agent Dispatch

This runtime uses the [Sub-Agent Dispatch Protocol](docs/agent-runtime/sub-agent-dispatch-protocol.md) (SADP) as the default development workflow:

```
[Codex Goal Agent]  --TaskSpec-->  [Claude Code Agent]  --ExecutionReport-->  [Goal Agent evaluates]
        ^                                                                              |
        +-------------------------- next TaskSpec or done -----------------------------+
```

- **Codex Goal Agent** (planning tier): Decomposes goals, dispatches TaskSpecs, evaluates ExecutionReports, updates plans.
- **Claude Code Agent** (execution tier): Receives self-contained TaskSpec, implements, collects evidence, returns ExecutionReport.
- All tasks use standardized [TaskSpec](docs/agent-runtime/sub-agent-dispatch-protocol.md#1-taskspec-format) and [ExecutionReport](docs/agent-runtime/sub-agent-dispatch-protocol.md#2-executionreport-format) formats.
- Capability usage is tracked per ExecutionReport and audited against `capability-inventory.md` (core-007).
- Integration: dev-frame (`D:\dev-frame\ai-workflow-hub`) for task state; test-frame (`D:\test-frame`) for evidence patterns.

## Hard Stops (P0)

These rules block delivery. Do not violate:

| # | Rule | Source |
|---|------|--------|
| 1 | No destructive git without human approval | `rules/core.md` core-001 |
| 2 | No secrets in code, logs, or reports | `rules/security.md` sec-001 |
| 3 | No command injection or path traversal | `rules/security.md` sec-002, sec-003 |
| 4 | No fake green (FAILED/BLOCKED != PASS) | `rules/review.md` review-001 |
| 5 | No write to dirty baseline files (13M + 6U) | `rules/core.md` core-005 |
| 6 | No capability without inventory registration | `rules/core.md` core-007 |

## Document Map

```
docs/agent-runtime/
  operating-model.md          <- Execution layers, tiers, lifecycle
  integration-contracts.md    <- 8 core data contracts + system appendix
  verification-gates.md       <- P0-P3 gate hierarchy
  memory-architecture.md      <- 3-layer memory, Phase 0-5 freeze
  tool-policy.md              <- Phase 0-5 active bootstrap policy
  skill-trigger-matrix.md     <- Trigger recommendations (not auto-triggers)
  external-skill-intake.md    <- reference_only / candidate / defer / reject
  resource-inventory.md       <- Batch A2: resource inventory
  frame-fusion-analysis.md    <- Batch A2: cross-frame analysis
  path-drift-register.md      <- Batch A2: known path issues
  source-of-truth-decision.md <- Batch A2: canonical root decision
  capability-inventory.md      <- Cross-platform (27 capabilities, Claude + Codex)
  sub-agent-dispatch-protocol.md <- Default dev workflow
  dispatch-model-profiles.md <- Per-model capability limits + failure patterns
  lessons-learned.md          <- Operational knowledge log (LL-001 to LL-006): TaskSpec + ExecutionReport

rules/
  README.md                   <- Rule index + priority system
  core.md                     <- Runtime core (6 rules)
  coding.md                   <- Code generation (7 rules)
  security.md                 <- Security hard stops (8 rules)
  review.md                   <- Review and evidence (6 rules)
  git.md                      <- Git safety (6 rules)
  research.md                 <- Read-only exploration (5 rules)
  frontend.md                 <- Frontend (6 rules, reference)

hooks/
  pre-edit.governance.ps1    <- ACTIVE governance hook (registered, blocks on memory/sealed/secrets)
  *.audit.draft.ps1 (other 4) <- Audit-only draft hooks (not registered, exit 0 always)
  register-hooks.ps1          <- Registration script (human-gated)
  sealed-files-manifest.json  <- Sealed file/dir manifest (22 files, 3 dirs)
  registration-config.json    <- Manual merge config snippet

skills-inbox/
  README.md                   <- Intake pipeline overview
  external/README.md          <- External skill intake area
```

## Phase 0-5 Boundary

The following are **NOT active** in Phase 0-5:

- Hooks: pre-edit is active (blocks memory/sealed/secrets edits). Other 4 hooks are audit-only drafts. No further registration without human gate.
- External skills: not installed, not cloned, not executed
- Memory writes: read-only; MemoryUpdateRecord proposals only
- Package install: forbidden (npm, pip, yarn)
- MCP config changes: forbidden
- Git mutations: no commit, stash, reset, clean, checkout, push, delete
- Dirty baseline (13M + 6U): do not touch
- Capability registration: all new capabilities must be registered in capability-inventory.md and reviewer-approved before enablement

See [tool-policy.md](docs/agent-runtime/tool-policy.md) for the full Phase 0-5 bootstrap policy.
