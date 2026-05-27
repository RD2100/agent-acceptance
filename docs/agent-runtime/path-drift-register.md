# Path Drift Register — RD2100 Agent Runtime v2

> Generated: Batch A2, 2026-05-27
> Purpose: Track all path inconsistencies across the agent runtime ecosystem

## Drift Entry #1: D:\devFrame (MISSING, REFERENCED)

| Field | Value |
|-------|-------|
| **Expected path** | `D:\devFrame` |
| **Actual path** | `D:\dev-frame` (with hyphen) |
| **Status** | **DEPRECATED ALIAS** — does not exist on disk |
| **First observed** | 2026-05-27, Batch A1 |
| **Severity** | **P3** — resolved in code by Batch E; only cosmetic memory alias remains |

### References to D:\devFrame

1. **`D:\agent-acceptance\README.md` line 7**:
   ```
   本仓库是 [ai-workflow-hub](D:\devFrame\ai-workflow-hub) 的**独立验收层**
   ```

2. **`D:\agent-acceptance\README.md` line 11**:
   ```
   $env:AI_WORKFLOW_HUB = "D:\devFrame\ai-workflow-hub"
   ```

3. **`C:\Users\RD\.claude\projects\D--devFrame\`** — Claude project memory directory (4 entries, active)

### Actual Path

- `D:\dev-frame` exists and contains `ai-workflow-hub/` (git repo)
- `D:\dev-frame\CLAUDE.md` describes it as "Dev-Frame Monorepo"

### Impact

- Any script or agent resolving `$env:AI_WORKFLOW_HUB` will fail with path-not-found
- Claude project memory maps to `D--devFrame` (directory name) but the on-disk directory is `D--dev-frame`
- Two different naming conventions coexist: `devFrame` (camelCase, in code/docs) vs `dev-frame` (kebab-case, on disk)

### Resolution

- **Resolved by Batch E (2026-05-27)** — README.md lines 7,11 now reference `D:\dev-frame`
- **Note**: `C:\Users\RD\.claude\projects\D--devFrame` remains as a Claude memory alias (P3, cosmetic)

---

## Drift Entry #2: Dual agent-acceptance Clones

| Field | Value |
|-------|-------|
| **Primary** | `D:\agent-acceptance` (HTTPS remote, dirty worktree) |
| **Secondary** | `D:\dev-frame\agent-acceptance` (SSH remote, clean worktree) |
| **Same repo** | YES — `RD2100/agent-acceptance` |
| **Same commit** | YES — `100a116` |
| **Status** | **DUPLICATE** — awaiting consolidation decision |
| **First observed** | 2026-05-27, Batch A1 |
| **Severity** | **P2** — risk of divergent evolution |

### Differences

| Attribute | Primary (`D:\agent-acceptance`) | Secondary (`D:\dev-frame\agent-acceptance`) |
|-----------|-------------------------------|---------------------------------------------|
| Remote | `https://github.com/RD2100/agent-acceptance.git` | `git@github.com:RD2100/agent-acceptance.git` |
| Worktree | Dirty (13M + 6U) | Clean |
| `.codegraph/` | Present (139KB, 0 indexed) | Absent |
| `templates/` | Present | Absent |
| `runs/` | Present | Absent |

### Resolution

- **Decision**: `D:\agent-acceptance` approved as canonical root
- **Secondary disposition**: Deferred to follow-up batch (remove or convert to worktree)

---

## Drift Entry #3: Claude Project Directory Naming

| Field | Value |
|-------|-------|
| **Path** | `C:\Users\RD\.claude\projects\` |
| **Directories found** | `D--devFrame`, `D--agent-acceptance`, `D--test-frame`, `D--dev-frame` |
| **Status** | **INCONSISTENT** — both `D--devFrame` and `D--dev-frame` exist |
| **Severity** | **P3** — cosmetic, may cause confusion |

### Observation

The Claude projects directory contains entries for BOTH:
- `D--devFrame/` — 4 memory entries, active
- `D--dev-frame/` — present but contents not inspected in this batch

This mirrors the same camelCase vs kebab-case inconsistency.

### Resolution

- **Decision**: Deferred. Non-blocking for Batch A2.

---

## Drift Entry #4: README.md References Upstream Path

| Field | Value |
|-------|-------|
| **File** | `D:\agent-acceptance\README.md` |
| **Pattern** | Hardcoded absolute Windows path to upstream dependency |
| **Current value** | `D:\devFrame\ai-workflow-hub` (broken) |
| **Actual location** | `D:\dev-frame\ai-workflow-hub` |
| **Status** | **FIXED by Batch E** — README.md lines 7,11 now reference `D:\dev-frame` |
| **Severity** | **P3** (resolved; cosmetic memory alias only) |

### Risk

Any new agent or operator following the README setup instructions will encounter a path resolution failure when trying to set `$env:AI_WORKFLOW_HUB`.

### Resolution

- **Resolved by Batch E (2026-05-27)** — README.md lines 7,11 now reference `D:\dev-frame`
- **Note**: `C:\Users\RD\.claude\projects\D--devFrame` remains as a Claude memory alias (P3, cosmetic)

---

## Summary

| # | Drift | Severity | Status |
|---|-------|----------|--------|
| 1 | `D:\devFrame` referenced but does not exist | P3 | Resolved by Batch E; cosmetic alias remains |
| 2 | Dual agent-acceptance clones | P2 | Canonical approved; consolidation deferred |
| 3 | Claude project dir naming inconsistency | P3 | Deferred |
| 4 | Broken upstream path in README.md | P3 | Resolved by Batch E |
