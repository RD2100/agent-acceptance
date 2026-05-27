# Resource Inventory — RD2100 Agent Runtime v2

> Generated: Batch A2, 2026-05-27
> Source: Batch A1 read-only inventory
> Status: baseline, approved by reviewer

## Overview

Three local resource paths were inventoried:

| Path | Exists | Git Repo | Role |
|------|--------|----------|------|
| `D:\agent-acceptance` | YES | YES (standalone) | Canonical root — agent acceptance framework |
| `D:\dev-frame` | YES | NO (loose collection) | Cross-project governance monorepo container |
| `D:\test-frame` | YES | YES (standalone) | Universal automated bug discovery platform |
| `D:\devFrame` | **NO** | — | Deprecated alias (see path-drift-register) |
| `D:\dev-frame\agent-acceptance` | YES | YES (standalone) | Secondary clone of agent-acceptance (SSH remote) |

## D:\agent-acceptance (Canonical Root)

- **Remote**: `https://github.com/RD2100/agent-acceptance.git`
- **Branch**: `master`
- **HEAD**: `100a116 feat: agent-acceptance v1.0`
- **Worktree status**: **dirty** — 13 modified + 6 untracked
- **CodeGraph**: `.codegraph/codegraph.db` exists (139 KB), but **files indexed = 0** (index is empty)

### Modified files (13)

```
README.md
agent-workqueue/QUEUE_INDEX.md
agent-workqueue/cleanup-dryrun.queue.json
agent-workqueue/docs-quality.queue.json
agent-workqueue/local-quality.queue.json
agent-workqueue/recovery-regression.queue.json
agent-workqueue/release-readiness.queue.json
docs/FLOW_CATALOG.md
docs/NEXT_STAGE_BACKLOG.md
docs/RUNBOOK.md
scripts/Run-WorkQueue.ps1
scripts/Test-WorkQueue.ps1
scripts/examples/batch-docs-quality.json
```

### Untracked files (6)

```
.claude/
.codegraph/
docs/COMMAND_CHEATSHEET.md
docs/SINGLE_PROJECT_ADOPTION.md
docs/SINGLE_PROJECT_QUEUE_SPEC.md
templates/
```

### Directory structure

| Directory | Purpose |
|-----------|---------|
| `scripts/` | 7 PowerShell scripts (Run-Smoke, Run-Batch, Run-WorkQueue, Run-AllQueues, Run-QueueGroup, Test-WorkQueue, Write-Report) + examples/ |
| `agent-workqueue/` | 5 Tier-graded queue JSONs + QUEUE_INDEX.md |
| `docs/` | 15 Markdown docs (RUNBOOK, FLOW_CATALOG, RECOVERY_PIPELINE, etc.) |
| `templates/` | AGENTS.single-project.md + 2 queue JSON templates |
| `.codegraph/` | codegraph.db (139KB, empty index) + WAL/SHM |
| `runs/` | powershell-acceptance/ historical run records |

### Missing

- No `CLAUDE.md` at project root
- No `AGENTS.md` at project root

## D:\dev-frame (Monorepo Container)

- **Git repo**: NO — no `.git`, no `.gitmodules`
- **CLAUDE.md**: 79 lines, describes "Cross-project governance chain"
- **Smoke test**: `smoke_test.py` — latest run 2026-05-27, 3/3 PASS
- **CodeGraph**: `.codegraph/codegraph.db` (13.5 MB), **files indexed = 410**

### Sub-projects

| Sub-directory | Git Repo | Description |
|---------------|----------|-------------|
| `agent-acceptance/` | YES | Secondary clone of agent-acceptance (SSH, clean, same commit `100a116`) |
| `ai-workflow-hub/` | YES | Core state machine + 5-agent pipeline |
| `ai-workflow-hub-e2e/` | YES | Evidence integrity + gate tests (168 tests) |
| `codegraph/` | YES | Local-first code intelligence library (tree-sitter) |
| `ai-workflow-hub-e2e-test/` | YES | Test repo |
| `ai-workflow-hub-test-repo/` | YES | Test repo |
| `aihub-worktrees/` | — | Git worktree collection |
| `runs/` | — | powershell-acceptance/ run records |

### Smoke test results (2026-05-27)

| # | Project | Status | Detail |
|---|---------|--------|--------|
| 1 | CodeGraph type-check | PASS | 0 errors |
| 2 | ai-workflow-hub core state tests | PASS | 31 passed |
| 3 | ai-workflow-hub-e2e evidence + gate tests | PASS | 168 passed |

## D:\test-frame (Bug Discovery Platform)

- **Git repo**: YES — standalone
- **CodeGraph**: `.codegraph/codegraph.db` (1.8 MB), **files indexed = 102**

### Key documents

| File | Size |
|------|------|
| `ARCHITECTURE.md` | 20 KB |
| `PIPELINE.md` | 20 KB |
| `INTEGRATION_PLAN.md` | 23 KB |
| `TOOL_SELECTION.md` | 15 KB |
| `README.md` | 2 KB |
| `SETUP.md` | 7 KB |
| `VERIFY.md` | 5 KB |
| `QUALITY_CHECKLIST.md` | 5 KB |

### Architecture layers

| Layer | Directory | Purpose |
|-------|-----------|---------|
| CLI | `cli/` | Unified command entry |
| Orchestrator | `orchestrator/` | Task orchestration |
| Evidence | `evidence/` | Log evidence collection |
| Aggregator | `aggregator/` | Result aggregation |
| Attribution | `attribution/` | Defect attribution engine |
| Tests | `tests/` | Test case repository (android, api, fittrack, h5, miniapp) |
| Reports | `reports/` | allure-results, jest-results, failure_history |
| Config | `config/` | Unified configuration layer |

### Test coverage

- Android App (Maestro + Airtest/Poco)
- WeChat MiniProgram (miniprogram-automator)
- H5/uni-app (Playwright)
- Backend API (MeterSphere + Apifox)
- Cloud device compatibility (WeTest)
- Crash monitoring (Sentry + Bugly)

## D:\dev-frame\agent-acceptance (Secondary Clone)

- **Remote**: `git@github.com:RD2100/agent-acceptance.git` (SSH)
- **Branch**: `master`
- **HEAD**: `100a116 feat: agent-acceptance v1.0` (same as canonical)
- **Worktree**: **clean** (no modified, no untracked)
- **Missing vs canonical**: no `.claude/`, `.codegraph/`, `templates/`, `runs/`
- **Has**: `scripts/`, `agent-workqueue/`, `docs/` (subset)

## D:\devFrame (Deprecated Alias)

- **Exists**: NO
- **Referenced by**:
  - `D:\agent-acceptance\README.md` line 7 (HISTORICAL — fixed by Batch E; now reads `D:\dev-frame`)
  - `D:\agent-acceptance\README.md` line 11 (HISTORICAL — fixed by Batch E; now reads `D:\dev-frame`)
  - `C:\Users\RD\.claude\projects\D--devFrame\` — Claude project memory (4 entries, P3 cosmetic alias)

## CodeGraph Summary

| Project | DB Size | Files Indexed | Status |
|---------|---------|---------------|--------|
| agent-acceptance | 139 KB | **0** | Index exists but empty |
| dev-frame | 13.5 MB | **410** | Active, full index |
| test-frame | 1.8 MB | **102** | Active, full index |
