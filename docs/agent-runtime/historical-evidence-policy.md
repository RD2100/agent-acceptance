# Historical Evidence Policy -- R2

> Batch R2-B, 2026-05-27
> RD2100 Agent Runtime v2
> Phase: R2 (Evidence Provider Registration)
> Defines how historical evidence from test-frame (and other sources) is classified, handled, and referenced.

---

## R2 Boundary Banner

```
All evidence in R2 is historical. No current evidence exists.
No test has been executed. No report has been generated. No GateResult has been produced by test tools.
All evidence references MUST carry reviewer annotation.
```

---

## 1. Definition

**Historical evidence** = any report, test result, or evidence artifact from a run that occurred before or outside the current Runtime v2 session.

In R2, all evidence is historical. No approved run has been performed. No test has been executed. No aggregator has been invoked. No attribution has produced output. No orchestrator has dispatched a task. Every file in `evidence/`, `reports/`, and `test-results/` was produced before R2 began.

---

## 2. What Historical Evidence CAN Be Used For

| Permitted Use | Description | Example |
|---------------|-------------|---------|
| Context for understanding system state | Understanding what test-frame contains and how it is structured | Reading ARCHITECTURE.md to understand component layout |
| Reference for designing new tests | Using historical test patterns as reference for future test design | Reviewing test fixture JSON structure |
| Input to risk assessment (FMEA/STRIDE) | Historical failure patterns inform risk analysis | "test-frame has a history of flaky tests in module X" |
| Evidence that a capability existed at a point in time | Demonstrating that test-frame had test coverage on a specific date | "as of 2026-04-15, test-frame covered feature Y" |
| Structural awareness | Understanding directory layout, file types, tool configurations | "test-frame uses pytest + playwright + allure" |

---

## 3. What Historical Evidence CANNOT Be Used For

| Prohibited Use | Reason |
|----------------|--------|
| Current pass/fail determination (NOT a GateResult) | Historical results are not current; they do not reflect the current system state |
| Claiming a test "passed today" | No test has been executed today; yesterday's pass is not today's pass |
| Substituting for an approved current run | An approved run with explicit human gate is required for current evidence |
| EvidenceIndex entries marked as "current" | All R2 EvidenceIndex entries must be marked as historical (see Section 6) |
| GateResult evidence without reviewer annotation | Reviewer must annotate any historical evidence before it can support a gate decision |
| Assertions about current test-frame state beyond directory existence | We know directories and filenames exist; we do not know test pass/fail status |
| Treating stale results as verified | Stale results have unknown freshness; they cannot be treated as verified without explicit reviewer action |

---

## 4. Required Metadata

Any historical evidence reference in an EvidenceIndex entry MUST carry the following metadata:

| Field | Type | Required | Description |
|-------|------|:--------:|-------------|
| run_id | string | YES | Source identifier or reference (e.g., "historical-prior-to-r2") |
| timestamp | ISO8601 | YES | When the evidence was originally captured (if known) or the file modification time |
| source | string | YES | Which tool or run produced this evidence (e.g., "pytest", "jest", "allure", "test-frame pre-R2") |
| freshness | enum | YES | Must be one of: `recent`, `stale`, `unknown` (see Section 5) |
| reviewer_annotation | string | YES | Required before any use in a gate decision; explains why historical evidence is relevant |

### Metadata Constraints

- `freshness` must NEVER be `current` in R2 -- no current evidence exists
- `reviewer_annotation` must be populated before the evidence can be referenced in a GateResult
- `timestamp` must be verifiable or explicitly marked as `unverifiable` with justification
- `source` must clearly identify that this is historical evidence, not R2 evidence

---

## 5. Freshness Classification

| Classification | Definition | R2 Default | Condition |
|---------------|------------|:----------:|-----------|
| current | Produced in current session with approved run | **NOT POSSIBLE** | Requires an approved run in R2 or later phase |
| recent | Produced within 7 days, verifiable timestamp | Conditional | Requires verifiable timestamp within 7 days; no R2 evidence qualifies |
| stale | Older than 7 days OR unverifiable timestamp | **YES (default)** | All test-frame artifacts are older than 7 days relative to R2 start |
| unknown | No timestamp available | **YES (fallback)** | If file modification timestamp is untrustworthy or missing |

### R2 Freshness Default

**All evidence in R2 defaults to `stale_or_unknown`.**

No evidence in R2 can be classified as `recent` because no approved run has been performed within 7 days of the R2 session. All pre-existing test-frame artifacts (reports, test-results, evidence) are at least weeks or months old relative to 2026-05-27.

If a file's modification timestamp can be verified (e.g., via git log or file stat), it may be classified as `stale` (older than 7 days). If the timestamp cannot be verified, it defaults to `unknown`.

**Under no circumstances may R2 evidence be classified as `current`.**

---

## 6. Historical Evidence in EvidenceIndex

When historical evidence is referenced in an EvidenceIndex entry, the following rules apply:

### Status Field

| Status | Allowed for Historical? | Conditions |
|--------|:----------------------:|------------|
| collected | YES | Default status for all historical evidence that has been located and recorded |
| verified | CONDITIONAL | Only if reviewer explicitly verifies the evidence is correct and relevant |
| disputed | YES | If the evidence is found to be incorrect, misleading, or outdated |

### Default Status for Historical Evidence

R2 default: **`collected`** (NOT `verified`).

Historical evidence is collected but NOT verified by default. Verification requires an explicit reviewer action. Until the reviewer confirms:
- The evidence is correctly attributed
- The timestamp is accurate (or staleness is acknowledged)
- The evidence is relevant to the current gate decision

...the status remains `collected`.

### Historical Evidence Entry Template

```json
{
  "evidence_id": "ev-hist-r2-001",
  "run_id": "historical-prior-to-r2",
  "artifact_path": "D:\\test-frame\\test-results\\pytest-20260415.xml",
  "artifact_type": "report",
  "collected_at": "2026-05-27T12:00:00Z",
  "status": "collected",
  "notes": "Historical test result from pre-R2 run. Freshness: stale. Source: pytest. Reviewer annotation: pending."
}
```

### Constraints

1. Status must NOT be `verified` unless reviewer explicitly validates
2. Notes field must reference freshness classification
3. Artifact path must point to an existing file (verified before entry)
4. Run ID must be clearly historical (e.g., `historical-prior-to-r2`, not a future run ID)

---

## 7. Historical Evidence in GateResult

When a reviewer produces a GateResult that references historical evidence:

### Requirements

1. The evidence MUST be referenced by `evidence_id` from an EvidenceIndex entry
2. The EvidenceIndex entry MUST have reviewer_annotation populated
3. The GateResult `details` field MUST explain why historical evidence is being used instead of current evidence
4. The GateResult `recommendation` field MUST note the evidence freshness limitation

### Example GateResult with Historical Evidence

```json
{
  "gate_id": "g-r2-001",
  "run_id": "r2-evidence-registration",
  "gate_level": "P1",
  "gate_name": "test-frame: evidence provider registration complete",
  "result": "pass",
  "checked_at": "2026-05-27T12:00:00Z",
  "details": "Historical evidence from test-frame confirms structural existence of 9 components. No test execution in R2. All evidence is stale_or_unknown. Gate passes based on structural verification, not test results.",
  "evidence_ids": ["ev-hist-r2-001", "ev-hist-r2-002"],
  "recommendation": "Proceed to next registration phase. Future approved run required before any current evidence claim."
}
```

---

## 8. Cross-Source Historical Evidence

Historical evidence may come from sources other than test-frame. The same policy applies:

| Source | Historical Evidence Type | R2 Freshness |
|--------|-------------------------|:------------:|
| test-frame (D:\test-frame) | Test results, reports, evidence logs | stale_or_unknown |
| dev-frame (D:\dev-frame) | smoke_report.txt, architecture docs | stale_or_unknown |
| agent-acceptance (D:\agent-acceptance) | Historical run logs, workqueue outputs | stale_or_unknown |
| CodeGraph | Indexed code intelligence data | stale_or_unknown |

All sources default to `stale_or_unknown` unless a verifiable timestamp within 7 days is produced. The same metadata, freshness, and reviewer annotation rules apply uniformly.

---

## Verification

- [x] Historical evidence defined: any artifact from before/outside current R2 session
- [x] 5 permitted uses documented
- [x] 7 prohibited uses documented
- [x] Required metadata: 5 fields (run_id, timestamp, source, freshness, reviewer_annotation)
- [x] Freshness classification: 4 levels with R2 defaults (stale_or_unknown)
- [x] EvidenceIndex rules: default status=collected, NOT verified
- [x] GateResult rules: evidence_ids only, reviewer_annotation required, details must explain historical use
- [x] Cross-source policy: all sources default to stale_or_unknown
- [x] No test-frame execution
- [x] No D:\test-frame modification
- [x] No write to C:\Users\RD
- [x] No commit, push, or destructive git operation

---

## References

- `test-frame-evidence-provider.md` -- R2 evidence provider policy: historical_only, 23 forbidden actions
- `integration-contracts.md` -- Contract 3 (EvidenceIndex), Contract 4 (GateResult)
- `resource-registry.md` -- Resource 3: test-frame (res-testframe-003)
- `test-frame-evidence-map.md` -- Component-to-contract mapping
- `test-frame-attribution-alignment.md` -- Attribution boundary vs GateResult
