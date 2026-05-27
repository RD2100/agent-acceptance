# Blackboard Snapshot Template -- R1

> Batch R1-B, 2026-05-27
> RD2100 Agent Runtime v2
> Resource: res-blackboard-mcp-001
> Status: template -- defines the Snapshot record format for R1 evidence collection

## Snapshot Record Format

A snapshot is a READ-ONLY point-in-time capture of Blackboard state. It must NOT mutate anything. It serves as evidence for the R1 exit gate.

### Required Fields

| Field | Type | Description |
|-------|------|-------------|
| snapshot_id | string | Unique ID (e.g., `BB-SNAP-20260527-001`) |
| captured_at | ISO8601 | When snapshot was taken |
| captured_by | string | Agent or human who captured |
| phase | string | `"R1"` |
| resource_refs | array[string] | Referenced resource IDs from registry (min: `["res-blackboard-mcp-001"]`) |
| state_file_status | enum | `present` / `not_found` / `locked` / `unreadable` |
| state_file_checksum | string | SHA256 if readable; otherwise `"unavailable"` |
| events_log_status | enum | `present` / `not_found` / `empty` / `readable` |
| events_log_summary | string | High-level summary only (last N entries topic, NOT full content) |
| knowledge_status | enum | `present` / `not_found` / `empty` / `readable` |
| knowledge_summary | string | Topic summary only (NOT full knowledge content) |
| handover_status | enum | `present` / `not_found` |
| mcp_status | string | MUST be `"disabled"` |
| mutating_tools_invoked | boolean | MUST be `false` |
| state_mutated | boolean | MUST be `false` |
| events_appended | boolean | MUST be `false` |
| knowledge_written | boolean | MUST be `false` |
| bb_tools_called | array[string] | List of read-only bb_* tools actually called during snapshot |
| summary | string | Human-readable summary of snapshot contents |
| verification_gaps | array[string] | What couldn't be verified |
| reviewer_approved | boolean | `false` until reviewer signs off |
| next_phase_blocked | boolean | `true` (R2 blocked until reviewer approves snapshot) |

### Minimal JSON Example

```json
{
  "snapshot_id": "BB-SNAP-20260527-001",
  "captured_at": "2026-05-27T12:00:00Z",
  "captured_by": "R1-B Agent",
  "phase": "R1",
  "resource_refs": ["res-blackboard-mcp-001"],
  "state_file_status": "present",
  "state_file_checksum": "a1b2c3d4e5f6...",
  "events_log_status": "readable",
  "events_log_summary": "Last 10 entries: session registrations, decisions shared, bug patterns reported",
  "knowledge_status": "readable",
  "knowledge_summary": "Topics: known bug patterns, session registrations, past decisions",
  "handover_status": "present",
  "mcp_status": "disabled",
  "mutating_tools_invoked": false,
  "state_mutated": false,
  "events_appended": false,
  "knowledge_written": false,
  "bb_tools_called": [],
  "summary": "R1-DESIGN only; no bb_* tools called; tool availability deferred to R1-SNAPSHOT after separate human gate. MCP remains disabled.",
  "verification_gaps": [
    "bb_* tool availability not verified because MCP remains disabled in R1-DESIGN",
    "bb_event tool not confirmed active (listed as unconfirmed in resource registry)",
    "knowledge.md content not exhaustively audited"
  ],
  "reviewer_approved": false,
  "next_phase_blocked": true
}
```

### Field Validation Rules

- `snapshot_id` must match pattern `BB-SNAP-YYYYMMDD-NNN`
- `captured_at` must be valid ISO8601
- `phase` must be exactly `"R1"`
- `state_file_status` must be one of: `present`, `not_found`, `locked`, `unreadable`
- `events_log_status` must be one of: `present`, `not_found`, `empty`, `readable`
- `knowledge_status` must be one of: `present`, `not_found`, `empty`, `readable`
- `handover_status` must be one of: `present`, `not_found`
- `mcp_status` must be exactly `"disabled"`
- `mutating_tools_invoked` must be exactly `false`
- `state_mutated` must be exactly `false`
- `events_appended` must be exactly `false`
- `knowledge_written` must be exactly `false`
- `bb_tools_called` must only contain tools from the permitted list (11 tools in blackboard-readonly-policy.md)
- `next_phase_blocked` must be `true` until `reviewer_approved` becomes `true`
- `reviewer_approved` must be `false` on initial capture; only reviewer sets to `true`

---

## Snapshot Protocol

The following protocol governs how snapshots are captured, verified, and archived in R1.

### Step 1: Agent Requests Snapshot Authorization

The agent informs the reviewer that a Blackboard snapshot is needed as R1 evidence. The request includes:
- Which resource is being snapshotted (`res-blackboard-mcp-001`)
- Which read-only bb_* tools will be called
- Confirmation that no mutating tools will be invoked

### Step 2: Reviewer Approves the Snapshot Request

The reviewer explicitly authorizes the snapshot capture. This approval is authorization to read and inspect Blackboard state -- NOT authorization to register MCP, execute the server, or mutate anything.

### Step 3: Agent Captures Snapshot

**R1-DESIGN note**: This step is FUTURE REFERENCE ONLY. In R1-DESIGN, NO bb_* tools are called. The tools below are candidates for R1-SNAPSHOT after separate human gate approval.

When R1-SNAPSHOT is authorized, the agent would use ONLY these read-only bb_* tools:

| Tool | Purpose |
|------|---------|
| `bb_status` | Read current Blackboard state |
| `bb_get_recent_knowledge` | Read recent knowledge entries (summary only) |
| `bb_search_knowledge` | Search for specific topics |
| `bb_session_files` | List session files |
| `bb_check_conflicts` | Check file conflict status |
| `bb_validate_knowledge` | Validate existing entries (read-only) |

**R1-DESIGN: NONE of these tools are called. bb_tools_called must be an empty array.**

**When reading files (state.json, events.log, knowledge.md):**
- Read only enough to determine status and compute checksum
- Summarize events.log (topics only, NOT full content)
- Summarize knowledge.md (topics only, NOT full content)
- Compute SHA256 checksum of state.json if readable

### Step 4: Agent Records Snapshot Fields

Agent fills the Snapshot Record with observed values. All mutating_* fields must be `false`. All forbidden tools must be absent from `bb_tools_called`.

### Step 5: Agent Submits Snapshot for Reviewer Verification

Agent presents the completed snapshot to the reviewer. The reviewer checks:
- All mandatory fields are filled
- `mutating_tools_invoked` is `false`
- `state_mutated` is `false`
- `events_appended` is `false`
- `knowledge_written` is `false`
- `mcp_status` is `"disabled"`
- `bb_tools_called` contains only permitted tools
- No forbidden actions occurred

### Step 6: Reviewer Approves or Rejects

- **Approved**: `reviewer_approved` set to `true`. Snapshot becomes valid R1 evidence.
- **Rejected**: Specific issues documented in `verification_gaps`. Agent must re-capture or correct.

### Step 7: Snapshot Is Archived as Evidence

The approved snapshot is stored as an R1 evidence artifact. It serves as input to the R1 exit gate but does NOT itself enable R2. R2 entry requires a separate gate check where the reviewer evaluates all R1 evidence (snapshots, tool verification, contract mapping).

---

## What a Snapshot Is NOT

To prevent scope creep and misunderstanding, the following are explicitly stated:

| A Snapshot Is NOT... | Explanation |
|----------------------|-------------|
| **A state mutation** | No write, append, or modify operation occurs during snapshot capture. All mutating flags are `false`. |
| **An event append** | No entry is written to events.log. The snapshot reads existing entries only. |
| **A knowledge write** | No knowledge is solidified or published. The snapshot reads existing knowledge summaries only. |
| **MCP registration** | The snapshot does not register, configure, or modify the MCP server. MCP status remains `"disabled"`. |
| **Server execution** | `server.py` is not executed. R1-DESIGN: no bb_* tools called. R1-SNAPSHOT (future, after separate human gate): uses pre-existing MCP channel only; no new MCP registration. |
| **A GateResult** | The snapshot is evidence FOR a gate check, not the gate itself. A separate GateResult (Contract 4) is required to evaluate whether the snapshot meets gate criteria. |
| **Authorization for R2** | An approved snapshot is necessary but not sufficient for R2 entry. R2 requires the full R1 exit gate (see blackboard-readonly-policy.md, "R1 Exit Gate" section). |
| **A knowledge consolidation** | `bb_solidify_knowledge` is NOT called. Knowledge stays as-is. |
| **A build lock acquisition** | `bb_acquire_build_lock` is NOT called. No critical sections are entered. |
| **A file claim** | `bb_claim_file` is NOT called. No files are locked. |

---

## Relationship to R1 Exit Gate

This snapshot template supports the R1 exit gate defined in `blackboard-readonly-policy.md`. Specifically, it provides evidence for:

1. **Evidence collected**: Snapshot records state.json existence and checksum (R1 exit gate item 1)
2. **Tool availability (R1-SNAPSHOT only)**: `bb_tools_called` lists which candidate read-only tools responded after separate human gate. R1-DESIGN does not collect this evidence.
3. **Tool policy compliance**: Absence of forbidden tools in `bb_tools_called` confirms no policy violation (R1 exit gate item 3)
4. **No violations**: All mutating flags `false` confirm no forbidden actions occurred (R1 exit gate item 4)

The snapshot does NOT itself satisfy the R1 exit gate. It is one piece of evidence that the reviewer evaluates. The full exit gate also requires R1-DESIGN completion (all 6 documents created + reviewed), R1-SNAPSHOT authorization (separate human gate), and contract mapping A3 verification. Tool availability evidence is R1-SNAPSHOT only — NOT required in R1-DESIGN.

---

## R1 Invariants Preserved

The snapshot capture process preserves the following invariants from `runtime-invariants.md`:

- **I-READONLY**: Agent operates in read-only mode. No write, append, execute, or modify actions.
- **I-HUMAN-GATE**: All phase transitions require explicit human reviewer approval.
- **I-EVIDENCE-FIRST**: Evidence is collected before any transition. No evidence, no gate pass.
- **I-NO-MUTATION**: Zero state mutation during snapshot capture. All mutating flags remain `false`.
- **I-TRACEABLE**: In R1-SNAPSHOT (future), every bb_* call is recorded in `bb_tools_called`. In R1-DESIGN, `bb_tools_called` is empty — no tools are called, so nothing to trace.
