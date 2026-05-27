# Frame Fusion Analysis — RD2100 Agent Runtime v2

> Generated: Batch A2, 2026-05-27
> Purpose: Analyze relationships, overlaps, and fusion opportunities across agent-acceptance, dev-frame, and test-frame

## Current Architecture

```
D:\
├── agent-acceptance/          ← Canonical root (acceptance framework)
│   ├── scripts/               ← PowerShell runners
│   ├── agent-workqueue/       ← Tier-graded task queues
│   └── docs/                  ← Runbooks, checklists, templates
│
├── dev-frame/                 ← Loose monorepo container (NOT a git repo)
│   ├── agent-acceptance/      ← Secondary clone (SSH, clean)
│   ├── ai-workflow-hub/       ← Core state machine (git repo)
│   ├── ai-workflow-hub-e2e/   ← E2E evidence tests (git repo)
│   └── codegraph/             ← Code intelligence lib (git repo)
│
└── test-frame/                ← Independent bug discovery platform (git repo)
    ├── orchestrator/          ← Task orchestration
    ├── aggregator/            ← Result aggregation
    ├── attribution/           ← Defect attribution
    └── tests/                 ← Multi-platform test cases
```

## Relationship Matrix

| | agent-acceptance | dev-frame | test-frame |
|---|:---:|:---:|:---:|
| **agent-acceptance** | — | Duplicate clone inside dev-frame | No direct dependency |
| **dev-frame** | Contains secondary clone | — | No direct dependency |
| **test-frame** | No direct dependency | No direct dependency | — |

## Overlap Analysis

### 1. agent-acceptance ↔ dev-frame/agent-acceptance (DUPLICATE)

- **Same repo**: `RD2100/agent-acceptance`
- **Same commit**: `100a116`
- **Different remotes**: HTTPS vs SSH
- **Content delta**: canonical has `.claude/`, `.codegraph/`, `templates/`, `runs/`; secondary does not
- **Worktree delta**: canonical is dirty (13 modified + 6 untracked); secondary is clean

**Risk**: Divergent evolution if both clones receive independent changes.

**Recommendation**: Retain `D:\agent-acceptance` as canonical. Either remove `D:\dev-frame\agent-acceptance` or convert it to a git worktree of the canonical clone.

### 2. agent-acceptance ↔ dev-frame/ai-workflow-hub (LOOSE COUPLING)

- agent-acceptance README claims to be the "independent acceptance layer" for ai-workflow-hub
- References `$env:AI_WORKFLOW_HUB = "D:\devFrame\ai-workflow-hub"` (path drift — actual is `D:\dev-frame\ai-workflow-hub`)
- No hard dependency: agent-acceptance can run smoke/batch/workqueue in dry-run mode without ai-workflow-hub

**Risk**: RESOLVED by Batch E (2026-05-27) — README.md lines 7,11 now reference `D:\dev-frame`. Claude memory alias `D--devFrame` remains as P3 cosmetic.

### 3. agent-acceptance ↔ test-frame (NO OVERLAP)

- agent-acceptance focuses on acceptance scripting (PowerShell runners, workqueues)
- test-frame focuses on automated bug discovery (multi-platform testing, attribution)
- Complementary but not overlapping: agent-acceptance could potentially trigger test-frame runs

**Opportunity**: agent-acceptance workqueues could include test-frame as a verification target in future iterations.

### 4. dev-frame as Monorepo Container (STRUCTURAL CONCERN)

- dev-frame is NOT a git repo — it's a loose directory of independent git repos
- No `.gitmodules`, no submodule tracking, no monorepo-level version control
- Changes to the container structure (adding/removing sub-projects) are not tracked
- This is acceptable for a development workspace but risky for production governance

## Fusion Options

### Option A: Status Quo (Current State)
Keep all three as independent entities. Fix path references only.

**Pros**: Minimal change, no disruption.
**Cons**: Path drift persists until fixed. Duplicate clone risk.

### Option B: Consolidate agent-acceptance
Remove `D:\dev-frame\agent-acceptance`. Keep only canonical `D:\agent-acceptance`.

**Pros**: Eliminates duplicate clone risk.
**Cons**: Loss of SSH-remote clone (may be used in CI/automation contexts).

### Option C: Git Worktree Pattern
Replace `D:\dev-frame\agent-acceptance` with a git worktree of the canonical clone.

**Pros**: Single source of truth, shared object store, no duplicate risk.
**Cons**: Requires git worktree management discipline.

### Option D: Formalize dev-frame as Git Repo
Initialize dev-frame as a git repo with submodules (or a monorepo with sparse checkout).

**Pros**: Versioned container structure, tracked sub-project relationships.
**Cons**: Migration effort, potential disruption to existing workflows.

## Recommendation

**Short-term (this batch)**: Document current state. No structural changes.

**Follow-up batches**:
1. ~~Batch A3: Fix README.md path drift~~ — COMPLETED by Batch E (2026-05-27)
2. Batch B1: Decide and execute agent-acceptance clone consolidation (Option B or C)
3. Batch C1: Evaluate dev-frame monorepo formalization (Option D)

## Blocking Issues for Fusion

1. Reviewer has not yet decided on clone consolidation strategy
2. ~~Path drift fix~~ — resolved by Batch E (2026-05-27)
3. No decision on dev-frame git initialization
