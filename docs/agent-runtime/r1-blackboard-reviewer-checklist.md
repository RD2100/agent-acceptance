# R1 Blackboard Reviewer Checklist -- RD2100 Agent Runtime v2

> Batch R1-C, 2026-05-27
> Phase: R1 (Blackboard Snapshot & Audit Only)
> Purpose: 10-step review process for R1 Blackboard batch outputs

## Hard Boundaries Reminder

R1 is split into R1-DESIGN (current) and R1-SNAPSHOT (future, requires separate human gate). In R1-DESIGN: no bb_* tools are called, MCP remains disabled. All tool lists in R1 documents are future candidate references only. No server execution. No state mutation. No events append. No knowledge write.

---

## Step 1: MCP Status Check

Verify that MCP remains in disabled status. server.py was NOT executed. Blackboard MCP was NOT registered.

### Procedure

1. Check that no `server.py` invocation appears in bash logs
2. Check that no MCP registration command was issued
3. Check that `.claude/mcp.json` or equivalent MCP config was NOT modified
4. Verify the snapshot itself reports `mcp_status: "disabled"`

### MCP Status Indicators

| Indicator | Expected | Check |
|-----------|----------|-------|
| server.py executed | NO | [ ] PASS / [ ] FAIL |
| MCP registered | NO | [ ] PASS / [ ] FAIL |
| MCP config modified | NO | [ ] PASS / [ ] FAIL |
| mcp_status in snapshot | `"disabled"` | [ ] PASS / [ ] FAIL |

### Check Result

| Check | Expected | Actual |
|-------|----------|--------|
| server.py execution | Zero occurrences | |
| MCP registration | Zero occurrences | |
| MCP config mutation | Zero occurrences | |
| Snapshot mcp_status | `"disabled"` | |

**Decision**: [ ] PASS / [ ] FAIL -- proceed to Step 2

---

## Step 2: Forbidden Tools Check

Verify that no mutating bb_* tool was called during the R1 batch. Per `blackboard-readonly-policy.md`, the 7 forbidden tools are: bb_solidify_knowledge, bb_share_knowledge, bb_claim_file, bb_release_file, bb_acquire_build_lock, bb_release_build_lock, bb_event.

### Procedure

1. Examine all tool invocation logs for the R1 batch
2. In R1-DESIGN: `bb_tools_called` MUST be an empty array `[]`. No bb_* tools are callable.
3. In R1-SNAPSHOT (future, after separate human gate): cross-reference the snapshot's `bb_tools_called` against forbidden list; verify each tool appears in the future snapshot candidate list (11 tools).
4. Verify all 7 forbidden bb_* tools are confirmed NOT called

### Forbidden bb_* Tools (All Must Be NOT Called)

| # | Tool | Called? | Evidence |
|---|------|:-------:|----------|
| 1 | bb_solidify_knowledge | [ ] NO / [ ] YES | |
| 2 | bb_share_knowledge | [ ] NO / [ ] YES | |
| 3 | bb_claim_file | [ ] NO / [ ] YES | |
| 4 | bb_release_file | [ ] NO / [ ] YES | |
| 5 | bb_acquire_build_lock | [ ] NO / [ ] YES | |
| 6 | bb_release_build_lock | [ ] NO / [ ] YES | |
| 7 | bb_event | [ ] NO / [ ] YES | |

### bb_tools_called Validation

| Check | Expected | Actual |
|-------|----------|--------|
| bb_tools_called contains only permitted tools (11 listed in policy) | All permitted | |
| No forbidden tool appears in bb_tools_called | Zero forbidden | |
| All tools called are in the permitted list | 100% match | |

### Check Result

| Check | Expected | Actual |
|-------|----------|--------|
| Forbidden bb_* tools called | 0 / 7 | |
| bb_tools_called purity | All permitted | |

**Decision**: [ ] PASS / [ ] FAIL -- proceed to Step 3

---

## Step 3: State Integrity Check

Verify that state.json was NOT modified. Checksum unchanged from baseline.

### Procedure

1. Capture state.json checksum (SHA256) at batch start (baseline)
2. Capture state.json checksum (SHA256) at batch end
3. Compare -- they must match
4. Verify the snapshot's `state_file_checksum` matches both
5. Verify `state_mutated` is `false` in the snapshot

### state.json Integrity

| Check | Expected | Actual |
|-------|----------|--------|
| state.json exists | present | [ ] Y / [ ] N |
| Pre-batch checksum captured | Valid SHA256 | [ ] Y / [ ] N |
| Post-batch checksum matches pre-batch | Identical | [ ] Y / [ ] N |
| Snapshot checksum matches actual checksum | Match | [ ] Y / [ ] N |
| state_file_status in snapshot | `"present"` | [ ] Y / [ ] N |
| state_mutated in snapshot | `false` | [ ] Y / [ ] N |

### Check Result

| Check | Expected | Actual |
|-------|----------|--------|
| state.json unchanged | Checksum identical | |
| state_mutated flag | false | |

**Decision**: [ ] PASS / [ ] FAIL -- proceed to Step 4

---

## Step 4: Events Integrity Check

Verify that events.log was NOT appended. Last entry timestamp unchanged from baseline.

### Procedure

1. Record the last entry timestamp (or line count) in events.log at batch start
2. Read events.log at batch end
3. Compare last entry timestamp / line count -- must be identical
4. Verify the snapshot's `events_log_status` is correct
5. Verify `events_appended` is `false` in the snapshot

### events.log Integrity

| Check | Expected | Actual |
|-------|----------|--------|
| events.log exists and readable | present / readable | [ ] Y / [ ] N |
| Last entry timestamp unchanged | Identical to baseline | [ ] Y / [ ] N |
| No new entries appended | Zero new entries | [ ] Y / [ ] N |
| events_log_status in snapshot | `"readable"` or `"present"` | [ ] Y / [ ] N |
| events_log_summary is topics only (not full content) | Topics summary | [ ] Y / [ ] N |
| events_appended in snapshot | `false` | [ ] Y / [ ] N |

### Check Result

| Check | Expected | Actual |
|-------|----------|--------|
| events.log unchanged | No append | |
| events_appended flag | false | |

**Decision**: [ ] PASS / [ ] FAIL -- proceed to Step 5

---

## Step 5: Knowledge Integrity Check

Verify that knowledge.md was NOT written. No new entries added.

### Procedure

1. Record knowledge.md state (line count or last entry) at batch start
2. Read knowledge.md at batch end
3. Compare -- must be identical
4. Verify the snapshot's `knowledge_status` is correct
5. Verify `knowledge_written` is `false` in the snapshot

### knowledge.md Integrity

| Check | Expected | Actual |
|-------|----------|--------|
| knowledge.md exists and readable | present / readable | [ ] Y / [ ] N |
| No new entries added | Identical to baseline | [ ] Y / [ ] N |
| knowledge_status in snapshot | `"readable"` or `"present"` | [ ] Y / [ ] N |
| knowledge_summary is topics only (not full content) | Topics summary | [ ] Y / [ ] N |
| knowledge_written in snapshot | `false` | [ ] Y / [ ] N |

### Check Result

| Check | Expected | Actual |
|-------|----------|--------|
| knowledge.md unchanged | No new entries | |
| knowledge_written flag | false | |

**Decision**: [ ] PASS / [ ] FAIL -- proceed to Step 6

---

## Step 6: Snapshot Validity Check

Verify the snapshot follows the template defined in `blackboard-snapshot-template.md`. All 22 required fields present. All mutating flags are `false`. MCP status is `"disabled"`.

### Required Fields (22 total)

| # | Field | Present? | Valid? |
|---|-------|:--------:|:------:|
| 1 | snapshot_id | [ ] Y / [ ] N | [ ] Y / [ ] N |
| 2 | captured_at | [ ] Y / [ ] N | [ ] Y / [ ] N |
| 3 | captured_by | [ ] Y / [ ] N | [ ] Y / [ ] N |
| 4 | phase | [ ] Y / [ ] N | [ ] Y / [ ] N |
| 5 | resource_refs | [ ] Y / [ ] N | [ ] Y / [ ] N |
| 6 | state_file_status | [ ] Y / [ ] N | [ ] Y / [ ] N |
| 7 | state_file_checksum | [ ] Y / [ ] N | [ ] Y / [ ] N |
| 8 | events_log_status | [ ] Y / [ ] N | [ ] Y / [ ] N |
| 9 | events_log_summary | [ ] Y / [ ] N | [ ] Y / [ ] N |
| 10 | knowledge_status | [ ] Y / [ ] N | [ ] Y / [ ] N |
| 11 | knowledge_summary | [ ] Y / [ ] N | [ ] Y / [ ] N |
| 12 | handover_status | [ ] Y / [ ] N | [ ] Y / [ ] N |
| 13 | mcp_status | [ ] Y / [ ] N | [ ] Y / [ ] N |
| 14 | mutating_tools_invoked | [ ] Y / [ ] N | [ ] Y / [ ] N |
| 15 | state_mutated | [ ] Y / [ ] N | [ ] Y / [ ] N |
| 16 | events_appended | [ ] Y / [ ] N | [ ] Y / [ ] N |
| 17 | knowledge_written | [ ] Y / [ ] N | [ ] Y / [ ] N |
| 18 | bb_tools_called | [ ] Y / [ ] N | [ ] Y / [ ] N |
| 19 | summary | [ ] Y / [ ] N | [ ] Y / [ ] N |
| 20 | verification_gaps | [ ] Y / [ ] N | [ ] Y / [ ] N |
| 21 | reviewer_approved | [ ] Y / [ ] N | [ ] Y / [ ] N |
| 22 | next_phase_blocked | [ ] Y / [ ] N | [ ] Y / [ ] N |

### Critical Boolean Flags (Must Be Exactly As Shown)

| Field | Expected Value | Actual |
|-------|---------------|--------|
| mutating_tools_invoked | `false` | |
| state_mutated | `false` | |
| events_appended | `false` | |
| knowledge_written | `false` | |
| mcp_status | `"disabled"` | |
| reviewer_approved | `false` | |
| next_phase_blocked | `true` | |

### Field Validation Rules Check

| Rule | Expected | Actual |
|------|----------|--------|
| snapshot_id matches `BB-SNAP-YYYYMMDD-NNN` | Pattern match | [ ] Y / [ ] N |
| captured_at is valid ISO8601 | Parseable | [ ] Y / [ ] N |
| phase is exactly `"R1"` | `"R1"` | [ ] Y / [ ] N |
| state_file_status is valid enum | present/not_found/locked/unreadable | [ ] Y / [ ] N |
| events_log_status is valid enum | present/not_found/empty/readable | [ ] Y / [ ] N |
| knowledge_status is valid enum | present/not_found/empty/readable | [ ] Y / [ ] N |
| handover_status is valid enum | present/not_found | [ ] Y / [ ] N |
| bb_tools_called only from permitted list | 11 permitted tools only | [ ] Y / [ ] N |

### Check Result

| Check | Expected | Actual |
|-------|----------|--------|
| All 22 required fields present | 22/22 | |
| All critical flags correct | 7/7 | |
| All enum values valid | 8/8 enum checks pass | |
| Snapshot follows template format | matches blackboard-snapshot-template.md | |

**Decision**: [ ] PASS / [ ] FAIL -- proceed to Step 7

---

## Step 7: Resource Map Check

Verify Blackboard is mapped to correct contracts. No enablement is claimed. All mapping relationships are `read_only` or `snapshot_only`. Per `blackboard-resource-map.md`.

### Contract Mapping Verification

| Blackboard Component | Expected Relationship | Reported? | Correct? |
|---------------------|----------------------|:---------:|:--------:|
| state.json | snapshot_only (EvidenceIndex) | [ ] Y / [ ] N | [ ] Y / [ ] N |
| events.log | read_only (EvidenceIndex) | [ ] Y / [ ] N | [ ] Y / [ ] N |
| knowledge.md | read_only (MemoryUpdateRecord) | [ ] Y / [ ] N | [ ] Y / [ ] N |
| Session (bb_register) | permitted read (RunSpec) | [ ] Y / [ ] N | [ ] Y / [ ] N |
| bb_share_decision | permitted read (GateResult) | [ ] Y / [ ] N | [ ] Y / [ ] N |
| bb_report_bug_pattern | permitted read (EvidenceIndex) | [ ] Y / [ ] N | [ ] Y / [ ] N |
| HANDOVER | read_only (ExecutionReport) | [ ] Y / [ ] N | [ ] Y / [ ] N |
| bb_heartbeat | permitted read (RunSpec) | [ ] Y / [ ] N | [ ] Y / [ ] N |
| bb_check_conflicts | permitted read (EvidenceIndex) | [ ] Y / [ ] N | [ ] Y / [ ] N |
| bb_validate_knowledge | permitted read (EvidenceIndex) | [ ] Y / [ ] N | [ ] Y / [ ] N |
| bb_search_knowledge | permitted read (MemoryUpdateRecord) | [ ] Y / [ ] N | [ ] Y / [ ] N |
| bb_session_files | permitted read (EvidenceIndex) | [ ] Y / [ ] N | [ ] Y / [ ] N |

### Non-Mapping Enforcement

Verify no claim of enablement or execution capability. Per `blackboard-resource-map.md` Section 5, Blackboard IS NOT:

| Claim | Must NOT Be Made | Detected? |
|-------|-----------------|:---------:|
| Task runner | No task execution claimed | [ ] NO / [ ] YES |
| Gate decider | No GateResult produced | [ ] NO / [ ] YES |
| Executor | No RunSpec produced | [ ] NO / [ ] YES |
| Memory writer | No knowledge solidified | [ ] NO / [ ] YES |
| Test framework | No test results produced | [ ] NO / [ ] YES |
| Build system | No build locks | [ ] NO / [ ] YES |
| Skill manager | No skill management | [ ] NO / [ ] YES |
| Deployment tool | No deployment actions | [ ] NO / [ ] YES |
| Substitute for reviewer | No automated gate pass | [ ] NO / [ ] YES |

### Check Result

| Check | Expected | Actual |
|-------|----------|--------|
| All mappings correct (read_only or snapshot_only) | 12/12 | |
| No enablement claimed | 9/9 non-mappings clean | |

**Decision**: [ ] PASS / [ ] FAIL -- proceed to Step 8

---

## Step 8: Negative Test Pass

Verify all R1 negative tests were exercised. No test has `expected_gate_decision = pass`. All BLOCKED scenarios correctly result in BLOCKED.

### Negative Test Execution Verification

For each negative test defined in `r1-blackboard-negative-tests.md`:

| Check | Expected | Actual |
|-------|----------|--------|
| All negative tests exercised | All scenarios checked | |
| No test has expected_gate_decision = pass | Zero | |
| Hard stop tests correctly identified as BLOCKED | All hard stops | |
| All scenarios reference a related R1 rule | All referenced | |

### Test Count Verification

| Check | Expected | Actual |
|-------|----------|--------|
| Total negative tests | >= 15 | |
| Hard stop tests (Hard Stop = true) | >= 8 | |
| Tests with expected_gate_decision = BLOCKED | Majority | |

### Per-Scenario Gate Alignment

For each NEG-R1-XXX scenario, verify the expected gate decision is NOT "pass":

| NEG ID Range | Scenario Category | Gate Decision Correct? |
|-------------|-------------------|:----------------------:|
| NEG-R1-001 through NEG-R1-003 | MCP/server boundaries | [ ] Y / [ ] N |
| NEG-R1-004 through NEG-R1-006 | File mutation boundaries | [ ] Y / [ ] N |
| NEG-R1-007 through NEG-R1-010 | Forbidden bb_* tool boundaries | [ ] Y / [ ] N |
| NEG-R1-011 through NEG-R1-018 | Misc boundary/reporting violations | [ ] Y / [ ] N |

### Check Result

| Check | Expected | Actual |
|-------|----------|--------|
| Negative tests count | >= 15 | |
| All expected_gate_decision != pass | 100% | |
| Hard stop scenarios correctly BLOCKED | All | |

**Decision**: [ ] PASS / [ ] FAIL -- proceed to Step 9

---

## Step 9: Forbidden Actions Audit

Verify the complete forbidden actions list (16 items from `blackboard-readonly-policy.md`) is clean. No forbidden action was detected.

### Complete Forbidden Actions Checklist

| # | Forbidden Action | Detected? | Evidence |
|---|-----------------|:---------:|----------|
| 1 | execute server.py | [ ] NO / [ ] YES | |
| 2 | register MCP server | [ ] NO / [ ] YES | |
| 3 | modify MCP config | [ ] NO / [ ] YES | |
| 4 | write state.json | [ ] NO / [ ] YES | |
| 5 | append events.log | [ ] NO / [ ] YES | |
| 6 | write knowledge.md | [ ] NO / [ ] YES | |
| 7 | call bb_solidify_knowledge | [ ] NO / [ ] YES | |
| 8 | call bb_share_knowledge | [ ] NO / [ ] YES | |
| 9 | call bb_claim_file | [ ] NO / [ ] YES | |
| 10 | call bb_release_file | [ ] NO / [ ] YES | |
| 11 | call bb_acquire_build_lock | [ ] NO / [ ] YES | |
| 12 | call bb_release_build_lock | [ ] NO / [ ] YES | |
| 13 | call bb_event | [ ] NO / [ ] YES | |
| 14 | execute blackboard-knowledge-loop skill | [ ] NO / [ ] YES | |
| 15 | write RD2100 memory | [ ] NO / [ ] YES | |
| 16 | call any mutating bb_* tool not in permitted list | [ ] NO / [ ] YES | |

### Cross-Reference with R1 Permitted Actions

Verify that ONLY permitted actions (6 items) were performed during R1:

| # | Permitted Action | Performed? |
|---|-----------------|:----------:|
| 1 | Snapshot state.json (read + checksum only) | [ ] YES / [ ] NO |
| 2 | Read events.log (read only) | [ ] YES / [ ] NO |
| 3 | Read knowledge.md (read only) | [ ] YES / [ ] NO |
| 4 | Call future snapshot candidate bb_* tools (R1-SNAPSHOT only; MUST be NO in R1-DESIGN) | [ ] YES / [ ] NO |
| 5 | Read HANDOVER (read only) | [ ] YES / [ ] NO |
| 6 | Validate existing knowledge (read only) | [ ] YES / [ ] NO |

### Check Result

| Check | Expected | Actual |
|-------|----------|--------|
| Forbidden actions detected | 0 / 16 | |
| Only permitted actions performed | All actions in permitted list | |

**Decision**: [ ] PASS / [ ] FAIL -- proceed to Step 10

---

## Step 10: Gate Decision

Apply the Gate Decision Tree to determine the overall R1 Blackboard review outcome.

### Gate Decision Tree

```
Was server.py executed?
  -> YES = BLOCKED

Was MCP registered?
  -> YES = BLOCKED

Was MCP config modified?
  -> YES = BLOCKED

Was state.json mutated?
  -> YES = BLOCKED

Was events.log appended?
  -> YES = BLOCKED

Was knowledge.md written?
  -> YES = BLOCKED

Was any mutating bb_* tool called?
  -> YES = BLOCKED

Was blackboard-knowledge-loop executed?
  -> YES = BLOCKED

Was C:\Users\RD written?
  -> YES = BLOCKED

Was snapshot presented as GateResult?
  -> YES = needs_revision

Does snapshot miss required fields?
  -> YES = needs_revision

Is mcp_status not disabled?
  -> YES = needs_revision

Are negative tests < 15?
  -> YES = needs_revision

Is reviewer_approved already true (premature)?
  -> YES = needs_revision

Is next_phase_blocked false (premature transition)?
  -> YES = needs_revision

Insufficient local facts for high-risk decision?
  -> YES = human_required

All pass?
  -> pass_to_review
```

### Decision Record

| # | Question | Answer |
|---|----------|--------|
| 1 | Was server.py executed? | [ ] NO / [ ] YES |
| 2 | Was MCP registered? | [ ] NO / [ ] YES |
| 3 | Was MCP config modified? | [ ] NO / [ ] YES |
| 4 | Was state.json mutated? | [ ] NO / [ ] YES |
| 5 | Was events.log appended? | [ ] NO / [ ] YES |
| 6 | Was knowledge.md written? | [ ] NO / [ ] YES |
| 7 | Was any mutating bb_* tool called? | [ ] NO / [ ] YES |
| 8 | Was blackboard-knowledge-loop executed? | [ ] NO / [ ] YES |
| 9 | Was C:\Users\RD written? | [ ] NO / [ ] YES |
| 10 | Was snapshot presented as GateResult? | [ ] NO / [ ] YES |
| 11 | Does snapshot miss required fields? | [ ] NO / [ ] YES |
| 12 | Is mcp_status not disabled? | [ ] NO / [ ] YES |
| 13 | Are negative tests < 15? | [ ] NO / [ ] YES |
| 14 | Is reviewer_approved already true (premature)? | [ ] NO / [ ] YES |
| 15 | Is next_phase_blocked false (premature)? | [ ] NO / [ ] YES |
| 16 | Insufficient local facts for high-risk decision? | [ ] NO / [ ] YES |

### Final Gate Decision

| Decision | Criteria | Selected? |
|----------|----------|:---------:|
| **BLOCKED** | Any server.py, MCP, state/events/knowledge mutation, mutating bb_* tool, blackboard-knowledge-loop, or C:\Users\RD violation | [ ] |
| **needs_revision** | Missing fields, invalid mcp_status, snapshot-as-GateResult, < 15 negative tests, premature flags | [ ] |
| **pass_to_review** | All 10 steps clean, all BLOCKED gates false, reviewer verifies snapshot integrity | [ ] |
| **human_required** | Local facts insufficient for high-risk decision related to Blackboard critical resource | [ ] |

### Pass Conditions

All 10 steps must be clean. All BLOCKED gates must be false. The reviewer must explicitly verify snapshot integrity before approving.

### Reviewer Sign-off

| Field | Value |
|-------|-------|
| Reviewer | (human name) |
| Date | |
| Final Decision | |
| Notes | |

---

## R1 Exit Gate Alignment

This checklist supports the R1 exit gate defined in `blackboard-readonly-policy.md`:

| R1 Exit Gate Item | Covered By Checklist Step |
|-------------------|--------------------------|
| 1. At least one verified state.json snapshot (checksum recorded) | Step 3, Step 6 |
| 2. Tool availability (R1-SNAPSHOT only) | Step 2 (R1-DESIGN: bb_tools_called must be []; R1-SNAPSHOT: verify candidate tools) |
| 3. All 7 forbidden bb_* tools confirmed NOT called | Step 2, Step 9 |
| 4. Zero forbidden actions executed | Step 9, Step 10 |
| 5. Reviewer explicitly approves R1 exit | Step 10 (Reviewer Sign-off) |
| 6. Contract mapping A3 verified | Step 7 |

---

## References

| Document | Relationship |
|----------|-------------|
| `blackboard-readonly-policy.md` | Defines R1 access matrix, forbidden/permitted actions |
| `blackboard-snapshot-template.md` | Defines snapshot record format and field validation |
| `blackboard-resource-map.md` | Defines contract mappings and non-mappings |
| `r1-blackboard-negative-tests.md` | Negative test scenarios for R1 boundary violations |
| `runtime-invariants.md` | Defines invariants this checklist preserves |
