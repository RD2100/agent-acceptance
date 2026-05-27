# Blackboard Resource Map -- R1

> Batch R1-B, 2026-05-27
> RD2100 Agent Runtime v2
> Resource: res-blackboard-mcp-001
> Status: resource map -- defines how Blackboard relates to Runtime v2 contracts WITHOUT enabling it

---

## 1. Blackboard to Runtime Contract Mapping

This section maps Blackboard components to the 8 core contracts defined in `integration-contracts.md`. All relationships are read-only or snapshot-only at R1. No Blackboard component enables any runtime capability.

| Blackboard Component | Runtime Contract | Relationship | Status |
|---------------------|------------------|--------------|--------|
| state.json | EvidenceIndex (Contract 3) | Blackboard state can be evidence for gate checks. The state.json checksum and status serve as an evidence artifact. | `snapshot_only` |
| events.log | EvidenceIndex (Contract 3) | Recent event entries can be referenced in execution reports. Events log topics feed into evidence summaries. | `read_only` |
| knowledge.md | MemoryUpdateRecord (Contract 8) | Knowledge entries are reference material. Agents may propose MemoryUpdateRecords based on knowledge.md content but must not write or solidify. | `read_only` |
| Session registration (bb_register) | RunSpec (Contract 2) | Session start maps to run lifecycle. Registration provides run_id context for the session. | `permitted (read)` |
| Decision logging (bb_share_decision) | GateResult (Contract 4) | Decisions feed into gate evidence. Each shared decision can be referenced as supporting evidence for a gate result. | `permitted (read)` |
| Bug patterns (bb_report_bug_pattern) | EvidenceIndex (Contract 3) | Bug reports are evidence artifacts. Reported bugs can be indexed as evidence for quality gates. | `permitted (read)` |
| HANDOVER | ExecutionReport (Contract 5) | Handover protocol informs report structure. HANDOVER content provides template context for execution reports. | `read_only` |
| Session heartbeat (bb_heartbeat) | RunSpec (Contract 2) | Heartbeat confirms session liveness and provides timing data for run lifecycle tracking. | `permitted (read)` |
| Conflict check (bb_check_conflicts) | EvidenceIndex (Contract 3) | Conflict status can be recorded as evidence of contention or isolation. | `permitted (read)` |
| Knowledge validation (bb_validate_knowledge) | EvidenceIndex (Contract 3) | Validation results confirm knowledge integrity. Can be recorded as evidence. | `permitted (read)` |
| Knowledge search (bb_search_knowledge) | MemoryUpdateRecord (Contract 8) | Search results inform proposed memory updates but do not write them. | `permitted (read)` |
| Session file list (bb_session_files) | EvidenceIndex (Contract 3) | File listing can serve as evidence of session artifacts. | `permitted (read)` |

### Key Principle

Every mapping above is `read_only` or `snapshot_only`. No Blackboard component is mapped as a producer of runtime contracts. Blackboard is a source of evidence, not an executor.

---

## 2. Blackboard in the Agent Lifecycle

Based on the operating model (`operating-model.md`) with R1 constraints from `blackboard-readonly-policy.md`.

### Session Start

| Action | Tool | R1 Status |
|--------|------|:---------:|
| Register session | `bb_register(name, task, session_id)` | PERMITTED |
| Get recent knowledge | `bb_get_recent_knowledge(48)` | PERMITTED |
| Check conflicts | `bb_check_conflicts` | PERMITTED |
| Read state | `bb_status` | PERMITTED |

### During Session

| Action | Tool | R1 Status |
|--------|------|:---------:|
| Log decisions | `bb_share_decision(...)` | PERMITTED |
| Report bug patterns | `bb_report_bug_pattern(...)` | PERMITTED |
| Search knowledge | `bb_search_knowledge(...)` | PERMITTED |
| Validate knowledge | `bb_validate_knowledge(...)` | PERMITTED |
| List session files | `bb_session_files` | PERMITTED |
| Heartbeat | `bb_heartbeat` | PERMITTED |
| **Solidify knowledge** | `bb_solidify_knowledge` | **FORBIDDEN** |
| **Share knowledge** | `bb_share_knowledge` | **FORBIDDEN** |
| **Claim file** | `bb_claim_file` | **FORBIDDEN** |
| **Release file** | `bb_release_file` | **FORBIDDEN** |
| **Acquire build lock** | `bb_acquire_build_lock` | **FORBIDDEN** |
| **Release build lock** | `bb_release_build_lock` | **FORBIDDEN** |
| **Fire event** | `bb_event` | **FORBIDDEN** |

### Session End

| Action | Tool | R1 Status |
|--------|------|:---------:|
| Deregister session | `bb_deregister` | PERMITTED |
| **Write knowledge** | `bb_solidify_knowledge` | **FORBIDDEN** |
| **Publish knowledge** | `bb_share_knowledge` | **FORBIDDEN** |

### R1 Constraint Summary

```
R1 CONSTRAINT: NO bb_solidify_knowledge, NO bb_share_knowledge
R1 CONSTRAINT: NO file locking (bb_claim_file, bb_release_file)
R1 CONSTRAINT: NO build locks (bb_acquire_build_lock, bb_release_build_lock)
R1 CONSTRAINT: NO bb_event
R1 CONSTRAINT: NO server.py execution
R1 CONSTRAINT: NO MCP registration
```

---

## 3. Blackboard to Resource Registry Mapping

How Blackboard relates to the other 7 registered resources in `resource-registry.md`.

| Related Resource | Resource ID | Relationship | R1 Interaction |
|-----------------|-------------|--------------|:--------------:|
| dev-frame | res-devframe-002 | None directly. Blackboard does not interact with dev-frame. | NONE |
| test-frame | res-testframe-003 | Blackboard can record bug patterns discovered during test-frame inspection (future R2+). | NONE in R1 |
| CodeGraph | res-codegraph-004 | CodeGraph search results can be reported as bug patterns via bb_report_bug_pattern. | PERMITTED (read) |
| Local Skills | res-localskills-005 | Blackboard does not manage skills. Skills may reference Blackboard knowledge. | NONE in R1 |
| RD2100 Memory | res-rd2100memory-006 | Blackboard is Layer 3 of the memory architecture (see memory-architecture.md). Blackboard complements but does not replace file memory. R1 forbids writing to either. | READ ONLY |
| Claude Plans/Rules | res-clauderules-007 | Rules govern Blackboard access (blackboard-protocol.md, blackboard-readonly-policy.md). | READ ONLY |
| agent-acceptance Native | res-agentacceptance-008 | Blackboard is a registered resource within agent-acceptance. Native scripts do not call Blackboard in R1. | NONE in R1 |

### Cross-Resource Gate

Blackboard is the first resource promoted beyond R0 (registered status). Its R1 snapshot is a template for how other resources will be audited in their respective R-phases.

---

## 4. R1 Snapshot to R2 Evidence Path

What must happen before Blackboard snapshots can be used as R2 evidence.

### Current State (R1)

```
[R1 Snapshot]
  - snapshot_id: BB-SNAP-YYYYMMDD-NNN
  - reviewer_approved: false
  - next_phase_blocked: true
  - All mutating flags: false
  - mcp_status: "disabled"
```

### Required Transitions

| Step | Action | Who | Prerequisite |
|:----:|--------|-----|--------------|
| 1 | Snapshot captured per protocol | Agent | Reviewer authorization |
| 2 | All fields verified complete and accurate | Agent | Snapshot capture complete |
| 3 | Zero forbidden tools in bb_tools_called | Agent | Snapshot self-audit |
| 4 | Snapshot submitted for review | Agent | Steps 1-3 complete |
| 5 | Reviewer approves snapshot | Reviewer | Step 4 complete |
| 6 | `reviewer_approved` set to `true` | Reviewer | Step 5 complete |
| 7 | Snapshot archived as R1 evidence | Agent | Step 6 complete |
| 8 | **R1 exit gate evaluation** | Reviewer | ALL R1 evidence, not just snapshots |
| 9 | R2 entry authorized | Reviewer | R1 exit gate fully passed |

### What R2 Evidence Requires

An approved snapshot is necessary but not sufficient for R2. The full R1 exit gate requires:

1. At least one verified state.json snapshot (checksum recorded)
2. All 11 future snapshot candidate bb_* tools listed for review; callability NOT verified in R1-DESIGN (MCP disabled); verification deferred to R1-SNAPSHOT after separate human gate
3. All 7 forbidden bb_* tools confirmed NOT called
4. Zero forbidden actions executed
5. Reviewer explicitly approves R1 exit
6. Contract mapping A3 verified against actual tool behavior

### Integrity Check

Before R2, the following must be verified:

- [ ] Snapshot checksum matches current state.json (no drift since snapshot)
- [ ] `mutating_tools_invoked` remains `false`
- [ ] `state_mutated` remains `false`
- [ ] `events_appended` remains `false`
- [ ] `knowledge_written` remains `false`
- [ ] No forbidden bb_* tools appear in any session log since snapshot
- [ ] Reviewer signed off on this specific snapshot

---

## 5. Explicit Non-Mappings

What Blackboard is NOT mapped to. These non-mappings prevent scope creep and clarify the resource's role.

| Blackboard Is NOT... | Explanation | Why This Matters |
|---------------------|-------------|------------------|
| **A task runner** | Blackboard does not execute tasks, dispatch work, or run scripts. It has no TaskSpec producer role. | Prevents confusion with agent-acceptance Native (res-agentacceptance-008), which is the runtime executor. |
| **A gate decider** | Blackboard does not evaluate gates or produce GateResult records. It provides evidence that gates consume. | Gates are evaluated by agents and reviewers, not by Blackboard. Blackboard is a silent evidence store. |
| **An executor** | Blackboard has no RunSpec producer role. It does not run commands, execute tests, or produce output. | Prevents treating Blackboard as an automation engine. It is a collaboration layer, not an execution layer. |
| **A memory writer** | Blackboard does not solidify knowledge or publish new entries during R1. All write operations are forbidden. | Prevents accidental knowledge contamination. The memory freeze applies to Layer 3 as well as Layers 1-2. |
| **A test framework** | Blackboard does not run tests, validate outputs, or produce test results. Bug patterns are reports, not test results. | Prevents confusion with test-frame (res-testframe-003). Bug reports are qualitative, not quantitative. |
| **A build system** | Blackboard does not manage build locks or critical sections during R1. All lock tools are forbidden. | Prevents Blackboard from being used as a mutex. Build coordination is entirely out of scope for R1. |
| **A skill manager** | Blackboard does not install, evolve, or manage skills. It may reference skill-trigger-matrix.md but does not control it. | Prevents scope overlap with skill-intake and skill-evolution concerns. |
| **A deployment tool** | Blackboard does not deploy code, manage releases, or control promotion. It records decisions about these things. | Prevents operational misuse. Blackboard is evidence, not operations. |
| **A substitute for reviewer judgment** | Blackboard records and shares information. It does not make decisions or replace human gates. All gates require human sign-off. | Preserves the human-gate invariant (I-HUMAN-GATE). No automated gate pass via Blackboard. |

---

## R1 Invariants Preserved

This resource map preserves the following invariants from `runtime-invariants.md`:

- **I-REGISTER-ONLY**: Resources are registered and mapped, not enabled or configured.
- **I-READONLY**: All Blackboard contract mappings are read_only or snapshot_only.
- **I-HUMAN-GATE**: All transitions from snapshot to R2 evidence require reviewer approval.
- **I-EVIDENCE-FIRST**: Snapshots are collected before any transition. The evidence path is clearly defined.
- **I-NO-EXECUTION**: Blackboard is explicitly mapped as NOT a task runner, executor, or build system.
- **I-TRACEABLE**: Every Blackboard component is mapped to a specific contract with a clear status.

---

## References

| Document | Relationship |
|----------|-------------|
| `blackboard-readonly-policy.md` | Defines R1 access matrix and forbidden actions |
| `blackboard-snapshot-template.md` | Defines the snapshot record format used in evidence collection |
| `resource-registry.md` | Registers res-blackboard-mcp-001 and 7 other resources |
| `integration-contracts.md` | Defines the 8 core contracts this map references |
| `memory-architecture.md` | Defines Layer 3 (Blackboard) in the three-layer memory model |
| `operating-model.md` | Defines the agent lifecycle this map situates Blackboard within |
| `runtime-invariants.md` | Defines the invariants this map must not violate |
| `tool-policy.md` | Defines permitted and forbidden tools across phases |
