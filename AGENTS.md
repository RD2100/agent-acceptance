# AGENTS.md -- RD2100 Agent Runtime v2

> Canonical root: D:\agent-acceptance
> Phase: 0-5 (bootstrap)
> Generated: Batch C2A, 2026-05-27

## Quick Start

New to this runtime? Read in this order:

1. [Operating Model](docs/agent-runtime/operating-model.md) -- execution layers, tiers, exit codes
2. [Integration Contracts](docs/agent-runtime/integration-contracts.md) -- 8 core data contracts
3. [Verification Gates](docs/agent-runtime/verification-gates.md) -- P0-P3 gate hierarchy


## Development Process

**Normal conversation** (no `@go`): Direct response. Think before acting, keep changes minimal, obey P0 hard stops.

After non-trivial work completes: auto-write summary report → dispatch to `deepseek/deepseek-v4-pro` → regression test + audit → apply fixes. No pre-execution formalities, but post-completion quality gate at highest standard.

**`@go` triggers [SADP](docs/agent-runtime/sub-agent-dispatch-protocol.md)** (formal workflow):
```
Gate 0 -> TaskSpec -> Execute -> ExecutionReport -> Plan Auditor -> Pass/Block/Escalate
```
- Capability usage tracked per ExecutionReport, audited against `capability-inventory.md` (core-007).
- Integration: dev-frame (`D:\dev-frame\ai-workflow-hub`), test-frame (`D:\test-frame`).


## Anti-Overengineering Gate

When the user proposes a plan, architecture, or feature, apply these criteria before agreeing:

| Signal | Meaning |
|--------|---------|
| No real data flow exists yet | Don't build runtime for hypothetical future |
| Dormant/inactive dependency | Register, don't integrate |
| "Just in case" / "future-proof" | Red flag — ask what concrete trigger makes this necessary now |
| Checker/validator for non-existent input | Will become noise, not safety |
| The proposal solves a problem that hasn't happened | Flag it, explain why it may be premature |

**Rules:**
- Always distinguish "registered/referenced" from "integrated/active"
- If you hear yourself thinking "we might need this later", say it out loud and ask the user to confirm
- Prefer "activation trigger list" over "runtime system that sits idle"
- A 50-line boundary doc is better than an 800-line compatibility layer with no real consumers

This is not about refusing user requests — it's about preventing "layperson guiding expert" dynamics where the human proposes and the agent executes without pushing back.
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


## Agent Secret Safety Rules (P0 — Hard Stop)

These rules apply to ALL agent actions, regardless of @go or normal mode:

| # | Rule |
|---|------|
| 1 | Never write real API keys into repository files |
| 2 | Never write real API keys into .env.example, config.example, README, tests, CI files, packaging files, or release artifacts |
| 3 | Treat every file containing "example", "sample", "template", "packaging", "workflow", "docker", or "README" as secret-sensitive |
| 4 | Before git add or git commit, secret scanning runs on staged diff (via sadp-audit.ps1) |
| 5 | If a suspected secret is found, STOP immediately and report it |
| 6 | If a secret has already been committed, REVOKE/ROTATE the key in the provider console BEFORE cleaning Git history |
| 7 | Default answer to "should I scan?" is YES. Scanning is mandatory, not optional |
| 8 | All .env.example files MUST use strongly invalid placeholders: `__REPLACE_WITH_YOUR_OWN_KEY__`, never `sk-your-key-here` |
| 9 | Agent debug output containing session data (tasks/*result*.txt) MUST NOT be committed |

Full policy: `docs/SECURITY_SECRETS_POLICY.md`
Enforcement: pre-commit hook (`sadp-audit.ps1`), CI, GitHub push protection

## Document Map

```
docs/agent-runtime/
  operating-model.md          <- Execution layers, tiers, lifecycle
  integration-contracts.md    <- 8 core data contracts + system appendix
  verification-gates.md       <- P0-P3 gate hierarchy
  memory-architecture.md      <- 3-layer memory, Phase 0-5 freeze
  tool-policy.md              <- Phase 0-5 active bootstrap policy
  skill-trigger-matrix.md     <- Trigger recommendations
  external-skill-intake.md    <- reference_only / candidate / defer / reject
  sub-agent-dispatch-protocol.md <- SADP v1.0: Gate 0, TaskSpec, dispatch, review, regression
  dispatch-model-profiles.md  <- Per-model capability limits + failure patterns
  lessons-learned.md          <- LL-001 ~ LL-010 operational knowledge log
  docs/agent-runtime/capability-inventory.md     <- Cross-platform (28 capabilities, Claude + Codex)
  authority-matrix.md         <- Who can produce what contract
  contract-evolution-policy.md <- How contracts evolve without breaking consumers
  inactive-frame-registry.md  <- External projects: registered but NOT integrated
  dependency-canaries.md      <- 4 canaries for external dependency behavior verification
  session-ledger.schema.md     <- Per-session compliance evidence ledger
  audit-record.schema.md       <- Independent Plan Auditor output schema
  governance-manifest.md      <- Protected section hashes + drift detection
  
  (Additional: resource-inventory, frame-fusion, path-drift, source-of-truth,
   negative-test-fixtures, red-team, phase reports, etc.)

rules/
  README.md                   <- Rule index + priority system
  core.md                     <- Runtime core (8 rules: core-001 ~ core-008)
  coding.md                   <- Code generation (7 rules)
  security.md                 <- Security hard stops (8 rules)
  review.md                   <- Review and evidence (6 rules)
  git.md                      <- Git safety (6 rules)
  research.md                 <- Read-only exploration (5 rules)
  frontend.md                 <- Frontend (6 rules, reference)

hooks/
  pre-edit.governance.ps1    <- ACTIVE governance hook
  *.audit.draft.ps1 (other 4) <- Audit-only draft hooks
  register-hooks.ps1          <- Registration script (human-gated)
  sealed-files-manifest.json  <- Sealed file/dir manifest
  registration-config.json    <- Manual merge config snippet

templates/runtime-bootstrap/
  bootstrap.ps1               <- One-click governance deployment
  governance-manifest.md      <- Bootstrap integrity manifest (protected sections + drift detection)
  AGENTS.template.md          <- AGENTS.md template
  capability-inventory.template.md <- Capability inventory template
  INSTANTIATION.md            <- Bootstrap instantiation guide
  tool-policy.template.md     <- Tool policy template
  README.md                   <- Bootstrap overview

schemas/
  schemas/draft/              <- Future schemas (NOT active)
  agent-runtime/              <- 9 JSON schemas (TaskSpec, ExecutionReport, etc.)
  resource-integration/       <- 10 resource integration schemas

skills-inbox/
  README.md                   <- Intake pipeline overview
  external/README.md          <- External skill intake area
```


## Phase 0-5 Boundary

The following are **NOT active** in Phase 0-5:

- Hooks: pre-edit is active (blocks memory/sealed/secrets edits). Other 4 hooks are audit-only drafts. No further registration without human gate.
- External skills: not installed, not cloned, not executed
- Memory writes: now active (post-Audit); MemoryUpdateRecord auto-applied
- Package install: forbidden (npm, pip, yarn)
- MCP config changes: forbidden
- Git mutations: no commit, stash, reset, clean, checkout, push, delete
- Dirty baseline (13M + 6U): do not touch
- Capability registration: all new capabilities must be registered in docs/agent-runtime/capability-inventory.md and reviewer-approved before enablement

See [tool-policy.md](docs/agent-runtime/tool-policy.md) for the full Phase 0-5 bootstrap policy.
