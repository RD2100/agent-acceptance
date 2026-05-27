# External Skills Inbox -- RD2100 Agent Runtime v2

> Batch B1, 2026-05-27

## Purpose

This directory receives external skills that have been submitted for evaluation and potential inclusion in the RD2100 Agent Runtime. All skills entering this directory go through the full intake pipeline defined in `docs/agent-runtime/external-skill-intake.md`.

## Intake Criteria Summary

Every external skill must pass:

| Gate | Requirement |
|------|-------------|
| **P0 Security** | No destructive defaults, no credential exfiltration, no remote code execution |
| **P1 Correctness** | Skill runs without errors in sandbox (Phase 6+ only, not executed in Phase 0-5), declared dependencies match actual usage |
| **P2 Quality** | Clean code, no performance anti-patterns, no namespace conflicts |

Full criteria: `docs/agent-runtime/external-skill-intake.md`

## Per-Skill Workspace

Each skill gets a workspace directory:

```
skills-inbox/external/<skill-name>/
  <skill-files>              <- Original submitted files
  evaluation/
    README.md                <- Evaluation checklist (Stage 2)
  sandbox/
    report.md                <- Sandbox plan notes (Stage 3, not executed in Phase 0-5)
  review/
    decision.md              <- Gate review + final decision (Stage 4)
```

## Creating a New Intake

# Phase 0-5: not executed, for documentation only.
```bash
SKILL_NAME="my-skill"
mkdir -p "skills-inbox/external/${SKILL_NAME}/evaluation"
mkdir -p "skills-inbox/external/${SKILL_NAME}/sandbox"
mkdir -p "skills-inbox/external/${SKILL_NAME}/review"
```

## Current Queue

- **No skills currently in intake**

## Related Documents

- `../README.md` -- Skills inbox overview
- `../../docs/agent-runtime/external-skill-intake.md` -- Full intake policy
- `../../docs/agent-runtime/skill-trigger-matrix.md` -- Skill trigger reference
- `../../docs/agent-runtime/tool-policy.md` -- Tool usage policy
- `../../docs/agent-runtime/verification-gates.md` -- Verification gate definitions
