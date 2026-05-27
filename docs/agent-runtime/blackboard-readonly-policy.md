# Blackboard Read-only Policy -- R1

> Batch R1-A, 2026-05-27
> RD2100 Agent Runtime v2
> Resource: res-blackboard-mcp-001

## R1 Boundary

```
R1 = snapshot and audit only.
No MCP registration. No server execution.
No state mutation. No events append. No knowledge write.
```

## MCP Status

```
disabled
```

R1 is split into two sub-phases:
- **R1-DESIGN (current)**: Schema, policy, template, map, checklist, and negative tests are defined. NO bb_* tools are called. MCP remains disabled. All tool lists are future candidate references only.
- **R1-SNAPSHOT (future, requires separate human gate)**: After reviewer explicitly approves, read-only bb_* tools may be called to capture a snapshot. Mutating tools remain forbidden.

Blackboard MCP server is NOT registered in either sub-phase. Even in R1-SNAPSHOT, only the pre-existing MCP channel is used — no new MCP registration occurs.

## Access Matrix

| Resource | Access Mode | Detail |
|----------|-------------|--------|
| state.json | snapshot_only | Read and checksum only; no write |
| events.log | read_only | Read recent entries only; no append |
| knowledge.md | read_only | Search and reference only; no write |
| HANDOVER | read_only | Read protocol only; no modification |
| server.py | forbidden | Must not be executed directly |
| MCP registration | forbidden | Must not be registered at R1 |

## Future Snapshot Candidate Tools (not callable in R1-DESIGN)

The following bb_* tools are permitted in R1. This list matches the Phase 0-5 permitted list from `tool-policy.md`.

| # | Tool | Constraint |
|---|------|------------|
| 1 | bb_register | Session start only |
| 2 | bb_heartbeat | Periodic liveness |
| 3 | bb_status | Read current state |
| 4 | bb_search_knowledge | Read-only search |
| 5 | bb_get_recent_knowledge | Read-only recent knowledge |
| 6 | bb_share_decision | Log decisions (safe write) |
| 7 | bb_report_bug_pattern | Report bugs (safe write) |
| 8 | bb_check_conflicts | Read conflict status |
| 9 | bb_session_files | Read session file list |
| 10 | bb_validate_knowledge | Validate existing entries |
| 11 | bb_deregister | Session end only |

## Forbidden bb_* Tools

The following bb_* tools are FORBIDDEN in R1 because they perform state mutation, file locking, knowledge publication, or critical section acquisition.

| # | Tool | Reason |
|---|------|--------|
| 1 | bb_solidify_knowledge | FORBIDDEN -- permanent knowledge write |
| 2 | bb_share_knowledge | FORBIDDEN -- publishing new knowledge |
| 3 | bb_claim_file | FORBIDDEN -- file locking (mutating) |
| 4 | bb_release_file | FORBIDDEN -- file locking (mutating) |
| 5 | bb_acquire_build_lock | FORBIDDEN -- critical section (mutating) |
| 6 | bb_release_build_lock | FORBIDDEN -- critical section (mutating) |
| 7 | bb_event | FORBIDDEN -- tool not confirmed active |

## Forbidden Actions (Complete List)

The following actions are explicitly forbidden at R1:

1. execute server.py
2. register MCP server
3. modify MCP config
4. write state.json
5. append events.log
6. write knowledge.md
7. call bb_solidify_knowledge
8. call bb_share_knowledge
9. call bb_claim_file
10. call bb_release_file
11. call bb_acquire_build_lock
12. call bb_release_build_lock
13. call bb_event
14. execute blackboard-knowledge-loop skill
15. write RD2100 memory
16. call any mutating bb_* tool not explicitly listed as permitted

## R1 Permitted Actions (Complete List)

The following actions are the ONLY actions permitted on Blackboard at R1:

| # | Action | Detail |
|---|--------|--------|
| 1 | Snapshot state.json | Future (R1-SNAPSHOT): read + checksum; not performed in R1-DESIGN |
| 2 | Read events.log | Future (R1-SNAPSHOT): read recent entries only; not performed in R1-DESIGN |
| 3 | Read knowledge.md | Future (R1-SNAPSHOT): search and reference only; not performed in R1-DESIGN |
| 4 | Call future snapshot candidate bb_* tools | Only after separate human gate for R1-SNAPSHOT; not called in R1-DESIGN |
| 5 | Read HANDOVER | Future (R1-SNAPSHOT): read protocol reference only; not performed in R1-DESIGN |
| 6 | Validate existing knowledge | Future (R1-SNAPSHOT): bb_validate_knowledge; not performed in R1-DESIGN |

## R1 Exit Gate

Before entering R2, the following conditions MUST be met (R1-DESIGN + R1-SNAPSHOT combined):

1. **R1-DESIGN complete**: All 6 R1 documents created, reviewed, and approved.
2. **R1-SNAPSHOT authorized**: Separate human gate explicitly approves snapshot capture.
3. **Tool availability confirmed (after R1-SNAPSHOT gate)**: All 11 future snapshot candidate bb_* tools verified as callable and responsive. NOT verified in R1-DESIGN.
3. **Tool policy confirmed**: All 7 forbidden bb_* tools confirmed as NOT called during R1.
4. **No violations**: Zero forbidden actions executed during R1.
5. **Reviewer approval**: Human reviewer explicitly approves R1 exit.
6. **Contract mapping A3**: All Blackboard contract items in `integration-contracts.md` Appendix A3 verified against actual tool behavior.

## Violation Response

If any forbidden action is detected during R1:

1. **BLOCKED**: The action is blocked immediately. No recovery attempt.
2. **Report to reviewer**: Violation is logged in the ExecutionReport with full context (what was attempted, when, by which batch).
3. **R1 record updated**: The `notes` field documents the violation.
4. **Exit gate blocked**: R1 exit gate becomes conditional on violation resolution by reviewer.
5. **R1 may restart**: Reviewer may require R1 to restart from a clean baseline.

## Verification Checklist

- [ ] state.json exists (path check only; snapshot deferred to R1-SNAPSHOT)
- [ ] All 11 future snapshot candidate bb_* tools listed; callability NOT verified (MCP disabled in R1-DESIGN)
- [ ] All 7 forbidden bb_* tools confirmed NOT called
- [ ] No server.py executed
- [ ] No MCP registration performed
- [ ] No state mutation occurred
- [ ] No knowledge write occurred
- [ ] No events appended
- [ ] Blackboard resource record (blackboard-resource-record.schema.json) created
- [ ] Reviewer gate: all R1 exit conditions met
