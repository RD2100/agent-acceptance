# Quarantine — RD2100 Agent Runtime v2

> Phase 6 | 2026-05-28

## Purpose

Isolated intake area for external skills before approval.
Skills are cloned here for static analysis only. No code execution.

## Directory Structure

\\\
quarantine/
  README.md           <- This file
  clones/             <- Shallow clones of external skill repos
  scans/              <- Static scan outputs (AST, deps, secrets)
  reports/            <- Quarantine reports per skill
\\\

## Pipeline

See [SourceLock Contract](../docs/agent-runtime/sourcelock-contract.md)

## Active Scans

| Skill | Clone | AST | Deps | Secrets | Report |
|-------|:-----:|:---:|:----:|:-------:|:------:|
| Taste-Skill | pending | - | - | - | - |
| Understand-Anything | pending | - | - | - | - |

## Rules

- No code execution in quarantine
- No network access during scan phase
- All scans are read-only
- Human gate required for approval
