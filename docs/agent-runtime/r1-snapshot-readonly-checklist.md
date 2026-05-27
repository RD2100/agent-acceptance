# R1-SNAPSHOT Read-only Checklist

> Batch R1-SNAP-DESIGN, 2026-05-27
> RD2100 Agent Runtime v2
> Phase: R1-DESIGN (snapshot authorization package design only)

## Critical Header

**This checklist is FUTURE REFERENCE ONLY. No bb_* tools are called in R1-DESIGN. This checklist activates only after the reviewer signs `r1-snapshot-approval-matrix.md`.**

All items below are conditional on reviewer approval. If the reviewer rejects the snapshot request, this checklist is not executed.

---

## Pre-snapshot Verification

Perform ALL of the following **before** calling any bb_* tool. If any check fails, do NOT proceed.

| # | Check | Expected | Result |
|---|-------|----------|:------:|
| 1 | Reviewer approval confirmed | Approval matrix signed `approve` | [ ] PASS / [ ] FAIL |
| 2 | MCP status confirmed disabled | No `mcp_registration` performed; `server.py` not executed | [ ] PASS / [ ] FAIL |
| 3 | `state.json` path confirmed exists | File present at expected path | [ ] PASS / [ ] FAIL |
| 4 | No mutating bb_* tools in session history | grep for forbidden tools returns empty | [ ] PASS / [ ] FAIL |
| 5 | Pre-snapshot checksum captured | SHA256 of `state.json` computed | [ ] PASS / [ ] FAIL |

### Pre-snapshot Decision

| Condition | Action |
|-----------|--------|
| All 5 checks PASS | Proceed to snapshot capture |
| Any check FAILS | **BLOCKED** -- report to reviewer; do NOT call any bb_* tool |

---

## During Snapshot

Execute ONLY if all pre-snapshot checks passed. Call ONLY the 6 read-only bb_* tools authorized in the approval matrix.

### Read-only bb_* Tool Calls

| # | Tool | Purpose | Called? | Response Record |
|---|------|---------|:-------:|-----------------|
| 1 | `bb_status` | Read current Blackboard state | [ ] YES / [ ] SKIP | |
| 2 | `bb_get_recent_knowledge(48)` | Read recent knowledge (48h window) | [ ] YES / [ ] SKIP | |
| 3 | `bb_search_knowledge` | Search for specific topics | [ ] YES / [ ] SKIP | |
| 4 | `bb_session_files` | List session files | [ ] YES / [ ] SKIP | |
| 5 | `bb_check_conflicts` | Check file conflict status | [ ] YES / [ ] SKIP | |
| 6 | `bb_validate_knowledge` | Validate existing knowledge | [ ] YES / [ ] SKIP | |

### During-snapshot Rules

- **Summarize, do not transcribe**: Record topic summaries only for `bb_get_recent_knowledge` and `bb_search_knowledge`. Do NOT read or record full knowledge content.
- **Record, do not act**: Log all tool responses as evidence. Do NOT take any action based on responses.
- **Do not mutate**: If any tool offers to write, modify, or consolidate, decline.

### bb_tools_called Log

Record every bb_* tool actually called during this step:

```
bb_tools_called = [
  ... fill during R1-SNAPSHOT ...
]
```

---

## Post-snapshot Verification

Perform AFTER all snapshot tool calls complete.

| # | Check | Expected | Result |
|---|-------|----------|:------:|
| 1 | `mutating_tools_invoked` | `false` (zero forbidden tools in `bb_tools_called`) | [ ] PASS / [ ] FAIL |
| 2 | `state_mutated` | `false` (post-snapshot checksum matches pre-snapshot) | [ ] PASS / [ ] FAIL |
| 3 | `events_appended` | `false` (no new events logged) | [ ] PASS / [ ] FAIL |
| 4 | `knowledge_written` | `false` (no new knowledge entries) | [ ] PASS / [ ] FAIL |
| 5 | Snapshot JSON matches template | All 22 fields present and valid per `blackboard-snapshot-template.md` | [ ] PASS / [ ] FAIL |
| 6 | `mcp_status` remains `"disabled"` | No registration occurred during snapshot | [ ] PASS / [ ] FAIL |

### Post-snapshot Checksum Verification

| Check | Expected | Actual |
|-------|----------|--------|
| Pre-snapshot checksum | (captured above) | |
| Post-snapshot checksum | Identical to pre-snapshot | |
| Match? | `true` | [ ] YES / [ ] NO |

---

## Hard Stop Conditions

If any of the following conditions are detected, the snapshot is **BLOCKED** immediately. No further bb_* tools are called. The situation is reported to the reviewer.

| # | Hard Stop Condition | Detection Method | Triggered? |
|---|---------------------|-----------------|:----------:|
| 1 | Any forbidden bb_* tool was called | Check `bb_tools_called` against forbidden list | [ ] NO / [ ] YES |
| 2 | `state.json` checksum changed | Compare pre-snapshot and post-snapshot SHA256 | [ ] NO / [ ] YES |
| 3 | Reviewer approval missing | Check approval matrix signature | [ ] NO / [ ] YES |
| 4 | `server.py` was executed | Check bash log for `server.py` invocation | [ ] NO / [ ] YES |
| 5 | MCP was registered | Check for MCP registration command | [ ] NO / [ ] YES |
| 6 | `events.log` was appended | Compare line count pre/post snapshot | [ ] NO / [ ] YES |
| 7 | `knowledge.md` was written | Compare line count pre/post snapshot | [ ] NO / [ ] YES |

### Hard Stop Response

If any hard stop triggers:

1. **BLOCKED**: No further action. No bb_* tools called.
2. **Record**: Document which condition triggered and the evidence.
3. **Report**: Notify reviewer with full context.
4. **No recovery**: Agent does NOT attempt to recover from a hard stop. Reviewer must decide next steps.

---

## Completion Checklist

All items must be complete before submitting the snapshot report to the reviewer.

| # | Item | Status |
|---|------|:------:|
| 1 | Pre-snapshot verification all PASS | [ ] |
| 2 | All 6 authorized bb_* tools called and responses recorded | [ ] |
| 3 | `bb_tools_called` log populated | [ ] |
| 4 | Post-snapshot verification all PASS | [ ] |
| 5 | No hard stop conditions triggered | [ ] |
| 6 | Snapshot JSON filled with observed values | [ ] |
| 7 | Snapshot report submitted to reviewer | [ ] |

---

## References

| Document | Relationship |
|----------|-------------|
| `r1-snapshot-approval-matrix.md` | Human gate that activates this checklist |
| `r1-snapshot.request.json` | SourceLockRequest for snapshot authorization |
| `blackboard-readonly-policy.md` | Defines R1 access matrix, forbidden/permitted actions |
| `blackboard-snapshot-template.md` | Defines the 22-field snapshot record format |
| `r1-blackboard-reviewer-checklist.md` | 10-step reviewer verification procedure (post-snapshot) |
| `r1-snapshot-report-template.md` | Template for the final snapshot report |
