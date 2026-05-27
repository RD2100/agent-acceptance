# Phase 6F Promotion Decision

> Date: 2026-05-27
> Scope: Taste-Skill static-review result and Understand Anything blocker

## Executive Assessment

`pass_with_restrictions`

Taste-Skill may advance from quarantine static review to `candidate_for_sandbox_dry_run` only. This is not approval to install, execute, auto-load, copy into runtime rules, enable MCP, or register hooks.

Understand Anything remains blocked because the source could not be cloned after repeated network failures.

## Decision Matrix

| Source | Current State | Decision | Rationale |
|---|---|---|---|
| Taste-Skill | cloned to quarantine, commit locked, static reviewed | `candidate_for_sandbox_dry_run` | Prompt/skill collection with MIT license, no package manifest, no postinstall; has strong prompt directives and install docs, so direct enablement remains forbidden. |
| Understand Anything | not cloned | `blocked` | GitHub/source unreachable; no commit SHA, no SOURCELOCK, no static review. |

## Taste-Skill Allowed Next Step

Only a future sandbox dry-run plan may be drafted, with all of the following restrictions:

- Select exactly one target skill file for evaluation.
- Do not install via `npx skills add`.
- Do not execute `skill.sh`.
- Do not auto-load any skill.
- Do not copy SKILL.md wholesale into AGENTS.md, rules, memory, or runtime docs.
- Do not enable MCP or external service integration.
- Do not allow network-dependent media generation unless separately approved.
- Require Capability Routing Audit in any future dry-run report.

## Still Forbidden

| Action | Status |
|---|---|
| Install Taste-Skill | forbidden |
| Execute Taste-Skill or `skill.sh` | forbidden |
| Auto-load any Taste-Skill skill | forbidden |
| Copy Taste-Skill into runtime rules/AGENTS.md | forbidden |
| Enable MCP from Taste-Skill docs | forbidden |
| Use external source as trusted runtime policy | forbidden |
| Advance Understand Anything | blocked |

## Required Future Gate

Before any sandbox dry-run:

1. Create a sandbox dry-run TaskSpec.
2. Choose one skill file and one bounded UI/documentation task.
3. Define network policy, asset policy, and conflict policy with RD2100 frontend/rules.
4. Reviewer signs human gate.
5. Dry-run result must be evidence-only and cannot mutate runtime policy.

## Final Recommendation

- Allow Resource Track closure for Taste-Skill: yes, with restrictions.
- Allow install/runtime enablement: no.
- Allow Understand Anything retry later: yes, only after network/source availability and a new Phase 6D attempt.

