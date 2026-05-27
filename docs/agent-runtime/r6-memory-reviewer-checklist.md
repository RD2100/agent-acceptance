# R6 Memory Reviewer Checklist -- RD2100 Agent Runtime v2

> Batch Y (R6), 2026-05-27
> 10-step review process for R6 memory context outputs.

## Step 1: Scope Check
- [ ] All R6 files exist in approved paths only
- [ ] No writes to C:\Users\RD or any memory directory
- [ ] No existing memory files modified

## Step 2: Approved Outputs Check
- [ ] memory-context-record.schema.json: exists, parseable
- [ ] memory-context-map.md: complete inventory, stale risk, conflict check, TTL
- [ ] stale-memory-review-checklist.md: staleness/conflict/risk/TTL checks
- [ ] r6-memory-negative-tests.md: >= 20 scenarios
- [ ] r6-memory-reviewer-checklist.md: this file

## Step 3: Changed Files Check
- [ ] git status shows only R6 approved outputs
- [ ] 13M + 6U baseline unchanged
- [ ] No C:\Users\RD writes
- [ ] No memory files modified

## Step 4: Command Audit
- [ ] No file writes to C:\Users\RD\.codex\, C:\Users\RD\.claude\
- [ ] No agent-state.db writes
- [ ] No dream-reflection, recursive-improve, memory-bridge execution

## Step 5: Forbidden Action Check
- [ ] Memory written? Must be NO
- [ ] Memory used as current fact? Must be NO
- [ ] agent-state.db written? Must be NO
- [ ] MEMORY.md modified? Must be NO
- [ ] Memory files moved/deleted? Must be NO

## Step 6: Schema Parse Check
- [ ] memory-context-record.schema.json parses
- [ ] access_mode const="read_only" enforced
- [ ] write_allowed const=false enforced
- [ ] used_as_fact const=false enforced
- [ ] stale_risk required and enum valid
- [ ] conflict_check required

## Step 7: Negative Test Coverage
- [ ] >= 20 negative tests total
- [ ] >= 10 hard stop (BLOCKED)
- [ ] 0 expected_gate_decision = pass

## Step 8: Fake Green Check
- [ ] No memory entry verified without evidence
- [ ] No stale_risk omitted or defaulted to low
- [ ] No conflict_check omitted
- [ ] No TTL omitted for path-dependent memory

## Step 9: Human Gate Check
- [ ] Memory write operations: all forbidden (no human gate bypass)
- [ ] MemoryUpdateRecord: all status=proposed (not approved)

## Step 10: Gate Decision Tree

```
Was any memory file written?                       -> YES = BLOCKED
Was C:\Users\RD written?                            -> YES = BLOCKED
Was agent-state.db written?                         -> YES = BLOCKED
Was MEMORY.md modified?                             -> YES = BLOCKED
Was memory used as current fact?                    -> YES = needs_revision
Was stale memory trusted without re-verification?   -> YES = needs_revision
Was used_as_fact not false?                         -> YES = needs_revision
Was write_allowed not false?                        -> YES = needs_revision
Was stale_risk missing?                            -> YES = needs_revision
Are negative tests < 20?                            -> YES = needs_revision
All pass?                                            -> pass_to_review
```

## Decision: [ ] pass_to_review / [ ] needs_revision / [ ] blocked / [ ] human_required
