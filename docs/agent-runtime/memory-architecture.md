# Memory Architecture -- RD2100 Agent Runtime v2

> Batch B1R, 2026-05-27

## Phase 6 Memory Write-Back (ACTIVE as of 2026-05-28)

Memory writes are now permitted for agents under the following conditions:
- Write to `memory/*.md` files: ALLOWED (with review)
- Write to `agent-state.db`: ALLOWED (with review)
- MemoryUpdateRecord proposals: now auto-applied after Audit Pass

Phase 0-5 read-only freeze is lifted. All memory layers are writable.

### Write Procedure
1. Agent proposes memory update in ExecutionReport.MemoryUpdateRecord
2. Plan Auditor reviews for consistency
3. Upon Audit Pass: write to target memory file
4. Update ACTIVE.md index if new topic file created

### What Agents CAN Do

| Action | Allowed? | Mechanism |
|--------|:---:|-----------|
| Read MEMORY.md index | YES | `Read` tool |
| Read memory files (*.md) | YES | `Read` tool (no secrets) |
| Read ACTIVE.md | YES | `Read` tool |
| Register session | YES |  |
| Share decisions | YES |  |
| Report bug patterns | YES |  |
| Propose MemoryUpdateRecord | YES | Include in ExecutionReport only |

### What Agents CANNOT Do (Phase 0-5)

| Action | Forbidden? | Reason |
|--------|:---:|--------|
| Write to `memory/*.md` files | ALLOWED (after Audit Pass) | File system mutation |
| Write to `agent-state.db` | ALLOWED (after Audit Pass) | Database mutation |
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
| Cross-session knowledge sharing, bug patterns, decisions          |
| Phase 6: READ + WRITE (after Audit Pass) + report_bug_pattern + share_decision         |
| Phase 6 FORBIDDEN (without Audit Pass): solidify_knowledge, share_knowledge           |
+------------------------------------------------------------------+
        ^
        |  (future phase: solidify after human approval)
        v
+------------------------------------------------------------------+
| Layer 2: Structured (agent-state.db)                              |
| SQL-queryable structured memory, skill evolution tracking         |
| Storage: SQLite (agent-state.db)                                   |
| Phase 6: READ + WRITE (if accessible). NO WRITES.                   |
+------------------------------------------------------------------+
        ^
        |  (future phase: extract patterns after human review)
        v
+------------------------------------------------------------------+
| Layer 1: File (memory/*.md)                                       |
| Human-readable persistent experience and knowledge                 |
| Storage: Markdown files with YAML frontmatter                      |
| Phase 6: READ + WRITE. NO WRITES.                                   |
+------------------------------------------------------------------+
```

## Layer Details

### Layer 1: File Memory

**Location**: `C:\Users\RD\.claude\projects\D--agent-acceptance\memory\` (project-local)
**Global fallback**: `C:\Users\RD\.codex\memories\RD2100-memory\`

**Phase 0-5 status**: Read-only. Agent may read existing memories for context. Agent may propose new memories via MemoryUpdateRecord in ExecutionReport. Agent must not write files.

### Layer 2: Structured Memory (agent-state.db)

**Phase 0-5 status**: Read-only if accessible. Agent must not write to agent-state.db. No new task_executions, skill_evolution, or session_log entries via agent action.


**Phase 0-5 allowed operations**:

**Phase 0-5 forbidden operations**:

## Session Memory Flow (Phase 0-5)

```
Session Start:
  1. (name, task, session_id)
  2. (48)  -> recent bug patterns
  3. Read MEMORY.md index (read-only)
  4. Read ACTIVE.md for current rules

During Session:
  5.  for state-changing actions
  6.  for discovered issues
  7. Collect proposed MemoryUpdateRecords (do NOT write)

Session End:
  8. Include proposed MemoryUpdateRecords in ExecutionReport
  9. Write memory files after Audit Pass
  10. Do NOT call 
  11. Do NOT write agent-state.db
```

## Session Memory Flow (Future Phase -- NOT ACTIVE)

```
The following is REFERENCE ONLY. Do NOT execute in Phase 0-5.

Session End (Phase 6+):
  - recursive-improve: extract learnings
  - Write new memories to Layer 1 (memory/*.md) -- AFTER human approval
  - Update MEMORY.md index -- AFTER human approval
  -  for validated findings -- AFTER human approval
  - Record skill execution results in agent-state.db -- AFTER human approval
```

## Project Memory Status (as of 2026-05-27)

| Location | Status | Phase 0-5 |
|----------|--------|-----------|
| `C:\Users\RD\.codex\memories\RD2100-memory\` | Active (80+ files) | Read-only |
| `C:\Users\RD\.claude\projects\D--agent-acceptance\memory\` | Empty | Read-only (nothing to read yet) |
| `C:\Users\RD\.claude\projects\D--devFrame\memory\` | Active (4 entries) | Read-only |
| `C:\Users\RD\.claude\ACTIVE.md` | Active | Read-only |
