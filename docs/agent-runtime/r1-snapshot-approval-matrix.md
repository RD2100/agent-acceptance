# R1-SNAPSHOT Approval Matrix

> Batch R1-SNAP-DESIGN, 2026-05-27
> RD2100 Agent Runtime v2
> Phase: R1-DESIGN (snapshot authorization package design only)

## Purpose

This matrix records the human reviewer decision to **authorize or deny** the R1 read-only Blackboard snapshot. **No bb_* tools are called until approved.** The snapshot capture itself is deferred to R1-SNAPSHOT, which activates only after the reviewer signs this matrix.

All tool lists in this document are candidate references. No bb_* tool has been called during R1-DESIGN. MCP remains disabled.

---

## Decision Summary

| Request | Current Phase | Requested Action | Risk | Recommends | Human Decision | Signature |
|---------|:---:|---|:---:|---|---|---|
| R1-SNAP-REQ-20260527 | R1-DESIGN | authorize_readonly_snapshot | medium | recommend_approve | [ ] approve / [ ] reject | |

---

## Preconditions

All preconditions must be true **before** the reviewer approves the snapshot request.

| # | Precondition | Status |
|---|-------------|--------|
| 1 | R1-DESIGN `pass_to_review` (COMPLETED 2026-05-27) | [ ] confirmed |
| 2 | All 6 R1-DESIGN documents exist | [ ] confirmed |
| 3 | `blackboard-resource-record.schema.json` valid | [ ] confirmed |
| 4 | MCP confirmed disabled (no registration, no server.py execution) | [ ] confirmed |
| 5 | No mutating bb_* tools called during R1-DESIGN | [ ] confirmed |

### R1-DESIGN Document Checklist

Verify all 6 R1-DESIGN documents are present before approving:

| # | Document | Path | Exists? |
|---|----------|------|:--------:|
| 1 | Blackboard Read-only Policy | `docs/agent-runtime/blackboard-readonly-policy.md` | [ ] Y |
| 2 | Blackboard Snapshot Template | `docs/agent-runtime/blackboard-snapshot-template.md` | [ ] Y |
| 3 | R1 Blackboard Reviewer Checklist | `docs/agent-runtime/r1-blackboard-reviewer-checklist.md` | [ ] Y |
| 4 | Blackboard Resource Record Schema | `schemas/resource-integration/blackboard-resource-record.schema.json` | [ ] Y |
| 5 | Blackboard Resource Map | `docs/agent-runtime/blackboard-resource-map.md` | [ ] Y |
| 6 | R1 Blackboard Negative Tests | `docs/agent-runtime/r1-blackboard-negative-tests.md` | [ ] Y |

---

## What Approval Authorizes

Approval authorizes **ONLY** the following 6 read-only bb_* tools to be called during R1-SNAPSHOT:

| # | Tool | Purpose | Constraint |
|---|------|---------|------------|
| 1 | `bb_status` | Read current Blackboard state | Display response; do not interpret as gate signal |
| 2 | `bb_get_recent_knowledge` | Read recent knowledge entries (48h window) | Record topic summary only; do NOT read full content |
| 3 | `bb_search_knowledge` | Search for specific topics | Read-only search; no write |
| 4 | `bb_session_files` | List session files | Record file list; do not modify |
| 5 | `bb_check_conflicts` | Check file conflict status | Read conflict status; no lock/resolve |
| 6 | `bb_validate_knowledge` | Validate existing knowledge entries | Read-only validation; no consolidation |

These tools are called through the **pre-existing MCP channel only**. No new MCP registration occurs.

---

## What Approval Does NOT Authorize

Approval does **NOT** authorize any of the following:

| # | Forbidden Action | Reason |
|---|-----------------|--------|
| 1 | Server execution (`server.py`) | R1 boundary: server execution is forbidden |
| 2 | MCP registration | R1 boundary: MCP registration is forbidden |
| 3 | MCP config modification | R1 boundary: config mutation is forbidden |
| 4 | State mutation (`state.json` write) | R1 boundary: snapshot_only access |
| 5 | Events append (`events.log` write) | R1 boundary: read_only access |
| 6 | Knowledge write (`knowledge.md` write) | R1 boundary: read_only access |
| 7 | `bb_solidify_knowledge` | Mutating tool -- forbidden in R1 |
| 8 | `bb_share_knowledge` | Mutating tool -- forbidden in R1 |
| 9 | `bb_claim_file` | File locking -- forbidden in R1 |
| 10 | `bb_release_file` | File locking -- forbidden in R1 |
| 11 | `bb_acquire_build_lock` | Critical section -- forbidden in R1 |
| 12 | `bb_release_build_lock` | Critical section -- forbidden in R1 |
| 13 | `bb_event` | Tool not confirmed active -- forbidden in R1 |
| 14 | R2 entry | R2 requires separate gate check with all R1 evidence |
| 15 | Any capability enablement | No execute/install/deploy capability is claimed |

---

## Reviewer Signature Block

By signing below, the reviewer explicitly acknowledges:

1. They have verified all 6 R1-DESIGN documents exist.
2. They have confirmed MCP is disabled.
3. They have confirmed zero mutating bb_* tools were called during R1-DESIGN.
4. They authorize ONLY the 6 read-only bb_* tools listed above.
5. They understand this does NOT authorize server execution, MCP registration, or state mutation.
6. They understand R2 entry requires a separate gate check after R1-SNAPSHOT completes.

| Field | Value |
|-------|-------|
| **Reviewer Name** | |
| **Date** | |
| **Decision** | [ ] approve / [ ] reject |
| **Comments** | |

---

## References

| Document | Relationship |
|----------|-------------|
| `r1-snapshot.request.json` | The SourceLockRequest JSON this matrix evaluates |
| `blackboard-readonly-policy.md` | Defines R1 access matrix and forbidden/permitted actions |
| `blackboard-snapshot-template.md` | Defines the 22-field snapshot record format |
| `r1-blackboard-reviewer-checklist.md` | 10-step reviewer verification procedure |
