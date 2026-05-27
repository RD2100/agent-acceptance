# Memory Context Map -- R6

> Batch Y (R6), 2026-05-27
> R6 = read-only memory mapping. No memory write. No fact from memory.

## 1. R6 Boundary

R6 maps the RD2100 memory system (3-layer architecture) as a reference-only resource. Memory entries are classified, assessed for stale risk, and assigned conflict checks. No memory is written, modified, or used as current fact.

**Fact priority**: filesystem > git status > command output > CodeGraph > memory > external docs.

## 2. Memory Inventory

### Layer 1: File Memory

| Source | Path | Type | Stale Risk | Notes |
|--------|------|:---:|:---:|-------|
| ACTIVE.md | `C:\Users\RD\.codex\memories\RD2100-memory\ACTIVE.md` | active_rules | medium | Last reviewed 2026-05-24 |
| MEMORY.md | `C:\Users\RD\.codex\memories\RD2100-memory\MEMORY.md` | guide | medium | Index of 80+ entries |
| MEMORY-CALL-GUIDE.md | `C:\Users\RD\.codex\memories\RD2100-memory\MEMORY-CALL-GUIDE.md` | guide | medium | 63 lines, call protocol |
| CLAUDE.md | `C:\Users\RD\.codex\memories\RD2100-memory\CLAUDE.md` | guide | low | Brief pointer |
| Topic docs (~80) | `C:\Users\RD\.codex\memories\RD2100-memory\*.md` | topic | high | Travel app, agent dev, etc. Many are project-specific and may be stale for Runtime v2. |
| Project memory | `C:\Users\RD\.claude\projects\` | project_memory | high | Multiple project dirs; D--agent-acceptance memory is empty |

### Layer 2: Structured Memory (agent-state.db)

| Source | Status | Notes |
|--------|:---:|-------|
| agent-state.db | **not verified** | Existence not confirmed in this session. Not accessible. |

### Layer 3: Collaborative Memory (Blackboard MCP)

| Source | Status | Notes |
|--------|:---:|-------|
| state.json | verified (R1-SNAPSHOT-FS) | 109 B, 6 lines, present |
| state.json.bak | verified (R1-SNAPSHOT-FS) | 109 B, 6 lines, different checksum |
| events.log | not_found | Not configured |
| knowledge.md | not_found | Not populated |

## 3. Stale Risk Classification

| Risk | Criteria | Example |
|:---:|----------|---------|
| high | Topic-specific, project-specific, >30 days since review, or path-dependent | Travel app sprint memories, path references |
| medium | Process/guide, 7-30 days since review, general applicability | ACTIVE.md, MEMORY-CALL-GUIDE.md |
| low | Pointer/framework, <7 days since review, structural | CLAUDE.md (pointer only) |

## 4. Conflict Check Policy

Every memory reference must include a conflict check:
- Does the memory claim conflict with current filesystem state?
- Does the memory claim conflict with git status?
- Does the memory reference a path that has since changed?
- Does the memory claim an agent behavior that contradicts current rules?

If conflict_check cannot be performed (e.g., path not accessible, tool unavailable), this must be recorded as a verification_gap.

## 5. TTL Recommendations

| Memory Type | TTL | Action on Expiry |
|-------------|-----|------------------|
| active_rules | 30 days or after any rules change | Re-read and re-verify |
| guide | 60 days | Re-read; mark stale if not re-verified |
| topic | 30 days | Mark stale; do not use without re-verification |
| project_memory | 30 days or after project phase change | Re-verify against current project state |
| blackboard_memory | Session-based | Re-verify each session via bb_get_recent_knowledge |
| archive | Indefinite | Reference only; always mark as historical |

## 6. Memory vs Fact

Memory is **used_as_reference**, never **used_as_fact**.

- "The memory says the file is at path X" -> check filesystem first
- "The memory says agent Y was used for task Z" -> check git log or evidence first
- "The memory says rule R applies" -> check current rules/ files first

Memory that has not been verified against current state must be tagged `stale_risk=high` and must not be the sole source for any claim.

## 7. MemoryUpdateRecord Protocol (Phase 0-5 ACTIVE)

Per `memory-architecture.md`:
- MemoryUpdateRecord can only be `proposed`
- Agent must not write memory files
- Agent must not call `bb_solidify_knowledge`
- Agent must not write agent-state.db
- Proposed records included in ExecutionReport for reviewer approval
