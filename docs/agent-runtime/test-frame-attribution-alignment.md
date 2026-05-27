# test-frame Attribution Alignment -- R2

> Batch R2-B, 2026-05-27
> RD2100 Agent Runtime v2
> Phase: R2 (Evidence Provider Registration)
> Defines the boundary between test-frame's attribution module and Runtime v2's GateResult contract.

---

## R2 Boundary Banner

```
Attribution has NEVER been run in Runtime v2.
Attribution output is an EvidenceIndex observation only.
Attribution does NOT decide pass/fail.
Attribution does NOT produce a GateResult.
```

---

## 1. Attribution Boundary

Attribution is the test-frame module that categorizes test failures (crash, assertion, timeout, flake, env error, unknown). In R2, attribution is **forbidden** from execution. This document defines the alignment contract between attribution's output and Runtime v2's GateResult -- for future reference when/if attribution is ever approved to run.

### Core Principle

```
Attribution output -> EvidenceIndex observation -> Reviewer evaluation -> GateResult
                          ^                                                  ^
                    (attribution produces)                            (reviewer produces)
```

Attribution output is an EvidenceIndex observation only. It categorizes failures. It does **NOT** decide pass/fail. It does **NOT** produce a GateResult. The GateResult is produced by the reviewer after evaluating all evidence, including attribution output as one input among many.

### Key Distinction

| Aspect | Attribution | GateResult |
|--------|-------------|------------|
| What it does | Categorizes failures | Decides pass/fail |
| What it produces | EvidenceIndex observation | GateResult record |
| Who consumes it | Reviewer (as one input) | Human reviewer, release pipeline |
| Decision authority | NONE -- advisory only | FULL -- decides gate outcome |
| Runs when | If approved future execution | At reviewer's discretion |
| Contract | Feeds into EvidenceIndex (Contract 3) | Implements GateResult (Contract 4) |

---

## 2. Data Flow (R2 -- No Actual Flow)

In R2, no data flow actually runs. All attribution execution is forbidden. The diagram below documents the conceptual flow for reference:

```
+-------------------------------+
| test-frame historical report  |
| (pre-existing, not generated  |
|  in R2, freshness=stale)      |
+-------------------------------+
              |
              v
+-------------------------------+
| attribution analysis          |
| (NOT RUN in R2 -- forbidden)  |
|                               |
| Future if approved:           |
| categorizes failures into     |
| failure_class buckets         |
+-------------------------------+
              |
              v
+-------------------------------+
| EvidenceIndex observation     |
| (NOT PRODUCED in R2)          |
|                               |
| Fields if ever produced:      |
| - failure_class               |
| - source (attribution)        |
| - timestamp                   |
| - freshness = stale_or_unknown|
| - status = collected          |
|   (NOT verified)              |
+-------------------------------+
              |
              v
+-------------------------------+
| Reviewer evaluates            |
| (HUMAN -- R2)                 |
|                               |
| Reads EvidenceIndex entries   |
| Cross-references other sources|
| Makes independent decision    |
+-------------------------------+
              |
              v
+-------------------------------+
| GateResult                    |
| (produced by REVIEWER,        |
|  NOT by attribution)          |
|                               |
| Fields:                       |
| - gate_id                     |
| - gate_name                   |
| - result (pass/fail/blocked)  |
| - evidence_ids (references)   |
| - details (reviewer rationale)|
+-------------------------------+
```

**R2 Reality**: The attribution box is never entered. The EvidenceIndex box is never populated. The reviewer evaluates historical evidence directly and produces GateResult through the review process. Attribution alignment is NOT VERIFIED because attribution has never been run.

---

## 3. Failure Class Mapping

If attribution were ever approved to run in a future phase, test-frame failure categories would map to Runtime v2 failure_classes as follows:

| test-frame Category | Runtime failure_class | Rationale |
|---------------------|----------------------|-----------|
| crash | BLOCKED | Application or framework crash prevents completion; not a test logic failure |
| assertion_failure | FAILED | Test assertion did not match expected outcome; this IS a test logic failure |
| timeout | BLOCKED | Test did not complete within time limit; execution was blocked, not a logic failure |
| flake | WARNING | Intermittent failure; passes on retry; indicates instability, not a definitive failure |
| env_error | BLOCKED | Environment misconfiguration or missing dependency; cannot proceed |
| unknown | UNVERIFIED | Outcome cannot be determined; requires human investigation before classification |

### Mapping Notes

- **BLOCKED** means execution could not complete; the result is inconclusive, not a pass or fail.
- **FAILED** means execution completed and assertions did not match; this is a definitive failure.
- **WARNING** means a potential issue was detected but does not block the gate.
- **UNVERIFIED** means the outcome cannot be determined without human investigation.

The mapping is **one-directional**: test-frame categories map TO runtime classes. Runtime classes do not map back to test-frame categories. Attribution is a source of evidence; runtime classification is an independent decision.

---

## 4. Anti-Patterns

The following 5 anti-patterns must never occur:

### AP-1: Attribution output directly becoming GateResult

Attribution produces an EvidenceIndex observation. It does not produce a GateResult. A GateResult requires a `gate_id`, `gate_level`, `gate_name`, `result`, and `checked_at` -- none of which attribution can legitimately generate. Taking attribution output and treating it as a GateResult without reviewer evaluation is forbidden.

### AP-2: Attribution auto-signing pass/fail

Attribution categorizes failures; it does not decide pass/fail. Any automated system that takes attribution output and produces a pass/fail decision without human review is violating this boundary. The pass/fail decision is made by the reviewer, not by attribution.

### AP-3: Attribution consuming current test results without approved run

Attribution may only run after an approved test execution. Running attribution on stale historical results without confirming the results are current is misleading and forbidden. In R2, no approved run has occurred, so attribution cannot legitimately consume any results.

### AP-4: Attribution overriding reviewer decision

If a reviewer produces a GateResult with a specific outcome, attribution output cannot be used to override or invalidate that decision. Attribution is advisory input to the reviewer, not an override mechanism. The reviewer's decision is authoritative.

### AP-5: Attribution running without human gate

Attribution is classified as `human_gated` and `forbidden` in R2. It may not be executed, imported, or invoked without explicit human gate approval. Even if a future phase permits attribution execution, every attribution run must be explicitly gated by a human reviewer.

---

## 5. Alignment Status

**NOT ALIGNED.**

Attribution has never been run in Runtime v2. This document defines the alignment contract -- how attribution output would integrate with Runtime v2's GateResult if attribution were ever approved to run. Actual alignment verification requires:

1. An approved attribution run in a future phase
2. EvidenceIndex entries produced by attribution
3. GateResult produced by reviewer, referencing attribution's EvidenceIndex entries
4. Verification that attribution output was advisory only and did not directly become a GateResult
5. Confirmation that all 5 anti-patterns were avoided

Until these conditions are met, attribution alignment status remains: **NOT ALIGNED -- CONTRACT ONLY**.

---

## Verification

- [x] Attribution boundary defined: EvidenceIndex observation only, never GateResult
- [x] Data flow documented with reviewer as the sole GateResult producer
- [x] Failure class mapping: 6 test-frame categories mapped to 4 runtime classes
- [x] 5 anti-patterns enumerated (AP-1 through AP-5)
- [x] Alignment status: NOT ALIGNED -- contract only, requires future verification
- [x] No test-frame execution
- [x] No D:\test-frame modification
- [x] No write to C:\Users\RD
- [x] No commit, push, or destructive git operation

---

## References

- `test-frame-evidence-provider.md` -- R2 evidence provider policy: attribution is forbidden
- `integration-contracts.md` -- Contract 3 (EvidenceIndex), Contract 4 (GateResult)
- `resource-registry.md` -- Resource 3: test-frame (res-testframe-003)
- `test-frame-evidence-map.md` -- Component-to-contract mapping: attribution -> NONE (forbidden)
