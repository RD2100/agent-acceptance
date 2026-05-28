# Next Agent Handoff -- RD2100 Agent Runtime v2

> Date: 2026-05-27
> Canonical root: `D:\agent-acceptance`
> Purpose: cold-start handoff for a new coding/reviewer agent

## Read This First

This repository is a governance/runtime acceptance project. Do not treat the existing assets as permission to execute tools, install skills, enable MCP, run hooks, consume queues, or write memory.

The project has reached a sealed documentation/governance state:

| Track | State |
|---|---|
| Phase 0-5 Runtime governance | complete |
| Resource Integration R0-R7 | sealed |
| Capability Routing CR0-CR5 | sealed |
| Phase 6 external source review | complete |
| Taste-Skill | `candidate_for_sandbox_dry_run` only |
| Understand Anything | `quarantine_permanent` |

## Current Source Of Truth

- Canonical root: `D:\agent-acceptance`
- Secondary clone: `D:\dev-frame\agent-acceptance` is not the write target
- Deprecated alias: `D:\devFrame` must not be used
- Existing dirty baseline was intentionally preserved during the runtime work
- Do not assume old phase/status docs are current if newer final reports disagree

Most current final-state references:

| Topic | File |
|---|---|
| Overall runtime status | `docs/agent-runtime/runtime-v2-final-status.md` |
| Resource integration final audit | `docs/agent-runtime/resource-integration-final-audit.md` |
| Resource integration handoff | `docs/agent-runtime/resource-integration-handoff.md` |
| Capability routing final audit | `docs/agent-runtime/capability-routing-final-audit.md` |
| Capability routing handoff | `docs/agent-runtime/capability-routing-handoff.md` |
| Taste-Skill static review | `docs/agent-runtime/phase-6e-static-review-report.md` |
| Taste-Skill 6F decision | `docs/agent-runtime/phase-6f-promotion-decision.md` |
| Understand Anything 6E/6F decision | `docs/agent-runtime/phase-6e-6f-ua-combined-report.md` |

## What Was Completed

### Runtime v2 Core

The runtime now has:

- Operating model
- Integration contracts
- Verification gates
- Memory architecture
- Tool policy
- Skill trigger matrix
- External skill intake policy
- FMEA and STRIDE risk models
- Runtime invariants
- Negative acceptance tests
- Reviewer playbooks
- Audit-only hook drafts
- JSON schemas

Important: pre-edit.governance.ps1 is ACTIVE (registered in Claude Code settings.json, blocks memory/sealed/secrets writes). The other 4 hook files under `hooks/` remain draft/audit-only and must not be registered without a new human gate.

### Resource Integration R0-R7

All local resources were registered and constrained:

| Resource | Final Rule |
|---|---|
|  | MCP disabled; filesystem snapshot only unless separately approved |
| test-frame | evidence provider only; no aggregator/attribution execution |
| dev-frame | adapter design only; no smoke test execution |
| CodeGraph | stale-aware; no auto-reindex; empty/stale indexes not trusted |
| Local skills | reference/intake only; no auto-load or execution |
| RD2100 memory | read-only reference; never current fact |
| Scripts | not_run; require ScriptSafetyRecord and human gate |
| WorkQueue | read-only; no consumption |

### Capability Routing

Capability routing is complete. Future agents must:

1. Identify the task type.
2. Check `docs/agent-runtime/task-capability-routing-matrix.md`.
3. Declare expected, forbidden, and fallback capabilities.
4. Explain if a preferred capability is skipped.
5. Include a `Capability Routing Audit` in final reports for non-trivial tasks.

CodeGraph example:

- For structural code questions, check CodeGraph first.
- If the index is empty/stale/unavailable, say so and use the approved fallback.
- Do not silently fall back to grep/read without explanation.

### Phase 6 External Sources

| Source | Final Decision | Notes |
|---|---|---|
| Taste-Skill | `candidate_for_sandbox_dry_run` | Static review passed with restrictions; no install/execute/auto-load. |
| Understand Anything | `quarantine_permanent` | Critical risk: Node/pnpm monorepo, IDE plugins, install scripts, symlink/config mutation. |
| ECC | defer | Still deferred from Phase 6A. |
| AnySearch Skill | defer | Still deferred. |
| addyosmani-agent-skills-zh | defer | Still deferred. |
| AnySearch MCP Server | reject | Permanent reject. |
| Anthropic Cybersecurity Skills | reject | Permanent reject. |
| UI-TARS Desktop | reject | Permanent reject. |

Taste-Skill quarantine:

- Path: `skills-inbox/quarantine/sources/Taste-Skill__3c7017d/`
- Commit: `3c7017d636c3a4aad378433ea6d0cfa6c921da4a`
- `install_allowed=false`
- `execute_allowed=false`
- `mcp_enable_allowed=false`
- `hook_registration_allowed=false`
- `runtime_loadable=false`

Understand Anything quarantine:

- Path: `skills-inbox/quarantine/sources/Understand-Anything__478962e/`
- Fingerprint: `478962e`
- No install, no execution, no MCP, no runtime integration
- Keep permanently quarantined unless a future human explicitly authorizes a new architecture-level review

## What Is Still Open

There are no required construction tasks left.

Only optional, separately gated future actions remain:

| Optional Action | Required Before Starting |
|---|---|
| Taste-Skill sandbox dry-run | New TaskSpec, one selected skill file, bounded task, reviewer human gate |
| CodeGraph reindex for `D:\agent-acceptance` | Explicit human approval; current/old index may be empty |
| Understand Anything re-evaluation | SBOM, network-isolated sandbox, no installer execution, architecture review |
| WorkQueue/script dry-run | ScriptSafetyRecord + human gate |

## Recommended Next Action

If the next agent is asked to continue productively, do this first:

1. Run `git status --short`.
2. Read this file.
3. Read `docs/agent-runtime/capability-routing-handoff.md`.
4. Read the one topic-specific final report for the task.
5. Produce a small `Capability Routing Audit` before doing any work.

If the user asks "what should we do next?", recommend one of:

- Taste-Skill sandbox dry-run planning, not execution
- CodeGraph reindex approval package, not direct reindex
- Final packaging/index cleanup for reviewer navigation

## Do Not

- Do not install Taste-Skill.
- Do not execute `skill.sh`.
- Do not execute any quarantined source.
- Do not run `npm install`, `pnpm install`, `pip install`, build, or tests in quarantine.
- Do not enable MCP.
- Do not register additional hooks beyond pre-edit (human gate required per hook).
- Do not use any capability that does not appear in `docs/agent-runtime/capability-inventory.md` with Status: approved.
- Do not install plugins or register hooks without first proposing and getting approval for the capability in capability-inventory.md.
- Do not assume a Both-platform capability is available on both platforms -- verify it is enabled on the specific platform before use.
- Do not modify `.git/hooks`.
- Do not write RD2100 memory.
- Do not consume WorkQueue.
- Do not run `scripts/*.ps1` without ScriptSafetyRecord and human gate.
- Do not reindex CodeGraph without human approval.
- Do not copy external SKILL.md files wholesale into `AGENTS.md`, `rules/`, memory, or runtime docs.
- Do not treat historical reports as current validation.
- Do not mark unknown/skipped/blocked checks as pass.
- Do not push/commit/delete/reset/clean/checkout/stash unless the user explicitly authorizes that git operation.

## Review Focus For The Next Agent

When reviewing future work, focus on these checks:

1. Did the agent include a Capability Routing Audit?
2. Did it use or skip CodeGraph for the right reason?
3. Did any forbidden capability run?
4. Did any quarantined source get installed/executed/copied?
5. Did memory become a source of fact?
6. Did any script or WorkQueue mutate state?
7. Did any old status document override newer final reports?
8. Did changed files stay inside approved outputs?
9. Did the report distinguish "candidate" from "approved/enabled"?
10. Did Phase 6 decisions remain restrictive?

## Quick Final State

```text
Runtime v2: complete
Resource Integration: sealed
Capability Routing: sealed
Phase 6: complete
Taste-Skill: candidate_for_sandbox_dry_run only
Understand Anything: quarantine_permanent
No capability is currently approved for install/runtime enablement
```

