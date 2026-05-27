# Memory Architecture -- RD2100 Agent Runtime v2

> Batch B1R, 2026-05-27

## Phase 0-5 Memory Freeze (ACTIVE)

During Phase 0-5 bootstrap, the memory system is **read-only** for agents.

### What Agents CAN Do

| Action | Allowed? | Mechanism |
|--------|:---:|-----------|
| Read MEMORY.md index | YES | `Read` tool |
| Read memory files (*.md) | YES | `Read` tool (no secrets) |
| Read ACTIVE.md | YES | `Read` tool |
| Query Blackboard recent knowledge | YES | `bb_get_recent_knowledge` |
| Search Blackboard knowledge | YES | `bb_search_knowledge` |
| Validate Blackboard knowledge | YES | `bb_validate_knowledge` |
| Register session | YES | `bb_register` |
| Share decisions | YES | `bb_share_decision` |
| Report bug patterns | YES | `bb_report_bug_pattern` |
| Propose MemoryUpdateRecord | YES | Include in ExecutionReport only |

### What Agents CANNOT Do (Phase 0-5)

| Action | Forbidden? | Reason |
|--------|:---:|--------|
| Write to `memory/*.md` files | FORBIDDEN | File system mutation |
| Write to `agent-state.db` | FORBIDDEN | Database mutation |
| Call `bb_solidify_knowledge` | FORBIDDEN | Permanent knowledge write |
| Call `bb_share_knowledge` | FORBIDDEN | Publishing new knowledge |
| Modify `MEMORY.md` index | FORBIDDEN | File system mutation |
| Modify `ACTIVE.md` | FORBIDDEN | Global rules mutation |
| Create new memory files | FORBIDDEN | File system mutation |

### MemoryUpdateRecord Protocol

When an agent identifies knowledge worth preserving:

1. Create a `MemoryUpdateRecord` (see `integration-contracts.md`, Contract 8)
2. Set `status: "proposed"`
3. Include it in the ExecutionReport
4. Do NOT write the actual memory

The human reviewer will:
1. Review the proposed record
2. Approve (`status: "approved"`) or reject (`status: "rejected"`)
3. If approved, handle writing in a future phase or manually

---

## Three-Layer Memory Model

```
+------------------------------------------------------------------+
| Layer 3: Collaborative (Blackboard)                               |
| Cross-session knowledge sharing, bug patterns, decisions          |
| Storage: Blackboard MCP server                                     |
| Phase 0-5: READ + report_bug_pattern + share_decision ONLY         |
| Phase 0-5 FORBIDDEN: solidify_knowledge, share_knowledge           |
+------------------------------------------------------------------+
        ^
        |  (future phase: solidify after human approval)
        v
+------------------------------------------------------------------+
| Layer 2: Structured (agent-state.db)                              |
| SQL-queryable structured memory, skill evolution tracking         |
| Storage: SQLite (agent-state.db)                                   |
| Phase 0-5: READ-ONLY (if accessible). NO WRITES.                   |
+------------------------------------------------------------------+
        ^
        |  (future phase: extract patterns after human review)
        v
+------------------------------------------------------------------+
| Layer 1: File (memory/*.md)                                       |
| Human-readable persistent experience and knowledge                 |
| Storage: Markdown files with YAML frontmatter                      |
| Phase 0-5: READ-ONLY. NO WRITES.                                   |
+------------------------------------------------------------------+
```

## Layer Details

### Layer 1: File Memory

**Location**: `C:\Users\RD\.claude\projects\D--agent-acceptance\memory\` (project-local)
**Global fallback**: `C:\Users\RD\.codex\memories\RD2100-memory\`

**Phase 0-5 status**: Read-only. Agent may read existing memories for context. Agent may propose new memories via MemoryUpdateRecord in ExecutionReport. Agent must not write files.

### Layer 2: Structured Memory (agent-state.db)

**Phase 0-5 status**: Read-only if accessible. Agent must not write to agent-state.db. No new task_executions, skill_evolution, or session_log entries via agent action.

### Layer 3: Collaborative Memory (Blackboard)

**Phase 0-5 allowed operations**:
- `bb_register` -- Session start
- `bb_get_recent_knowledge` -- Get recent knowledge
- `bb_search_knowledge` -- Search knowledge base
- `bb_share_decision` -- Log state-changing decisions
- `bb_report_bug_pattern` -- Report discovered bugs
- `bb_validate_knowledge` -- Validate existing entries

**Phase 0-5 forbidden operations**:
- `bb_solidify_knowledge` -- FORBIDDEN (permanent write)
- `bb_share_knowledge` -- FORBIDDEN (publishing new knowledge)

## Session Memory Flow (Phase 0-5)

```
Session Start:
  1. bb_register(name, task, session_id)
  2. bb_get_recent_knowledge(48)  -> recent bug patterns
  3. Read MEMORY.md index (read-only)
  4. Read ACTIVE.md for current rules

During Session:
  5. bb_share_decision() for state-changing actions
  6. bb_report_bug_pattern() for discovered issues
  7. Collect proposed MemoryUpdateRecords (do NOT write)

Session End:
  8. Include proposed MemoryUpdateRecords in ExecutionReport
  9. Do NOT write memory files
  10. Do NOT call bb_solidify_knowledge
  11. Do NOT write agent-state.db
```

## Session Memory Flow (Future Phase -- NOT ACTIVE)

```
The following is REFERENCE ONLY. Do NOT execute in Phase 0-5.

Session End (Phase 6+):
  - recursive-improve: extract learnings
  - Write new memories to Layer 1 (memory/*.md) -- AFTER human approval
  - Update MEMORY.md index -- AFTER human approval
  - bb_solidify_knowledge() for validated findings -- AFTER human approval
  - Record skill execution results in agent-state.db -- AFTER human approval
```

## Project Memory Status (as of 2026-05-27)

| Location | Status | Phase 0-5 |
|----------|--------|-----------|
| `C:\Users\RD\.codex\memories\RD2100-memory\` | Active (80+ files) | Read-only |
| `C:\Users\RD\.claude\projects\D--agent-acceptance\memory\` | Empty | Read-only (nothing to read yet) |
| `C:\Users\RD\.claude\projects\D--devFrame\memory\` | Active (4 entries) | Read-only |
| `C:\Users\RD\.claude\ACTIVE.md` | Active | Read-only |
