# test-frame Evidence Map -- R2

> Batch R2-B, 2026-05-27
> RD2100 Agent Runtime v2
> Phase: R2 (Evidence Provider Registration)
> Maps test-frame components to Runtime v2 contracts.

---

## R2 Boundary Banner

```
R2 = evidence provider registration only.
No test execution. No aggregator. No attribution. No CLI. No orchestrator.
All reports are historical evidence. No current result is produced.
No test-frame component is authorized to produce a GateResult in R2.
```

---

## Component-to-Contract Mapping

| Component | Runtime Contract | Access Mode | Can Produce EvidenceIndex? | Can Produce GateResult? | Current Phase Status | Forbidden Actions | Verification Gaps |
|-----------|-----------------|:-----------:|:--------------------------:|:-----------------------:|:--------------------:|-------------------|-------------------|
| evidence/ | EvidenceIndex | read_only | conditional -- if a prior approved run generated evidence, it can be indexed as historical; no new evidence can be produced in R2 | **no** | historical_only | execute tests, generate new evidence, mark evidence as verified | Directory listing only; no verification of evidence content integrity |
| reports/ | EvidenceIndex | read_only | conditional -- historical reports can be referenced in an EvidenceIndex with status=collected, freshness=stale_or_unknown | **no** | historical_only | execute aggregator, treat historical report as current pass, generate new reports | No current report verification; all reports are pre-existing artifacts |
| test-results/ | EvidenceIndex | read_only | conditional -- historical test results can be referenced in EvidenceIndex; no new results can be produced | **no** | historical_only | execute any test runner, modify test results, treat historical result as current | No current test results exist; freshness unverifiable for all artifacts |
| aggregator/ | NONE | forbidden | no -- aggregator is forbidden from execution; it cannot produce or reference any EvidenceIndex entry | **no** | forbidden | execute, import, call any function, consume test results, generate aggregated reports | Aggregator has never been invoked in this runtime; no contract mapping exists |
| attribution/ | NONE | forbidden | no -- attribution is forbidden from execution; it cannot produce any EvidenceIndex entry | **no** | forbidden | execute, import, call any function, produce GateResult, auto-sign pass/fail, categorize without human gate | Attribution has never been invoked in this runtime; no contract mapping exists |
| cli/ | NONE | forbidden | no -- CLI is forbidden from execution; it cannot trigger any EvidenceIndex production | **no** | forbidden | execute, trigger any command, invoke any test runner or aggregator | CLI commands have never been issued in this runtime; no contract mapping exists |
| orchestrator/ | NONE | forbidden | no -- orchestrator is forbidden from execution; it cannot schedule or dispatch any task | **no** | forbidden | execute, schedule, dispatch any task, invoke any downstream component | Orchestrator has never been invoked in this runtime; no contract mapping exists |
| tests/ | EvidenceIndex | metadata_only | conditional -- test definitions can be referenced as structural evidence; no test execution is permitted | **no** | historical_only | execute any test (pytest, npm test, playwright), treat test source as evidence of passing | Test source code exists but has never been executed in this runtime |
| config/ | EvidenceIndex | metadata_only | conditional -- configuration files can be referenced as structural evidence; configuration cannot be modified | **no** | historical_only | modify configuration, install dependencies, change test parameters | Configuration integrity not verified against runtime requirements |

---

## GateResult Prohibition Summary

**All 9 components: can_produce_gate_result = no.**

No test-frame component is authorized to produce a GateResult in R2. All evidence is historical.

GateResult is a verification gate check (Contract 4) that must be produced by a verification gate runner -- not by test-frame, not by attribution, not by aggregator. The reviewer evaluates historical evidence and produces GateResult through the approved review process. Attribution output is an EvidenceIndex observation only; it does not decide pass/fail.

---

## Access Mode Summary

| Access Mode | Components | Count |
|-------------|------------|:-----:|
| read_only | evidence/, reports/, test-results/ | 3 |
| metadata_only | tests/, config/ | 2 |
| forbidden | aggregator/, attribution/, cli/, orchestrator/ | 4 |

---

## Contract Coverage Summary

| Contract | Mapped Components | Notes |
|----------|-------------------|-------|
| EvidenceIndex (Contract 3) | evidence/, reports/, test-results/, tests/, config/ | All mapping is conditional; no current EvidenceIndex entries can be produced |
| GateResult (Contract 4) | NONE | No component is authorized to produce a GateResult |
| ExecutionReport (Contract 5) | NONE | No ExecutionReport can be produced from test-frame in R2 |
| NONE | aggregator/, attribution/, cli/, orchestrator/ | These 4 components have no contract mapping in R2; they are forbidden from all contract participation |

---

## Verification

- [x] 9 of 9 components mapped with contract, access mode, GateResult capability, phase status, forbidden actions, and verification gaps
- [x] 0 of 9 components can produce GateResult
- [x] 4 of 9 components have access_mode=forbidden
- [x] 3 of 9 components have access_mode=read_only
- [x] 2 of 9 components have access_mode=metadata_only
- [x] All components have current_phase_status as historical_only or forbidden (none as active or current_pass)
- [x] Attribution boundary: attribution output is EvidenceIndex observation only, never GateResult
- [x] No test-frame execution
- [x] No D:\test-frame modification
- [x] No write to C:\Users\RD
- [x] No commit, push, or destructive git operation

---

## References

- `test-frame-evidence-provider.md` -- R2 evidence provider policy with 23 forbidden actions
- `integration-contracts.md` -- Contract 3 (EvidenceIndex), Contract 4 (GateResult), Contract 5 (ExecutionReport)
- `resource-registry.md` -- Resource 3: test-frame (res-testframe-003)
