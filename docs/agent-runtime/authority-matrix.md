# Authority Matrix — RD2100 Agent Runtime v2

> Phase 3 | 2026-05-30
> Defines WHO can produce WHICH contract under WHAT authority.
> This matrix is machine-enforceable via runtime-compatibility-lock.yaml.

## Core Principle

**Declaration ≠ Authorization.** A frame manifest DECLARES what it can do.
The Authority Matrix (enforced by compatibility lock) DETERMINES what it may do.

## Matrix

| Producer ↓ / Contract → | TaskSpec | RunSpec | EvidenceIndex | GateResult | ExecutionReport |
|--------------------------|:--------:|:-------:|:-------------:|:----------:|:---------------:|
| **agent-acceptance** | produce | produce + consume | produce + consume | produce | produce |
| **dev-frame** | forbidden | candidate_only | historical_only | **forbidden** | forbidden |
| **test-frame** | forbidden | forbidden | historical_observation_only | **forbidden** | forbidden |
| **attribution** | forbidden | forbidden | observation_only | **forbidden** | forbidden |

## Authority Levels

| Level | Meaning | Can Decide Pass/Fail? | Can Auto-Advance Gate? |
|-------|---------|:---------------------:|:----------------------:|
| produce | Full authority to create and sign this contract | Yes (runtime only) | Yes (with reviewer) |
| produce + consume | Can both create and read this contract | Yes (runtime only) | Yes (with reviewer) |
| candidate_only | May produce in future, NOT currently active | No | No |
| historical_only | Can reference historical artifacts only | No | No |
| historical_observation_only | Can observe and categorize, NOT produce evidence | No | No |
| observation_only | Can produce observations for EvidenceIndex only | No | No |
| orbidden | MUST NOT produce this contract under any circumstance | No | No |

## GateResult — The Inviolable Boundary

**External frames MUST NOT produce GateResult.** This is the highest-priority rule.

GateResult is the decision contract. It determines pass/fail/blocked. If an external
frame produces GateResult, it can override human reviewer decisions.

The only legitimate GateResult producer is gent-acceptance (via its verification gates).
Even attribution (which categorizes failures) does not decide pass/fail — its output goes
to EvidenceIndex as an observation, and the reviewer produces GateResult.

### Anti-Pattern: GateResult from External Frame

`	ext
IF external frame produces GateResult
  → BLOCKED at compatibility preflight
  → Even if manifest declares it
  → Even if lock accidentally allows it
  → GateResult authority = forbidden is hard-coded for external frames
`

## EvidenceIndex — Freshness Boundary

| Producer | Max Freshness | Requires |
|----------|:------------:|----------|
| agent-acceptance | current | approved_run_id |
| dev-frame | historical | n/a (historical smoke reports) |
| test-frame | historical | n/a (pre-existing artifacts) |
| attribution | historical | n/a (categorization, not evidence) |

Historical evidence CANNOT be used as current evidence in GateResult.
See integration-contracts.md Contract 3 for freshness field definitions.

## Decision Precedence

When multiple sources disagree, precedence is:

`	ext
1. Human reviewer (overrides all)
2. agent-acceptance Gate 0 checker (runtime authority)
3. Compatibility lock (whitelist)
4. Frame manifest (self-declaration, weakest)
`

## Validation in checker

The check-frame-compat.py script validates:
- GateResult authority MUST be "forbidden" for all external frames
- EvidenceIndex freshness MUST NOT be "current" for external frames
- Manifest execution_policy MUST NOT exceed lock execution_policy
- Manifest access MUST NOT exceed lock max_access
