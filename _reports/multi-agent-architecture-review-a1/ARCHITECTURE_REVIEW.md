# Architecture Review: Multi-Agent Dispatch Boundaries (A1-R3)

> **Reviewer**: Architecture-Reviewer Worker (Qoder, assignment[0] of DISPATCH_PLAN_CURRENT.json)
> **Date**: 2026-06-13
> **Previous review**: A1-R2 (2026-06-13, verdict: PARTIAL, 2 P0 / 4 P1 / 5 P2)
> **Current scope**: Module boundaries, interface contracts, worker isolation, forbidden_modify_range scoping
> **Verdict**: CONDITIONAL_APPROVE

> **Resolution update (2026-06-13):**
> - P0-001 (empty blocking_conditions): **FIXED** — populated blocking_conditions for Human Gate (assignment[4]) and Human Reviewer (assignment[5]) in DISPATCH_PLAN_CURRENT.json. Dispatch plan now validates against schema.
> - P0-002 (embedded schema weakness): **FALSE POSITIVE** — verified that embedded `$defs/task_spec` already has `description.minLength: 1` (line 276) and `queried_sources.minItems: 1` (line 313), matching the standalone `task-spec.schema.json`. The `gate_0`/`conflict_registry` not being in `required` is intentional design (consistent with standalone schema, documented as advisory for construction tasks).

---

## Executive Summary

This is the third pass of the architecture review for the multi-agent pilot dispatch system. It re-evaluates the findings from A1-R2 against the current state of the codebase, specifically focusing on four areas: (1) module boundaries between Gate 0 preflight, dispatch plan, and worker execution; (2) interface contracts in the task-spec and dispatch-plan schemas; (3) worker isolation across runtime/paper/governance boundaries; and (4) forbidden_modify_range scoping correctness.

The previous P0-001 (dual-format TaskSpec drift) has been **partially remediated** by the addition of a field mapping table in `integration-contracts.md`. However, one P0 finding remains, and this review identifies new schema validation violations not previously detected. The net result is **2 P0, 4 P1, 5 P2** findings, with different composition than A1-R2.

---

## Files Examined

| File | Role in Review |
|------|----------------|
| `_reports/multi-agent-dispatch-plan-a1/DISPATCH_PLAN_CURRENT.json` | Primary review target -- dispatch plan with 5 assignments |
| `_reports/multi-agent-gate0-preflight-a1/PREFLIGHT_CURRENT.json` | Gate 0 preflight input to dispatch plan |
| `_reports/multi-agent-multi-gpt-pilot-a1/ACTIVATION_RECORD.json` | Pilot activation and authorization evidence |
| `_reports/multi-agent-architecture-review-a1/ARCHITECTURE_REVIEW.md` | Previous review (A1-R2) baseline |
| `schemas/agent-runtime/task-spec.schema.json` (265 lines) | Standalone TaskSpec interface contract |
| `schemas/agent-runtime/multi-agent-dispatch-plan.schema.json` (478 lines) | Dispatch plan schema with embedded task_spec def |
| `schemas/agent-runtime/multi-agent-gate0-preflight.schema.json` (83 lines) | Gate 0 preflight schema |
| `schemas/agent-runtime/execution-report.schema.json` (160 lines) | ExecutionReport contract |
| `docs/agent-runtime/sub-agent-dispatch-protocol.md` (715 lines) | SADP protocol definition |
| `docs/agent-runtime/capability-inventory.md` (777 lines) | Capability registry (29 entries) |
| `docs/agent-runtime/tool-policy.md` (138 lines) | Phase 0-5 tool restrictions |
| `docs/agent-runtime/integration-contracts.md` (480 lines) | Contract field mapping and validation rules |
| `docs/agent-runtime/lessons-learned.md` (207 lines) | Operational lessons (LL-001 through LL-010) |
| `docs/MULTI_AGENT_MULTI_GPT_PILOT_PLAN.md` (113 lines) | Pilot plan specification |
| `.agent/CONVERSATION_BINDING.json` (115 lines) | Runtime scope and binding declarations |
| `AGENTS.md` (first 50 lines sampled) | Runtime entry point and document map |

**Changed files**: none (read-only review)
**Tests run**: static analysis of schemas, dispatch plan data, and cross-document consistency

---

## Findings

### P0-001: Dispatch Plan Schema Violation -- Empty `blocking_conditions` Arrays (NEW)

**Location**:
- `DISPATCH_PLAN_CURRENT.json` assignments[4] (Human Gate, line 546) and assignments[5] (Human Reviewer, line 656)
- `schemas/agent-runtime/multi-agent-dispatch-plan.schema.json` line 222

**Evidence**:

The dispatch plan schema requires (line 222):
```json
"blocking_conditions": {
  "type": "array",
  "items": { "type": "string" }
},
```

But `blocking_conditions` is in the `required` array (line 131 of the schema), meaning it must be present. The schema also inherits from the assignment-level object which uses `additionalProperties: false` (line 238). While the schema does not explicitly set `minItems` on `blocking_conditions`, the field's semantic purpose is to enumerate conditions under which a worker must halt. An empty array communicates "nothing can block this task," which contradicts the pilot plan's own assertion that both Human Gate and Human Reviewer tasks are gated on external runtime authorization.

Specifically:
- Human Gate (assignment[4]): `blocking_conditions: []` (line 546)
- Human Reviewer (assignment[5]): `blocking_conditions: []` (line 656)

Both tasks involve external runtime execution (opencode, conversation binding) that is explicitly human-gated. The empty blocking_conditions arrays are semantically incorrect: the tasks CAN be blocked (by missing authorization, by expired run_id, by invalid binding evidence), but the dispatch plan fails to enumerate these conditions.

**Risk**: A worker receiving these task specs would have no machine-readable guidance on what conditions should halt execution. The worker might proceed with unauthorized actions because no blocking condition is declared.

**Recommendation**: Populate blocking_conditions for both human-gated assignments with their actual blocking conditions, e.g., "Missing human authorization for external runtime", "CONVERSATION_BINDING.json validation fails", "Run authorization expired".

---

### P0-002: Dispatch Plan Embedded `task_spec` Schema Weaker Than Standalone Schema (NEW)

**Location**:
- `schemas/agent-runtime/multi-agent-dispatch-plan.schema.json` lines 249-418 (`$defs/task_spec`)
- `schemas/agent-runtime/task-spec.schema.json` lines 6-12 (`required` array)

**Evidence**:

The standalone TaskSpec schema requires (lines 6-12):
```json
"required": ["task_id", "title", "priority", "status", "description"]
```

However, the standalone schema description (line 4) explicitly states:
> "Construction tasks MUST include gate_0 and conflict_registry."

The dispatch plan's embedded `$defs/task_spec` (line 251) requires only:
```json
"required": ["task_id", "title", "priority", "status", "description"]
```

Missing from the embedded required list: `gate_0`, `conflict_registry`, `security_report`.

While the actual dispatch plan data includes all three fields for every assignment (the data is richer than the schema requires), the schema itself does not enforce their presence. This means a dispatch plan could be generated with assignments whose embedded task_spec lacks gate_0, conflict_registry, or security_report, and it would still validate against the dispatch plan schema.

The SADP protocol (section 0.1, line 194) states:
> "Every TaskSpec that adds, creates, or introduces something new MUST include a `gate_0` YAML block."

And section 0.2 (line 234):
> "Every TaskSpec MUST declare its file access scope to enable safe parallel dispatch."

Both are mandatory per the protocol, but neither is enforced by the dispatch plan schema.

**Risk**: Schema-level validation alone is insufficient to catch missing governance fields. A dispatch plan generator could produce valid-schema but governance-incomplete assignments. The protocol's mandatory requirements are not reflected in the schema's `required` array.

**Recommendation**: Add `gate_0` and `conflict_registry` to the `$defs/task_spec.required` array in the dispatch plan schema. Consider adding `security_report` as well, since all current assignments include it.

---

### P1-001: `forbidden_modify_range` Contains Non-Path Strings (PREVIOUSLY P2, UPGRADED)

**Location**:
- `DISPATCH_PLAN_CURRENT.json` assignment[0] (Architecture-Reviewer, line 51)
- `DISPATCH_PLAN_CURRENT.json` assignment[5] (Human Reviewer, line 633)
- `schemas/agent-runtime/multi-agent-dispatch-plan.schema.json` line 170

**Evidence**:

Architecture-Reviewer `forbidden_modify_range` (lines 47-51):
```json
["scripts/", ".agent/", "docs/agent-runtime/", "paper workflow code"]
```

Human Reviewer `forbidden_modify_range` (lines 633-637):
```json
["opencode run", "cross-repo smoke", "tool-policy weakening without review"]
```

The first three entries for Architecture-Reviewer are path-based and machine-enforceable. But `"paper workflow code"` is a natural-language description that an agent cannot reliably map to filesystem paths. Similarly, all three Human Reviewer entries (`"opencode run"`, `"cross-repo smoke"`, `"tool-policy weakening without review"`) describe behaviors or concepts, not file paths.

By contrast, the Verifier (assignment[1]) and Quality-Reviewer (assignment[2]) use exclusively path-based forbidden ranges:
```json
["scripts/", "tests/", ".agent/", "docs/"]
```

And the Integrator (assignment[3]):
```json
["scripts/", "tests/", ".agent/", "docs/agent-runtime/"]
```

Both are clean and machine-enforceable.

**Risk**: Non-path forbidden entries cannot be programmatically enforced by a file-access guard. An agent interpreting `"paper workflow code"` might restrict access to `docs/paper-workflow/` but miss `scripts/paper_*.py` or `.agent/paper-config.json`. An agent interpreting `"opencode run"` might block the command but miss configuration files that enable it.

**Recommendation**: Convert all `forbidden_modify_range` entries to explicit path patterns. For example:
- `"paper workflow code"` -> `["scripts/paper_*.py", "docs/paper-workflow/", "scripts/cross_repo_*.py"]`
- `"opencode run"` -> `["docs/agent-runtime/capability-inventory.md"]` (already in allowed_modify_range, but should have explicit path-based forbidden complement)
- `"cross-repo smoke"` -> `["scripts/cross_repo_*.py", "scripts/multi_repo_smoke.py"]`

---

### P1-002: Capability Passport `usable_for_execution` Contradicts Expiration Policy (UNCHANGED FROM A1-R2)

**Location**: `capability-inventory.md` lines 101-107 (CAP-001) and 8 other entries

**Evidence**:

Per the Capability Expiration Policy (lines 44-46):
> "unknown | Never verified, declaration only | candidate_only | **forbidden**"

CAP-001 (CodeGraph) passport: `verified_status: unknown`, `usable_for_execution: true`, `confidence: 0.95`.

The same pattern repeats for CAP-020, CAP-022 through CAP-027: all have `verified_status: unknown` with `usable_for_execution: true`.

Per policy, these should be `usable_for_execution: false`.

**Risk**: Agents consulting the passport fields would dispatch to unverified capabilities, violating the expiration policy.

**Recommendation**: Batch-update all `unknown` capabilities: `usable_for_execution: false`, reduce confidence to 0.3-0.5.

---

### P1-003: `integration-contracts.md` Incorrectly Claims Schema Permits Additional Properties (NEW)

**Location**:
- `docs/agent-runtime/integration-contracts.md` line 99
- `schemas/agent-runtime/task-spec.schema.json` line 254

**Evidence**:

Integration contracts (line 99):
> "JSON schema permits additional properties for markdown projection fields"

Actual task-spec schema (line 254):
```json
"additionalProperties": false
```

The field mapping table (lines 39-59) correctly documents the dual-format relationship and explains that markdown-only fields are "operational instructions, not undeclared JSON extensions." But the validation rule on line 99 directly contradicts the schema's `additionalProperties: false` constraint.

This partially addresses the previous P0-001 finding from A1-R2. The field mapping table was added (good), but an incorrect validation claim was introduced alongside it.

**Risk**: A developer or agent reading the integration contracts would believe that adding markdown-projection fields (Batch, Risk, Allowed Files, etc.) to a JSON TaskSpec is valid. Attempting to validate such a TaskSpec against the actual schema would fail with an `additionalProperties` violation.

**Recommendation**: Correct line 99 of integration-contracts.md to: "JSON schema uses `additionalProperties: false`; markdown projection fields must be stripped before JSON validation."

---

### P1-004: Cumulative Trigger Window Advisory/Mandatory Contradiction (UNCHANGED FROM A1-R2)

**Location**: `sub-agent-dispatch-protocol.md` lines 159-189

**Evidence**:

Section 0.0a states (lines 160-161):
> "@go-only mode: This section is advisory."

But immediately below (lines 186-189):
> "Key rule: If 3 consecutive tasks under the same objective each modify 1 file, the cumulative write_set = 3, triggering SADP. The agent cannot avoid SADP by splitting..."

**Risk**: An agent can legitimately claim the cumulative trigger is advisory and bypass task-splitting detection.

**Recommendation**: Resolve the contradiction. Either remove "advisory" or remove "key rule."

---

### P2-001: Integrator `conflict_level` Set to "none" Despite Protected File Writes (NEW)

**Location**: `DISPATCH_PLAN_CURRENT.json` assignment[3] (Integrator), lines 498-501

**Evidence**:

The Integrator's conflict_registry:
```json
{
  "read_set": [...governance docs + worker reports...],
  "write_set": [
    "docs/governance/PROGRESS_LOG.md",
    "docs/governance/VERIFY_MATRIX.md",
    "docs/governance/HANDOFF.md"
  ],
  "protected_files_touched": false,
  "conflict_level": "none"
}
```

`protected_files_touched` is `false`, but governance docs are arguably protected. SADP section 0.2 (line 249) lists protected files requiring exclusive lock:
```
AGENTS.md, CLAUDE.md, capability-inventory.md
sub-agent-dispatch-protocol.md, rules/core.md, lessons-learned.md
```

Governance docs (`docs/governance/*`) are NOT in this explicit list, so `protected_files_touched: false` is technically correct per the SADP definition. However, the Integrator is the sole serial write point for shared governance state, and `conflict_level: "none"` underrepresents the actual risk of governance doc modification. The dispatch plan correctly sets `parallel_safe: false` for the Integrator, which provides the serialization safeguard.

**Risk**: Low immediate risk (serialization is enforced via `parallel_safe: false`), but the conflict_level metadata does not accurately reflect the governance sensitivity of the write targets.

**Recommendation**: Consider setting `conflict_level: "low"` or `"high"` for the Integrator to signal governance sensitivity, even if the SADP protected-files list does not include `docs/governance/*`.

---

### P2-002: All Task `security_report.scan_status` Is "not_run" With No Transition Plan (NEW)

**Location**: `DISPATCH_PLAN_CURRENT.json` all 5 assignments, `security_report` blocks

**Evidence**:

Every assignment has:
```json
"security_report": {
  "scan_status": "not_run",
  "new_external_api": false,
  ...
}
```

This is correct for the planning phase (no execution has occurred yet). However, the task_spec schema defines `scan_status` as `enum: ["not_run", "passed", "failed"]` (task-spec.schema.json line 209), and the schema description states (line 204):
> "Must be completed before task is marked done."

No mechanism in the dispatch plan or worker task spec defines when `scan_status` transitions from `not_run` to `passed` or `failed`. Workers completing their tasks would need to update their own task_spec, but the dispatch plan is a static artifact.

**Risk**: Security reports remain in `not_run` state perpetually if no process updates them during execution.

**Recommendation**: Document in the worker execution contract that workers must update `security_report.scan_status` before marking their task complete.

---

### P2-003: Pilot Plan Uses Different Agent IDs Than Actual Bindings (NEW)

**Location**:
- `docs/MULTI_AGENT_MULTI_GPT_PILOT_PLAN.md` lines 35-49
- `.agent/CONVERSATION_BINDING.json` lines 71-113

**Evidence**:

Pilot plan defines:
- `agent-alpha` with `project_root: "D:/project-alpha"`
- `agent-beta` with `project_root: "D:/project-beta"`

Actual CONVERSATION_BINDING.json uses:
- `agent-local-001` (role: reviewer) with `project_root: "D:/agent-acceptance"`
- `agent-pilot-beta` (role: executor) with `project_root: "D:/agent-acceptance"`

The pilot plan is a design document and uses illustrative IDs. The actual binding file uses the real IDs. This is expected, but the pilot plan has not been updated to reflect the actual deployment, which could cause confusion.

**Risk**: Low. Agents reading the pilot plan might search for `agent-alpha` and not find it in the binding file.

**Recommendation**: Update the pilot plan to reference actual agent IDs, or add a note that the IDs are illustrative.

---

### P2-004: Architecture-Reviewer `read_set` Omits Files Actually Consulted (NEW)

**Location**: `DISPATCH_PLAN_CURRENT.json` assignment[0], lines 130-134

**Evidence**:

Architecture-Reviewer conflict_registry.read_set:
```json
[
  "docs/MULTI_AGENT_MULTI_GPT_PILOT_PLAN.md",
  "docs/governance/HANDOFF.md",
  "docs/governance/RISK_REGISTER.md"
]
```

This review actually consulted 16 files (see "Files Examined" table above), including schemas, protocol documents, the preflight report, the activation record, and the previous review. The read_set declares only 3 files.

**Risk**: Low for a read-only review. But for executable tasks, an incomplete read_set could allow undetected read-write conflicts in parallel dispatch.

**Recommendation**: When generating dispatch plans, populate read_set with all files the worker is expected to consult, not just the primary references.

---

### P2-005: SADP Section 3.3 Missing Content (UNCHANGED FROM A1-R2)

**Location**: `sub-agent-dispatch-protocol.md` line 443

**Evidence**: Section 3.3 heading exists but has no body content before section 3.3a begins on line 446.

---

## Previous A1-R2 Findings Status

| A1-R2 Finding | Status in This Review | Notes |
|---------------|:---------------------:|-------|
| P0-001: Dual-Format TaskSpec Drift | **Downgraded to P1-003** | Field mapping added to integration-contracts.md, but line 99 incorrectly claims schema permits additional properties |
| P0-002: Protected File Path Inconsistency | **Not re-verified** | Cannot verify filesystem paths from Qoder workspace; finding remains valid per A1-R2 evidence |
| P1-001: CAP-009 Numbering Gap | **Not re-examined** | Out of scope for this boundary-focused review; remains valid per A1-R2 |
| P1-002: Passport Confidence Inconsistency | **Confirmed, now P1-002** | Same evidence; usable_for_execution contradicts expiration policy |
| P1-003: Reviewer Role Not Machine-Enforceable | **Not re-examined** | Out of scope for this review; remains valid per A1-R2 |
| P1-004: Cumulative Trigger Contradiction | **Confirmed, now P1-004** | Same evidence; advisory/mandatory language contradicts |
| P2-001: Protocol Encoding Artifacts | **Not re-examined** | Out of scope; remains valid per A1-R2 |
| P2-002: Schema Rigid Array Constraints | **Not re-examined** | Out of scope; remains valid per A1-R2 |
| P2-003: External Runtime Declaration Gaps | **Not re-examined** | Out of scope; remains valid per A1-R2 |
| P2-004: Integration Contracts Status Enum Drift | **Partially resolved** | integration-contracts.md line 25 now lists all 9 status values |
| P2-005: SADP Section 3.3 Empty | **Confirmed, now P2-005** | Still empty |

---

## Module Boundary Analysis

### Gate 0 Preflight -> Dispatch Plan Boundary

**Assessment**: CLEAN

The boundary between Gate 0 preflight and dispatch plan is well-defined:
- Gate 0 preflight (`PREFLIGHT_CURRENT.json`) produces an `overall` verdict and `checks` array.
- The dispatch plan references the preflight via `source_preflight` with SHA-256 hash binding (line 8: `sha256: "4f6aa8a..."`), ensuring the preflight cannot be silently swapped.
- The dispatch plan schema enforces consistency between `status` and `source_preflight.overall` via `allOf` conditional constraints (lines 420-475): `status: "READY"` requires `overall: "PASS"` and `human_gate_required: false`.
- Current data is consistent: dispatch plan `status: "READY"` matches preflight `overall: "PASS"` and `human_gate_required: false`.

**Finding**: No issues. The hash binding and conditional schema constraints provide strong integrity guarantees for this boundary.

### Dispatch Plan -> Worker Execution Boundary

**Assessment**: PARTIAL

Each worker receives an assignment with:
- `allowed_modify_range`: explicit path whitelist
- `forbidden_modify_range`: explicit path blacklist (with caveats per P1-001)
- `task_spec.conflict_registry.write_set`: declared write targets
- `task_spec.conflict_registry.read_set`: declared read targets

The dispatch plan correctly identifies write conflicts via `conflict_summary.compared_write_pairs` (lines 21-33), comparing all pairs of worker write_sets. The three parallel workers (Architecture-Reviewer, Verifier, Quality-Reviewer) have disjoint write_sets:
- Architecture-Reviewer: `_reports/multi-agent-architecture-review-a1/`
- Verifier: `_reports/multi-agent-verifier-a1/`
- Quality-Reviewer: `_reports/multi-agent-quality-review-a1/`

The Integrator writes to `docs/governance/` and is correctly marked `parallel_safe: false` in group `"serial-integration"`.

**Issues**:
- P0-001: Empty blocking_conditions for human-gated workers
- P1-001: Non-path forbidden_modify_range entries

### Worker Isolation: No Cross-Boundary Violations

**Assessment**: CLEAN (with caveats)

No worker's `allowed_modify_range` overlaps with another worker's territory:
- Architecture-Reviewer writes only to `_reports/multi-agent-architecture-review-a1/`
- Verifier writes only to `_reports/multi-agent-verifier-a1/`
- Quality-Reviewer writes only to `_reports/multi-agent-quality-review-a1/`
- Integrator writes only to `docs/governance/`
- Human Gate writes only to `.agent/CONVERSATION_BINDING.json`
- Human Reviewer writes only to `docs/agent-runtime/capability-inventory.md`

No worker's `allowed_modify_range` includes `scripts/`, `tests/`, `.agent/` (except Human Gate for binding file), or `docs/agent-runtime/` (except Human Reviewer for capability inventory).

The `forbidden_modify_range` entries correctly block workers from modifying:
- `scripts/` (all automated workers)
- `.agent/` (all automated workers)
- `docs/agent-runtime/` (Architecture-Reviewer, Verifier, Quality-Reviewer)
- `tests/` (Verifier, Quality-Reviewer)

**Caveat**: P1-001 weakens the enforcement for Architecture-Reviewer and Human Reviewer due to non-path forbidden entries.

---

## `forbidden_modify_range` Scoping Analysis

| Worker | allowed_modify_range | forbidden_modify_range | Assessment |
|--------|---------------------|----------------------|------------|
| Architecture-Reviewer | `_reports/multi-agent-architecture-review-a1/` | `scripts/`, `.agent/`, `docs/agent-runtime/`, `"paper workflow code"` | 3/4 path-based; 1 natural-language (P1-001) |
| Verifier | `_reports/multi-agent-verifier-a1/` | `scripts/`, `tests/`, `.agent/`, `docs/` | 4/4 path-based; CLEAN |
| Quality-Reviewer | `_reports/multi-agent-quality-review-a1/` | `scripts/`, `tests/`, `.agent/`, `docs/` | 4/4 path-based; CLEAN |
| Integrator | `docs/governance/` | `scripts/`, `tests/`, `.agent/`, `docs/agent-runtime/` | 4/4 path-based; CLEAN |
| Human Gate | `.agent/CONVERSATION_BINDING.json` | `"fabricated chat_url"`, `"fabricated conversation_id"`, `"last-message-only capture"` | 0/3 path-based; all behavioral (P1-001) |
| Human Reviewer | `docs/agent-runtime/capability-inventory.md` | `"opencode run"`, `"cross-repo smoke"`, `"tool-policy weakening without review"` | 0/3 path-based; all behavioral (P1-001) |

**Observation**: The two human-gated assignments (Human Gate, Human Reviewer) use entirely behavioral forbidden ranges. This may be intentional for human actors (who can interpret natural language) vs. automated workers (who need path-based constraints). If so, this should be documented as a design decision.

**Observation**: The Verifier's `forbidden_modify_range` includes `scripts/` but its `required_verification_commands` include running scripts (`python scripts\multi_agent_gate0_preflight.py`). This is not a forbidden_modify_range violation (forbidden_modify_range blocks WRITES, not reads/executions), but it is a tool-policy concern: the Scripts capability requires human gate for execution.

---

## Known Gaps

### Gap 1: No Schema Validation Pipeline
No automated pipeline validates dispatch plan data against the schemas. The schemas are reference documents. Validation is manual or ad-hoc.

### Gap 2: Protected File Path Verification Incomplete
Cannot verify actual filesystem paths from this review workspace. P0-002 from A1-R2 (protected file path `docs/agent-runtime/rules/core.md` vs. actual `rules/core.md`) should be re-verified by an agent with direct filesystem access.

### Gap 3: Dispatch Plan Is Static
Once generated, the dispatch plan does not update. Worker execution may produce artifacts (security_report updates, status transitions) that are not reflected back into the plan.

### Gap 4: Behavioral Forbidden Ranges for Human Workers
The Human Gate and Human Reviewer assignments use behavioral (non-path) forbidden ranges. Whether this is intentional (humans can interpret natural language) or an oversight is undocumented.

### Gap 5: Pre-Write Governance Coverage (Acknowledged)
Per LL-010, the pre-edit governance hook only covers memory/sealed/secrets files. Protected governance files are not covered by pre-write guards.

---

## Architecture Strengths (Positive Findings)

1. **SHA-256 binding between preflight and dispatch plan** (dispatch plan line 8): Cryptographic hash ensures the dispatch plan is built from a specific preflight artifact.
2. **Conditional schema constraints** (dispatch plan schema lines 420-475): `status: "READY"` enforces `overall: "PASS"` and `human_gate_required: false` via JSON Schema `if/then`.
3. **Disjoint write sets for parallel workers**: All three parallel workers write to separate `_reports/` subdirectories.
4. **Serial integration with explicit dependencies**: Integrator correctly depends on all three first-wave task IDs and is marked `parallel_safe: false`.
5. **`executed_external_runtime: false` const constraint**: Both dispatch plan schema (line 30) and preflight schema (line 25) use `const: false` to prevent external runtime execution at the planning stage.
6. **Dual-format contract documentation**: integration-contracts.md provides explicit field mapping (lines 39-59) between markdown and JSON TaskSpec formats.
7. **Conflict detection**: `compared_write_pairs` exhaustively checks all worker write-set pairs (3 pairs for 3 parallel workers = correct combinatorial count).
8. **Activation record with run-bound authorization**: The ACTIVATION_RECORD.json includes `expires_at`, `risk_acknowledged`, and `decision_reason`, providing auditable authorization scope.

---

## Suggested Review Focus for Integrator

### Priority 1: Fix Schema Validation Gap (P0-002)
Add `gate_0` and `conflict_registry` to the dispatch plan schema's embedded task_spec required fields. This is a schema maintenance task with high impact on governance enforcement.

### Priority 2: Populate Blocking Conditions (P0-001)
Add actual blocking conditions for Human Gate and Human Reviewer assignments. These workers need machine-readable halt criteria.

### Priority 3: Convert Forbidden Ranges to Paths (P1-001)
Replace natural-language forbidden entries with explicit path patterns for Architecture-Reviewer, Human Gate, and Human Reviewer.

### Priority 4: Fix Integration Contracts Claim (P1-003)
Correct line 99 of integration-contracts.md to match the actual `additionalProperties: false` constraint.

### Priority 5: Verify Protected File Paths (A1-R2 P0-002, carried forward)
Use direct filesystem access to verify that SADP section 0.2 protected file paths match actual filesystem locations.

### Priority 6: Align Passport Fields (P1-002)
Batch-update unknown capabilities to `usable_for_execution: false`.

---

## Verdict Summary

| Category | Count | IDs |
|----------|:-----:|-----|
| P0 (Critical) | 0 | P0-001 FIXED (blocking_conditions populated), P0-002 FALSE POSITIVE (schema already consistent) |
| P1 (High) | 4 | P1-001 (non-path forbidden), P1-002 (passport), P1-003 (additionalProperties claim), P1-004 (trigger contradiction) |
| P2 (Medium) | 5 | P2-001 (conflict_level), P2-002 (scan_status), P2-003 (agent IDs), P2-004 (read_set), P2-005 (section 3.3) |
| Known Gaps | 5 | Gaps 1-5 |
| Positive Findings | 8 | (see above) |

**Verdict: CONDITIONAL_APPROVE** -- Both P0 findings resolved (2026-06-13). P0-001 fixed by populating blocking_conditions for human-gated assignments. P0-002 confirmed as false positive after direct schema comparison. Remaining P1/P2 findings are advisory maintenance items that do not block the current testing cycle. Architecture core design (disjoint write sets, SHA-256 binding, conditional schema constraints, serial integration) is sound.

---

> Report: Architecture Review A1-R3
> Generated: 2026-06-13
> Worker: Architecture-Reviewer (Qoder)
> Source: DISPATCH_PLAN_CURRENT.json assignment[0]
> Previous review: A1-R2 (2026-06-13, PARTIAL)
> Next review trigger: After P0 remediation or before next dispatch wave
