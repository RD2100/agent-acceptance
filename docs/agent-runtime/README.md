# Agent Runtime v2 -- Documentation Index

> K3 Index Agent, 2026-05-27
> Canonical root: D:\agent-acceptance

## Current Status

```
Phase 0-5: COMPLETE | Phase 6A: COMPLETE | Phase 6B-Plan: COMPLETE | Phase 6C: BLOCKED
```

## Quick Entry Points

New reader? Start here:

| Document | Purpose |
|----------|---------|
| [AGENTS.md](../../AGENTS.md) | Overall project navigation and agent entry point (root) |
| [operating-model.md](operating-model.md) | Execution layers, tier semantics, agent lifecycle, exit codes |
| [runtime-v2-final-status.md](runtime-v2-final-status.md) | Current status summary and known blockers (pending creation) |

## Phase 0-5 Core Documents

| # | File | Description |
|---|------|-------------|
| 1 | [operating-model.md](operating-model.md) | Execution layers (L0-L3), tier semantics, dry-run defaults, agent lifecycle |
| 2 | [source-of-truth-decision.md](source-of-truth-decision.md) | Canonical root declaration, approved paths, deprecated aliases |
| 3 | [resource-inventory.md](resource-inventory.md) | Local resource paths, git-repo status, cross-project structure |
| 4 | [path-drift-register.md](path-drift-register.md) | All path inconsistencies across the runtime ecosystem |
| 5 | [frame-fusion-analysis.md](frame-fusion-analysis.md) | Cross-project overlaps and fusion opportunities (agent/dev/test frames) |
| 6 | [verification-gates.md](verification-gates.md) | P0/P1/P2 gate hierarchy every agent execution must pass |
| 7 | [integration-contracts.md](integration-contracts.md) | 8 core data contracts (TaskSpec, RunSpec, EvidenceIndex, GateResult, etc.) |
| 8 | [tool-policy.md](tool-policy.md) | Phase-split tool permissions: read-only bootstrapping, future-phase policies |
| 9 | [memory-architecture.md](memory-architecture.md) | Phase 0-5 memory freeze rules, read-only agent constraints |
| 10 | [skill-trigger-matrix.md](skill-trigger-matrix.md) | Skill classification system (Recommended, Reference, Deferred, Forbidden) |
| 11 | [external-skill-intake.md](external-skill-intake.md) | Intake pipeline: discovery, classification, risk review, deferral |
| 12 | [reviewer-playbook.md](reviewer-playbook.md) | Deterministic reviewer process: evidence chain, fake-green detection, gate decisions |
| 13 | [runtime-invariants.md](runtime-invariants.md) | 40 runtime invariants with P0/P1/P2 priority and violation consequences |
| 14 | [negative-acceptance-tests.md](negative-acceptance-tests.md) | 30 negative acceptance test fixtures for reviewer detection capability testing |

## Phase 6 Documents

| # | File | Description |
|---|------|-------------|
| 1 | [phase-6-source-lock-quarantine.md](phase-6-source-lock-quarantine.md) | Phase 6 design: source lock, quarantine clone, static analysis (review-only) |
| 2 | [phase-6a-approval-pack.md](phase-6a-approval-pack.md) | Phase 6A human-approval workflow BEFORE any clone operation |
| 3 | [phase-6a-approval-matrix.md](phase-6a-approval-matrix.md) | Reviewer decisions: 5 projects evaluated, 2 approved for source-lock planning |
| 4 | [phase-6b-source-lock-plan.md](phase-6b-source-lock-plan.md) | Phase 6B source lock plans for Taste-Skill and Understand Anything |
| 5 | [phase-6b-handoff.md](phase-6b-handoff.md) | Full handoff package from Phase 6B to Phase 6C (pending creation) |

## Reviewer Materials

| # | File | Description |
|---|------|-------------|
| 1 | [runtime-invariants.md](runtime-invariants.md) | 40 runtime invariants -- P0 hard stops cannot be downgraded |
| 2 | [negative-acceptance-tests.md](negative-acceptance-tests.md) | 30 negative test fixtures with expected gate decisions and hard-stop flags |
| 3 | [fmea-risk-analysis.md](fmea-risk-analysis.md) | FMEA risk analysis (AIAG-VDA methodology) for Phase 0-5 constraints |
| 4 | [stride-threat-model.md](stride-threat-model.md) | STRIDE threat model (Microsoft SDL) covering all 6 threat categories |
| 5 | [verification-gates.md](verification-gates.md) | Gate hierarchy: P0 Security, P1 Correctness, P2 Quality |

## Schemas

Formal JSON Schema definitions (Draft 2020-12) for the 8 core integration contracts, plus a source-lock record schema.

See: [schemas/agent-runtime/README.md](../../schemas/agent-runtime/README.md)

## Phase 6C Next Steps

**Status: BLOCKED**

Phase 6C cannot proceed until the following prerequisites are satisfied:

1. **Source URLs required**: Taste-Skill and Understand Anything need canonical source URLs before clone can be authorized
2. **Clone requires separate Phase 6C approval**: Clone into quarantine is a distinct gate, not covered by Phase 6A/6B planning approval
3. **No clone, no install, no execution** is permitted in the current phase
4. Refer to `phase-6b-handoff.md` (pending creation) for the full handoff package

The 3 deferred projects (ECC, AnySearch Skill, addyosmani-agent-skills-zh) remain out of scope until the medium-risk cycle completes.
