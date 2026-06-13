# Architecture Review: Multi-Agent Dispatch System (A1-R2)

> **Reviewer**: Architecture Reviewer Agent (A1, second pass)
> **Date**: 2026-06-13
> **Previous review**: 2026-06-09 (verdict: PASS, scope: dispatch plan scripts + governance handoff)
> **Current scope**: Full SADP dispatch boundaries, capability classifications, runtime scope declarations, interface contracts, dispatch plan schema, core rules, lessons learned
> **Verdict**: PARTIAL

---

## Executive Summary

This is a **broadened review** that expands beyond the previous A1 review (which focused on dispatch plan scripts and governance handoff). While the previous review found no P0/P1 issues in the dispatch planning architecture specifically, this review examines the **full protocol-to-schema contract chain** and identifies **2 P0 findings, 4 P1 findings, and 5 P2 findings** that represent architecture risks in the broader multi-agent system.

The most critical issues are: (1) dual-format interface contract drift between the markdown TaskSpec in the protocol and the JSON schema, and (2) protected file path inconsistencies between SADP declarations and actual filesystem layout.

**Previous review findings remain valid** for their specific scope (dispatch plan scripts, Gate 0 preflight, conflict detection). This review adds findings from the protocol document, capability inventory, core rules, and cross-document consistency.

---

## Files Reviewed

| File | Lines | Role |
|------|:-----:|------|
| `docs/agent-runtime/sub-agent-dispatch-protocol.md` | 1-715 | Primary dispatch protocol |
| `docs/agent-runtime/capability-inventory.md` | 1-777 | Capability registry |
| `.agent/CONVERSATION_BINDING.json` | 1-102 | Runtime scope declarations |
| `schemas/agent-runtime/task-spec.schema.json` | 1-258 | TaskSpec interface contract |
| `schemas/agent-runtime/multi-agent-dispatch-plan.schema.json` | 1-464 | Dispatch plan schema |
| `schemas/agent-runtime/execution-report.schema.json` | 1-150 | ExecutionReport contract |
| `AGENTS.md` | 1-195 | Runtime entry point |
| `rules/core.md` | 1-158 | Core rules (P0 hard stops) |
| `docs/agent-runtime/lessons-learned.md` | 1-207 | Operational lessons log |
| `docs/agent-runtime/dispatch-model-profiles.md` | 1-78 | Model dispatch limits |
| `docs/agent-runtime/integration-contracts.md` | 1-60 | Core data contracts |
| `docs/agent-runtime/authority-matrix.md` | 1-60 | Contract authority matrix |

---

## P0 Findings (Critical -- Must Fix Before Next Formal Dispatch)

### P0-001: Dual-Format Interface Contract Drift (TaskSpec)

**Location**:
- `sub-agent-dispatch-protocol.md` lines 255-300 (markdown TaskSpec format)
- `schemas/agent-runtime/task-spec.schema.json` lines 1-258 (JSON schema)

**Evidence**:

The protocol defines TaskSpec as a **markdown format** with fields:
ID, Batch, Risk, Priority, Goal, Context, Allowed Files, Forbidden, Gate 0 Ledger, Conflict Registry, Acceptance Gates, Expected Output, Rollback, Report To.

The JSON schema defines TaskSpec as a **JSON object** with fields:
task_id, title, priority, status, description, depends_on, assumptions, risk_notes, estimated_tools, gate_0, conflict_registry, security_report.

**Critical mismatches**:

| Field | Markdown Format | JSON Schema | Match? |
|-------|----------------|-------------|:------:|
| Batch | Present | Missing | NO |
| Risk (low/medium/high/critical) | Present | Missing | NO |
| Goal | Present | description (partial) | PARTIAL |
| Context | Present | Missing | NO |
| Allowed Files | Present | Missing | NO |
| Forbidden | Present | Missing | NO |
| Acceptance Gates | Present | Missing | NO |
| Expected Output | Present | Missing | NO |
| Rollback | Present | Missing | NO |
| Report To | Present | Missing | NO |
| status | Implicit | Required | MISMATCH |
| depends_on | Missing | Present | NO |
| security_report | Missing | Present | NO |

**Risk**: Agents producing markdown TaskSpecs (as shown in protocol examples, lines 302-364) cannot be validated against the JSON schema. The `additionalProperties: false` constraint (schema line 248) means any JSON TaskSpec with protocol-documented fields (Batch, Risk, Allowed Files, etc.) would **fail validation**. This creates two parallel, incompatible contract formats.

**Note**: The previous A1 review flagged a related concern -- `task_spec` in the dispatch plan schema is "only typed as an object" (previous review line 41). This review identifies the deeper issue: the two formats have diverged structurally.

**Recommendation**: Reconcile the two formats. Either:
1. Extend the JSON schema to include all protocol-documented fields (Batch, Risk, Allowed Files, Forbidden, Acceptance Gates, Expected Output, Rollback, Report To).
2. Or formally declare the markdown format as the "human-readable projection" and the JSON schema as the "machine-validatable subset", with explicit field mapping in `integration-contracts.md`.

---

### P0-002: Protected File Path Inconsistency

**Location**:
- `sub-agent-dispatch-protocol.md` line 252
- `AGENTS.md` lines 145-147 (document map)
- Actual filesystem: `D:\agent-acceptance\rules\core.md`

**Evidence**:

SADP section 0.2 declares protected files requiring exclusive lock (line 252):
```
Core rules (`docs/agent-runtime/rules/core.md`)
```

But `AGENTS.md` document map (line 146) correctly shows:
```
rules/
  core.md   <- Runtime core (8 rules: core-001 ~ core-008)
```

And the actual file exists at `D:\agent-acceptance\rules\core.md`, NOT at `D:\agent-acceptance\docs\agent-runtime\rules\core.md`.

**Risk**: An agent enforcing the protected file list would monitor the **wrong path**. A write to `rules/core.md` (the actual path) would not be detected as a protected file modification if the guard checks `docs/agent-runtime/rules/core.md`. This is a direct security gap in the governance boundary.

**Recommendation**: Update SADP section 0.2 line 252 to reference `rules/core.md`. Verify all other protected file paths against actual filesystem locations:
- `AGENTS.md` -- correct (root level)
- `CLAUDE.md` -- correct (root level, but note: user's global CLAUDE.md is at `C:\Users\RD\.claude\CLAUDE.md`)
- `capability-inventory.md` -- should be `docs/agent-runtime/capability-inventory.md` (verify this is the intended path)
- `sub-agent-dispatch-protocol.md` -- should be `docs/agent-runtime/sub-agent-dispatch-protocol.md` (verify)
- `docs/agent-runtime/rules/core.md` -- INCORRECT, should be `rules/core.md`
- `docs/agent-runtime/lessons-learned.md` -- verify exists at this path

---

## P1 Findings (High Priority -- Fix Before Next Batch)

### P1-001: Capability Inventory Numbering Gap (CAP-009 Missing)

**Location**: `capability-inventory.md` lines 217-234

**Evidence**: The inventory jumps from section "8. Reviewer Playbooks" (line 217) to "10. test-frame" (line 234). There is no CAP-009 entry. The header claims "29 capabilities" (line 4), and the summary table lists 29 rows, but the numbering sequence has a gap at position 9.

**Risk**: Automated tools referencing capabilities by sequential ID would have an off-by-one error for all capabilities after position 8. Any capability lookup by ordinal position would fail.

**Recommendation**: Either renumber sequentially (filling the CAP-009 gap), or add a "CAP-009: deprecated/removed" entry with reason and date.

---

### P1-002: Capability Passport Confidence/Status Inconsistency

**Location**: `capability-inventory.md` lines 101-107 (CAP-001 CodeGraph) and 8 other entries

**Evidence**:

CAP-001 (CodeGraph) passport:
- `verified_status: unknown`
- `confidence: 0.95`
- `usable_for_execution: true`

Per the Capability Expiration Policy (lines 44-46):
> "unknown | Never verified, declaration only | candidate_only | **forbidden**"

A capability with `verified_status: unknown` should have `usable_for_execution: false`. A confidence of 0.95 contradicts the `unknown` status.

The same pattern repeats for 7 other capabilities (CAP-020, CAP-022~027): all have `verified_status: unknown` but `usable_for_execution: true` and `confidence: 0.9`.

**Risk**: Agents relying on passport fields to decide execution eligibility would incorrectly dispatch to unverified capabilities. The expiration policy's "forbidden" rule for unknown capabilities is not reflected in the actual passport data.

**Recommendation**: Batch-update all `unknown` capabilities: set `usable_for_execution: false` and reduce `confidence` to match the actual evidence strength (e.g., 0.3-0.5 for "not installed but declared").

---

### P1-003: Reviewer Role Boundary Not Machine-Enforceable

**Location**:
- `sub-agent-dispatch-protocol.md` lines 49-58 (Role Boundaries)
- `schemas/agent-runtime/execution-report.schema.json` lines 124-127

**Evidence**: The protocol mandates (line 58):
> "The reviewer MUST run as a separate role/session/model identity from the executor/fixer."

The execution-report schema enforces this via (lines 125-126):
```json
"reviewer_role": {
  "not": { "enum": ["executor", "fixer", "coder"] }
}
```

**Gaps**:
1. The constraint only works for JSON validation. Markdown-format ExecutionReports (protocol examples, lines 372-420) bypass this constraint.
2. The constraint checks role **labels**, not session **identity**. An executor could label itself "reviewer" and pass validation.
3. The `reviewer_id` and `executor_id` fields exist in the review.yaml format (protocol lines 78-79) but are NOT present in any JSON schema, so cross-ID validation is impossible.

**Risk**: The "executor must not approve its own work" principle relies on label-based checking rather than session-ID cross-referencing.

**Recommendation**: Add `reviewer_id` and `executor_id` fields to `execution-report.schema.json` with a conditional constraint that they must differ when both are present.

---

### P1-004: Cumulative Trigger Window Advisory/Mandatory Contradiction

**Location**: `sub-agent-dispatch-protocol.md` lines 159-189

**Evidence**:

Section 0.0a states (lines 160-161):
> "**@go-only mode**: This section is advisory. Cumulative thresholds inform human judgment but do NOT force SADP activation."

But immediately below (lines 186-189):
> "Key rule: If 3 consecutive tasks under the same objective each modify 1 file, the cumulative write_set = 3, triggering SADP. The agent cannot avoid SADP by splitting..."

These statements contradict: the trigger is simultaneously "advisory" (cannot force activation) and a "key rule" (must prevent bypass).

**Risk**: An agent can legitimately claim the cumulative trigger is advisory and bypass task-splitting detection. This undermines the Plan Auditor's cumulative trigger check (section 3.3a, line 463). LL-009 (Plan Agent Self-Bypass) specifically warns about this class of vulnerability.

**Recommendation**: Resolve the contradiction. Either:
- Remove the "advisory" qualifier and make cumulative triggers mandatory.
- Or remove the "key rule" language and accept that task-splitting detection is informational only.

---

## P2 Findings (Medium Priority -- Document or Plan Fix)

### P2-001: Protocol Encoding Artifacts

**Location**: `sub-agent-dispatch-protocol.md` -- 20+ occurrences

**Evidence**: The protocol contains `锟斤拷` sequences throughout, including in critical structural positions:
- Line 16: `Decompose goal 锟斤拷 TaskSpec`
- Line 33: `dispatch 锟斤拷 it does not re-derive`
- Line 299: `Report To: [where to return ExecutionReport 锟斤拷 default: calling agent session]`
- Lines 595-600: Decision tree arrows

**Risk**: Agents parsing the protocol may misinterpret field boundaries or structural markers. Automated tooling cannot reliably parse these sections.

---

### P2-002: Dispatch Plan Schema Overly Rigid Array Constraints

**Location**: `schemas/agent-runtime/multi-agent-dispatch-plan.schema.json`

**Evidence**: Multiple assignment-level array fields use `minItems: 1` unconditionally:
- `allowed_modify_range` (line 156)
- `forbidden_modify_range` (line 161)
- `depends_on_interface_contracts` (line 169)
- `provides_interface_contracts` (line 175)
- `tests_or_probes_required` (line 192)
- `required_verification_commands` (line 198)
- `blocking_conditions` (line 213)
- `governance_record_requirements` (line 219)

**Risk**: A simple task with no dependencies, no forbidden files, or no blocking conditions cannot produce a valid assignment without placeholder strings.

---

### P2-003: External Runtime Scope Declaration Gaps

**Location**: `.agent/CONVERSATION_BINDING.json` lines 12-67 vs. `sub-agent-dispatch-protocol.md` lines 551-626

**Evidence**: CONVERSATION_BINDING declares 3 external runtimes:
1. `devframe-control-plane`
2. `dev-frame-opencode`
3. `paper-workflow`

But SADP integration points reference 5 external systems:
1. dev-frame (SADP 4.1)
2. test-frame (SADP 4.2)
3. WorkQueue (SADP 4.5)
4. Scripts (SADP 4.6)
5. opencode dispatch (SADP 4.4)

`test-frame`, `WorkQueue`, and `Scripts` are NOT declared as external runtimes in CONVERSATION_BINDING.json.

**Risk**: Runtime scope enforcement cannot cover undeclared systems. Agent interactions with test-frame or WorkQueue may not trigger `human_gate_required` checks.

---

### P2-004: Integration Contracts Status Enum Drift

**Location**:
- `docs/agent-runtime/integration-contracts.md` line 25
- `schemas/agent-runtime/task-spec.schema.json` lines 34-46

**Evidence**:
- Integration contracts define TaskSpec status: `draft`, `ready`, `deferred`, `rejected` (4 values)
- JSON schema defines TaskSpec status: `draft`, `ready`, `in_progress`, `completed`, `closed`, `deferred`, `rejected`, `accepted_with_limitation`, `pending_human_decision` (9 values)

The schema has 5 additional status values not documented in the integration contract.

---

### P2-005: SADP Section 3.3 Missing Content

**Location**: `sub-agent-dispatch-protocol.md` line 443

**Evidence**: Section 3.3 "Goal Agent (Evaluate -> Next)" has a heading on line 443 but no body content before section 3.3a begins on line 446. The section that should describe the goal agent's evaluation procedure is empty. Readers must reconstruct the flow from sections 3.3a (Plan Auditor) and 3.3b (Review Procedure).

---

## Comparison with Previous A1 Review

| Aspect | Previous A1 (2026-06-09) | This Review (2026-06-13) |
|--------|:---:|:---:|
| Verdict | PASS | PARTIAL |
| Scope | Dispatch plan scripts + governance handoff | Full protocol-to-schema chain |
| P0 findings | 0 | 2 |
| P1 findings | 0 | 4 |
| P2 findings | 0 | 5 |

The previous review correctly found no issues in its narrower scope (dispatch plan script logic, Gate 0 preflight execution safety, conflict detection algorithm, governance handoff). Those findings remain valid. This review adds findings from the **protocol document itself, schema-to-protocol consistency, capability inventory data quality, and cross-document path accuracy**.

---

## Known Gaps

### Gap 1: No Schema Validation Pipeline
No automated pipeline validates that agents produce JSON conforming to the schemas. The schemas are reference documents. The protocol operates primarily in markdown format.

### Gap 2: Pre-Write Governance Coverage (Acknowledged)
As documented in LL-010, the pre-edit governance hook only covers memory/sealed/secrets files. Protected governance files (rules/*, SADP, inventory, lessons) are not covered. Acknowledged as "acceptable for Phase 0-5."

### Gap 3: Cross-Session Identity Verification
The reviewer independence requirement relies on role labels and self-reported session IDs. No runtime-level mechanism verifies that reviewer and executor are genuinely distinct.

### Gap 4: Phase Exit Authorization Currency
Section 8 (Phase Exit Authorization) was last updated 2026-05-28. Capability passport statuses have been updated since (2026-06-10, 2026-06-12) but the Phase Exit table has not been re-validated.

---

## Architecture Strengths (Positive Findings)

1. **Role separation** (SADP 0.R.1): Three-tier model with explicit "may produce" / "must not produce" boundaries.
2. **Gate 0 evidence contract**: Requires inventory_evidence with queried_sources, not boolean self-attestation (directly addresses LL-007).
3. **Conflict registry**: read_set/write_set with serialization rules and exclusive locks for protected files.
4. **Authority matrix**: "Declaration != Authorization" principle with GateResult inviolable boundary.
5. **Capability expiration policy**: Decay model with different expiry windows for external vs. local capabilities.
6. **Fallback matrix**: Risk-graded fallback with "silent fallback forbidden" rule.
7. **Plan Auditor independence**: Anti-recursion constraint and bounded cost model (0-1 LLM calls per session).
8. **Dispatch plan script safety** (confirmed by previous A1): Gate 0 preflight is read-only, conflict detection is correct, integrator is the sole serial write point.

---

## Suggested Review Focus for Integrator

### Priority 1: Reconcile TaskSpec Formats (P0-001)
Before the next dispatch cycle, decide whether markdown or JSON is authoritative, and align the other. If both must coexist, document explicit field mapping in `integration-contracts.md`.

### Priority 2: Fix Protected File Paths (P0-002)
Verify all 6 protected file paths in SADP section 0.2 against the actual filesystem. Quick fix with high security impact.

### Priority 3: Align Passport Fields with Expiration Policy (P1-002)
Batch-update all `unknown` capabilities to `usable_for_execution: false` with appropriate confidence values. Single maintenance task.

### Priority 4: Clarify Cumulative Trigger Status (P1-004)
Resolve the advisory/mandatory contradiction in section 0.0a. Affects Plan Auditor enforcement.

### Priority 5: Strengthen Reviewer Identity Verification (P1-003)
Add reviewer_id/executor_id fields to the execution-report schema with a not-equal constraint.

### Priority 6: Declare Missing External Runtimes (P2-003)
Add test-frame, WorkQueue, and Scripts to CONVERSATION_BINDING.json governance_scope, or document why they are excluded.

---

## Verdict Summary

| Category | Count | IDs |
|----------|:-----:|-----|
| P0 (Critical) | 2 | P0-001, P0-002 |
| P1 (High) | 4 | P1-001, P1-002, P1-003, P1-004 |
| P2 (Medium) | 5 | P2-001, P2-002, P2-003, P2-004, P2-005 |
| Known Gaps | 4 | Gap 1-4 |
| Positive Findings | 8 | (see above) |

**Verdict: PARTIAL** -- The architecture is well-designed with strong governance principles, but has interface contract inconsistencies and path errors that must be resolved before the next formal multi-agent dispatch cycle. Both P0 findings are fixable within a single maintenance session.

---

> Report: Architecture Review A1-R2
> Generated: 2026-06-13
> Previous review: A1 (2026-06-09, PASS for dispatch plan scope)
> Next review trigger: After P0 remediation, or before next @go batch dispatch
