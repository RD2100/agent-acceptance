# Resource Integration Plan -- R0-R7

> Batch R0-A, 2026-05-27
> RD2100 Agent Runtime v2

## Current Phase

```
R0: ACTIVE  (Registry and Classification)
R1: FUTURE  (Blackboard Read-only Snapshot)
R2: FUTURE  (test-frame Evidence Provider)
R3: FUTURE  (dev-frame Orchestration Adapter)
R4: FUTURE  (CodeGraph Stale-aware Policy)
R5: FUTURE  (Local Skills / Claude Rules Intake)
R6: FUTURE  (RD2100 Memory Context Map)
R7: FUTURE  (Scripts / WorkQueue Controlled Use)
```

## R0 Definition

> **Registry and classification only.**

R0 produces registration records and classification decisions. It does not execute, enable, install, or configure any resource.

Key constraints:

- **Register != Enable.** Adding a resource to the registry does not grant it any execution capability.
- **Candidate != Adapter.** Promoting a resource to `candidate` status does not create an integration adapter.
- **Adapter != Capability.** Drafting or dry-running an adapter does not approve the resource as a runtime capability.
- **R0 cannot approve capability.** The `promotion_status` enum ends at `candidate` (within R0). The `lifecycle_state` enum includes `capability_approved` as a valid state, but R0 cannot set it -- that requires R6+ gates.

## Roadmap: R0-R7

| Phase | Name | Status | Description |
|-------|------|--------|-------------|
| R0 | Resource Registry & Classification | **ACTIVE** | Discover, register, classify all local resources. Produce resource-registry records. Define promotion gates. No execution. |
| R1 | Blackboard Read-only Snapshot | FUTURE | Snapshot Blackboard state for evidence. Validate bb_* tool availability. Contract mapping A3 verified. |
| R2 | test-frame Evidence Provider | FUTURE | Integrate test-frame as evidence source. Run discoverer to identify test suites. Produce evidence index records. No test execution. |
| R3 | dev-frame Orchestration Adapter | FUTURE | Draft adapter for dev-frame orchestration layer. Dry-run read-only orchestration commands. Validate smoke_test.py interface. |
| R4 | CodeGraph Stale-aware Policy | FUTURE | Human-gated stale check policy; no automatic reindex. Contract mapping A2 verified with freshness checks. All reindex decisions require explicit human approval. |
| R5 | Local Skills / Claude Rules Intake | FUTURE | Evaluate skills-inbox/ and rules/ directories. Produce SkillIntakeRecords. No installation -- intake evaluation only. |
| R6 | RD2100 Memory Context Map | FUTURE | Map memory system layers (file, structured, collaborative). Produce MemoryUpdateRecords (proposed only). Validate memory architecture. |
| R7 | Scripts / WorkQueue Controlled Use | FUTURE | Controlled execution of approved scripts. Dry-run WorkQueue processing. Human-gated script execution with evidence collection. |

## Promotion Gate Definitions

Each gate represents exactly one step in the R0-R7 progression. Gates must be passed sequentially -- skipping gates is forbidden.

### Gate 1: `registered_to_candidate`

- **From**: `promotion_status` = `registered`
- **To**: `promotion_status` = `candidate`
- **Phase**: R0
- **Preconditions**:
  - `resource_id` exists in registry
  - `path_status` is `exists` or `verified`
  - `local_verification_status` is not `blocked`
  - `risk_level` assessed
  - `lifecycle_state` is at least `classified`
- **Human gate**: Required if `risk_level` is `high` or `critical`

### Gate 2: `candidate_to_evaluated`

- **From**: `lifecycle_state` = `classified`
- **To**: `lifecycle_state` = `evaluated`
- **Phase**: R1-R2
- **Preconditions**:
  - Gate 1 passed (promotion_status is at least `candidate`)
  - Evidence requirements defined
  - Contract mapping validated (references verified)
  - Access mode re-evaluated
- **Human gate**: Required if access mode escalation is proposed

### Gate 3: `evaluated_to_adapter_draft`

- **From**: `lifecycle_state` = `evaluated`
- **To**: `lifecycle_state` = `adapter_draft`
- **Phase**: R3
- **Preconditions**:
  - Gate 2 passed
  - Resource type supports adapter (not `native_runtime`, not `rules_config`)
  - Adapter specification drafted
  - Read-only interface defined
- **Human gate**: Always required (adapter design is architectural)

### Gate 4: `adapter_draft_to_adapter_dry_run`

- **From**: `lifecycle_state` = `adapter_draft`
- **To**: `lifecycle_state` = `adapter_dry_run`
- **Phase**: R3-R4
- **Preconditions**:
  - Gate 3 passed
  - Adapter specification approved by reviewer
  - Dry-run scope defined (no side effects)
  - Rollback plan documented
- **Human gate**: Always required (dry-run may touch real systems)

### Gate 5: `adapter_dry_run_to_capability_proposed`

- **From**: `lifecycle_state` = `adapter_dry_run`
- **To**: `lifecycle_state` = `capability_proposed`
- **Phase**: R5-R6
- **Preconditions**:
  - Gate 4 passed
  - Dry-run completed successfully
  - Evidence collected and verified
  - No blocking issues from dry-run
- **Human gate**: Always required (capability proposal is a commitment)

### Gate 6: `capability_proposed_to_capability_approved`

- **From**: `lifecycle_state` = `capability_proposed`
- **To**: `lifecycle_state` = `capability_approved`
- **Phase**: R6-R7
- **Preconditions**:
  - Gate 5 passed
  - All gates 1-5 evidence reviewed
  - Full risk assessment updated
  - Integration contracts fully validated
  - Reviewer approval obtained
- **Human gate**: Always required (final capability approval)
- **Note**: This is the MAXIMUM gate. There is no `capability_approved_to_active` gate. The `active` lifecycle state is set post-approval but does not require a separate promotion gate.

### Gate Mapping Summary

| # | Gate Name | Phase | Human Gate |
|---|-----------|-------|:----------:|
| 1 | `registered_to_candidate` | R0 | Conditional (high/critical risk) |
| 2 | `candidate_to_evaluated` | R1-R2 | Conditional (access escalation) |
| 3 | `evaluated_to_adapter_draft` | R3 | Always |
| 4 | `adapter_draft_to_adapter_dry_run` | R3-R4 | Always |
| 5 | `adapter_dry_run_to_capability_proposed` | R5-R6 | Always |
| 6 | `capability_proposed_to_capability_approved` | R6-R7 | Always |

## Forbidden Transitions

The following transitions are explicitly forbidden and must be rejected by any validation:

| From | To | Reason |
|------|----|--------|
| `registered` (promotion_status) | `capability_approved` (lifecycle_state) | Must pass all 6 gates sequentially |
| `registered` (promotion_status) | `active` (lifecycle_state) | No direct path; requires capability_approved first |
| `candidate` (promotion_status) | `capability_approved` (lifecycle_state) | Must pass gates 2-6 |
| `classified` (lifecycle_state) | `adapter_draft` (lifecycle_state) | Must pass gate 2 (evaluated) first |
| `discovered` (lifecycle_state) | `candidate` (promotion_status) | Must be registered and classified first |
| `rejected` (promotion_status) | Any approved state | Rejection is terminal for this promotion record |
| Any state with `risk_level` = `critical` and `human_gate_passed` = `false` | Any state beyond `classified` | Critical risk resources require explicit human gate |

## R0 Hard Boundary

> **No resource may be executed, enabled, installed, or configured at R0. R0 produces registration records and classification decisions only.**

Concrete implications:

1. No script execution (PowerShell, Python, shell)
2. No MCP server enablement or configuration changes
3. No CodeGraph reindex or database modification
4. No Blackboard write operations beyond registration and decision logging
5. No skill installation or code execution from skills-inbox/
6. No memory file writes (MemoryUpdateRecords are proposal-only)
7. No git operations that modify state (commit, push, reset, clean)
8. No package manager usage (npm, pip, yarn)

R0 is purely a cataloging and decision-support phase. All capability enablement is deferred to R1-R7.
