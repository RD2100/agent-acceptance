# Skills Inbox -- RD2100 Agent Runtime v2

> Batch B1, 2026-05-27

## Purpose

The skills inbox is the entry point for all new skills entering the RD2100 Agent Runtime. In Phase 0-5 it records intake metadata only: discovery, evaluation notes, risk review, and deferral. Installation is out of scope until a later human-approved phase.

## Directory Structure

```
skills-inbox/
  README.md              <- This file
  external/              <- External skills awaiting intake
    README.md            <- External intake area docs
    <skill-name>/        <- Per-skill intake workspace
      evaluation/        <- Evaluation checklist and notes
      sandbox/           <- Future sandbox notes (not executed in Phase 0-5)
      review/            <- Gate review and final decision
```

## Intake Pipeline

```
skills-inbox/external/<skill-name>/
  |
  +-- Stage 1: Skill files placed here (discovery)
  |
  +-- Stage 2: evaluation/README.md (evaluation checklist)
  |
  +-- Stage 3: sandbox/report.md (future sandbox plan, not execution)
  |
  +-- Stage 4: review/decision.md (gate review, accept/reject)
  |
  +-- Stage 5: Deferred for Phase 6+ Source Lock review
```

## Policy Documents

- `docs/agent-runtime/external-skill-intake.md` -- Full intake policy
- `docs/agent-runtime/skill-trigger-matrix.md` -- When skills trigger
- `docs/agent-runtime/tool-policy.md` -- What tools skills may use
- `docs/agent-runtime/verification-gates.md` -- Quality gates for acceptance

## Current State

- **External inbox**: Empty
- **Pending reviews**: 0
- **Emergency intakes**: 0

## Quick Reference

```text
Phase 0-5 quick reference:
- List inbox contents only.
- Do not create per-skill workspaces unless a batch explicitly approves that output path.
- Do not run sandbox tests.
- Do not install, clone, execute, or load external skills.

See docs/agent-runtime/external-skill-intake.md for the full intake policy.
```
