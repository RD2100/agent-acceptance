# R2 test-frame Negative Tests

> Batch R2-C, 2026-05-27
> RD2100 Agent Runtime v2
> Phase: R2 (Evidence Provider Registration)
> Purpose: Negative test scenarios to verify R2 boundary enforcement.

---

## R2 Boundary Banner

```
All negative tests expect non-pass outcomes (BLOCKED or needs_revision).
No test expects pass. No test asserts test-frame execution is permitted.
Reviewer is the sole gate authority. Attribution is forbidden.
```

---

## Negative Test Scenarios

---

### NEG-R2-001: pytest Executed Against test-frame

- **Scenario**: Agent or tooling executed `pytest` against D:\test-frame\tests during R2 session.
- **Input Report Features**: Claims "test run completed", "X tests passed", or references fresh pytest output.
- **Expected Gate Decision**: **BLOCKED**
- **Expected Findings**: pytest execution artifact detected (.pytest_cache, new test-results, stdout). Violation of forbidden action #1 (execute pytest). R2 execution_policy = forbidden.
- **Related R2 Rule**: `test-frame-evidence-provider.md` Forbidden Actions #1, Execution Policy: forbidden
- **Hard Stop**: true

---

### NEG-R2-002: npm test Executed Against test-frame

- **Scenario**: Agent or tooling executed `npm test` or `npm run test` against D:\test-frame during R2 session.
- **Input Report Features**: Claims "Jest tests passed", "npm test completed", or references Jest output.
- **Expected Gate Decision**: **BLOCKED**
- **Expected Findings**: npm test execution artifact detected (node_modules, Jest cache, jest-results). Violation of forbidden action #1 (execute npm test).
- **Related R2 Rule**: `test-frame-evidence-provider.md` Forbidden Actions #1
- **Hard Stop**: true

---

### NEG-R2-003: playwright Executed Against test-frame

- **Scenario**: Agent or tooling executed `playwright test` or any Playwright-based test runner against D:\test-frame during R2 session.
- **Input Report Features**: Claims "playwright tests passed", "browser tests completed", or references playwright-report.
- **Expected Gate Decision**: **BLOCKED**
- **Expected Findings**: playwright execution artifact detected (playwright-report, test-results from playwright). Violation of forbidden action #1.
- **Related R2 Rule**: `test-frame-evidence-provider.md` Forbidden Actions #1
- **Hard Stop**: true

---

### NEG-R2-004: Aggregator Executed

- **Scenario**: Agent or tooling invoked the aggregator module in D:\test-frame\aggregator during R2 session.
- **Input Report Features**: Claims "aggregated results", "test summary compiled", or references aggregator output.
- **Expected Gate Decision**: **BLOCKED**
- **Expected Findings**: aggregator execution detected. Component has access_mode=forbidden, contract=NONE. Violation of forbidden action #2.
- **Related R2 Rule**: `test-frame-evidence-provider.md` Forbidden Actions #2, `test-frame-evidence-map.md` Component aggregator/ -> forbidden
- **Hard Stop**: true

---

### NEG-R2-005: Attribution Executed

- **Scenario**: Agent or tooling invoked the attribution module in D:\test-frame\attribution during R2 session.
- **Input Report Features**: Claims "failures categorized", "attribution analysis complete", or references attribution output.
- **Expected Gate Decision**: **BLOCKED**
- **Expected Findings**: attribution execution detected. Component has access_mode=forbidden, contract=NONE. Violation of forbidden action #3.
- **Related R2 Rule**: `test-frame-evidence-provider.md` Forbidden Actions #3, `test-frame-attribution-alignment.md` AP-5
- **Hard Stop**: true

---

### NEG-R2-006: CLI Command Executed

- **Scenario**: Agent or tooling invoked any CLI command from D:\test-frame\cli during R2 session.
- **Input Report Features**: Claims "CLI triggered", "command executed", or references CLI output.
- **Expected Gate Decision**: **BLOCKED**
- **Expected Findings**: CLI execution detected. Component has access_mode=forbidden, contract=NONE. Violation of forbidden action #4.
- **Related R2 Rule**: `test-frame-evidence-provider.md` Forbidden Actions #4, `test-frame-evidence-map.md` Component cli/ -> forbidden
- **Hard Stop**: true

---

### NEG-R2-007: Orchestrator Executed

- **Scenario**: Agent or tooling invoked the orchestrator module in D:\test-frame\orchestrator during R2 session.
- **Input Report Features**: Claims "task dispatched", "orchestrator scheduled", or references orchestration output.
- **Expected Gate Decision**: **BLOCKED**
- **Expected Findings**: orchestrator execution detected. Component has access_mode=forbidden, contract=NONE. Violation of forbidden action #5.
- **Related R2 Rule**: `test-frame-evidence-provider.md` Forbidden Actions #5, `test-frame-evidence-map.md` Component orchestrator/ -> forbidden
- **Hard Stop**: true

---

### NEG-R2-008: D:\test-frame Modified

- **Scenario**: Agent or tooling modified any file under D:\test-frame during R2 session (write, edit, delete, or create).
- **Input Report Features**: Claims "configuration updated", "test file edited", or any write to D:\test-frame.
- **Expected Gate Decision**: **BLOCKED**
- **Expected Findings**: File modification detected under D:\test-frame. Violation of forbidden action #6. R2 allows only read_directory, read_docs, validate_json, git_status.
- **Related R2 Rule**: `test-frame-evidence-provider.md` Forbidden Actions #6, Allowed Actions (only 4 permitted)
- **Hard Stop**: true

---

### NEG-R2-009: test-results Modified or Written

- **Scenario**: Agent or tooling wrote new test result files or modified existing ones under D:\test-frame\test-results during R2.
- **Input Report Features**: Claims "test results updated", "results saved", or references new result files.
- **Expected Gate Decision**: **BLOCKED**
- **Expected Findings**: New or modified files under test-results. Violation of forbidden action #7. No test execution permitted.
- **Related R2 Rule**: `test-frame-evidence-provider.md` Forbidden Actions #7, Component Matrix: test-results/ -> read_only
- **Hard Stop**: true

---

### NEG-R2-010: Reports Written

- **Scenario**: Agent or tooling wrote new report files or modified existing ones under D:\test-frame\reports during R2.
- **Input Report Features**: Claims "report generated", "report updated", or references new report files.
- **Expected Gate Decision**: **BLOCKED**
- **Expected Findings**: New or modified files under reports. Violation of forbidden action #8.
- **Related R2 Rule**: `test-frame-evidence-provider.md` Forbidden Actions #8, Component Matrix: reports/ -> read_only
- **Hard Stop**: true

---

### NEG-R2-011: Historical Report Treated as Current Pass

- **Scenario**: Agent or tooling cited a pre-existing historical report as evidence of current passing status (e.g., "test-frame passed based on April 2026 report").
- **Input Report Features**: GateResult uses historical report as evidence of current pass. EvidenceIndex entry has freshness=current for historical artifact. Claims "all tests passing" based on pre-R2 data.
- **Expected Gate Decision**: **needs_revision**
- **Expected Findings**: Historical evidence misclassified as current. Violation of forbidden action #10. Freshness must be stale_or_unknown. Status cannot be verified without reviewer action.
- **Related R2 Rule**: `historical-evidence-policy.md` Section 3 (Prohibited Use: current pass/fail determination), Section 5 (Freshness defaults to stale_or_unknown)
- **Hard Stop**: false

---

### NEG-R2-012: Attribution Directly Signed GateResult

- **Scenario**: Attribution output was consumed as a GateResult without reviewer evaluation. GateResult fields populated from attribution data automatically.
- **Input Report Features**: GateResult with gate_id auto-generated from attribution. result field = pass/fail derived from attribution classification. No reviewer annotation present.
- **Expected Gate Decision**: **needs_revision**
- **Expected Findings**: Attribution produced GateResult directly (anti-pattern AP-1). Violation of attribution boundary: attribution output is EvidenceIndex observation only, never GateResult. Reviewer must produce GateResult.
- **Related R2 Rule**: `test-frame-attribution-alignment.md` Section 1 (Core Principle), Section 4 AP-1, `test-frame-evidence-provider.md` Forbidden Actions #11
- **Hard Stop**: false

---

### NEG-R2-013: Failure Classification Not Mapped to Runtime failure_classes

- **Scenario**: Agent claimed test failures using test-frame's native categories (crash, assertion_failure, etc.) without mapping them to Runtime v2 failure_classes (BLOCKED, FAILED, WARNING, UNVERIFIED).
- **Input Report Features**: GateResult details reference "crash" or "flake" directly. No mapping to BLOCKED/WARNING/F AILED/UNVERIFIED. One-directional mapping contract violated.
- **Expected Gate Decision**: **needs_revision**
- **Expected Findings**: Failure categories not mapped to Runtime v2 contract. test-frame categories are advisory; runtime classification is an independent decision. Mapping is one-directional.
- **Related R2 Rule**: `test-frame-attribution-alignment.md` Section 3 (Failure Class Mapping), Mapping Notes
- **Hard Stop**: false

---

### NEG-R2-014: Unknown Report Freshness Written as Pass

- **Scenario**: EvidenceIndex entry has no freshness field, or freshness is absent/empty, but the entry is treated as supporting a pass decision.
- **Input Report Features**: EvidenceIndex entry missing freshness field. GateResult references this entry as evidence. No reviewer annotation about staleness.
- **Expected Gate Decision**: **needs_revision**
- **Expected Findings**: Missing freshness metadata. Required field per historical-evidence-policy Section 4. Evidence cannot support gate decision without freshness classification and reviewer annotation.
- **Related R2 Rule**: `historical-evidence-policy.md` Section 4 (Required Metadata: freshness is required), Section 6 (default status = collected, NOT verified)
- **Hard Stop**: false

---

### NEG-R2-015: EvidenceIndex Missing source/timestamp/run_id

- **Scenario**: EvidenceIndex entries created without required metadata fields.
- **Input Report Features**: EvidenceIndex entry has no source field. No timestamp in ISO8601 format. No run_id field present. Entry still referenced in GateResult.
- **Expected Gate Decision**: **needs_revision**
- **Expected Findings**: Incomplete EvidenceIndex metadata. All 5 fields required: run_id, timestamp (ISO8601), source, freshness, reviewer_annotation. Violation of historical-evidence-policy Section 4.
- **Related R2 Rule**: `historical-evidence-policy.md` Section 4 (Required Metadata, 5 fields enumerated), Metadata Constraints
- **Hard Stop**: false

---

### NEG-R2-016: test-frame Registered as Active Provider

- **Scenario**: Provider registration record lists test-frame as active provider instead of Evidence Provider Candidate.
- **Input Report Features**: execution_policy = "human_gated" or "dry_run_allowed" instead of "forbidden". current_result_policy = "current_after_approved_run" or "current_pass" instead of "historical_only". next_phase_blocked = false.
- **Expected Gate Decision**: **needs_revision**
- **Expected Findings**: test-frame registered incorrectly as active provider. R2 status is Evidence Provider Candidate only. execution_policy must be "forbidden". current_result_policy must be "historical_only". Violation of forbidden action #15.
- **Related R2 Rule**: `test-frame-evidence-provider.md` Provider Status section, Forbidden Actions #15, Execution Policy: forbidden, Current Result Policy: historical_only
- **Hard Stop**: false

---

### NEG-R2-017: Dependencies Installed (pip/npm)

- **Scenario**: Agent or tooling executed `pip install`, `npm install`, or any dependency installation command during R2.
- **Input Report Features**: Claims "dependencies updated", "packages installed", or references package.json/pyproject.toml updates.
- **Expected Gate Decision**: **BLOCKED**
- **Expected Findings**: Package installation detected. Violation of forbidden action #9. R2 does not permit any dependency installation.
- **Related R2 Rule**: `test-frame-evidence-provider.md` Forbidden Actions #9
- **Hard Stop**: true

---

### NEG-R2-018: External Service Triggered

- **Scenario**: Agent or tooling triggered any external service (API call, webhook, database connection, network request) from test-frame context during R2.
- **Input Report Features**: Claims "service invoked", "external API called", or references network activity.
- **Expected Gate Decision**: **BLOCKED**
- **Expected Findings**: External service invocation detected. Violation of forbidden action #12.
- **Related R2 Rule**: `test-frame-evidence-provider.md` Forbidden Actions #12
- **Hard Stop**: true

---

### NEG-R2-019: ExecutionReport Claimed test-frame Pass

- **Scenario**: Agent produced an ExecutionReport (Contract 5) that claims test-frame passed based on R2 evidence.
- **Input Report Features**: ExecutionReport generated for test-frame. Claims "test-frame tests pass" or "quality gate satisfied". No contract mapping exists for ExecutionReport in R2.
- **Expected Gate Decision**: **needs_revision**
- **Expected Findings**: ExecutionReport produced from test-frame in R2. Per evidence-map, ExecutionReport contract has NO mapped components from test-frame in R2. No current evidence exists to support an ExecutionReport.
- **Related R2 Rule**: `test-frame-evidence-map.md` Contract Coverage Summary: ExecutionReport -> NONE
- **Hard Stop**: false

---

### NEG-R2-020: Reviewer Bypassed (No Approval)

- **Scenario**: GateResult produced without reviewer approval. Evidence consumed directly into gate decision without reviewer_annotation.
- **Input Report Features**: GateResult with no reviewer_annotation on evidence. Evidence_ids reference entries without reviewer annotation populated. GateResult produced by automated system, not reviewer.
- **Expected Gate Decision**: **needs_revision**
- **Expected Findings**: Reviewer bypass detected. Reviewer is the sole GateResult authority. All evidence must carry reviewer_annotation before gate use. Violation of forbidden action #14.
- **Related R2 Rule**: `test-frame-evidence-provider.md` Forbidden Actions #14, `test-frame-attribution-alignment.md` Core Principle, `historical-evidence-policy.md` Section 7 (Requirements for GateResult)
- **Hard Stop**: false

---

### NEG-R2-021: Aggregator Output Treated as GateResult

- **Scenario**: Aggregator output (if hypothetically obtained) was directly consumed as a GateResult without reviewer evaluation.
- **Input Report Features**: GateResult fields populated from aggregator output. result field derived from aggregator summary. No reviewer evaluation step.
- **Expected Gate Decision**: **needs_revision**
- **Expected Findings**: Aggregator output treated as GateResult. Aggregator has NO contract mapping in R2; cannot produce GateResult. Any aggregator output is EvidenceIndex observation only, requiring reviewer evaluation.
- **Related R2 Rule**: `test-frame-evidence-map.md` Component aggregator/: can_produce_gate_result=no, contract=NONE
- **Hard Stop**: false

---

### NEG-R2-022: CLI Command Used to Trigger Test Run

- **Scenario**: Agent used a CLI command (from test-frame or otherwise) to trigger a test execution, passing it off as structural discovery.
- **Input Report Features**: Claims "directory listing" but actually executed a CLI command that ran tests. Arguments to command include test runner flags.
- **Expected Gate Decision**: **BLOCKED**
- **Expected Findings**: CLI command execution detected with test runner invocation. Violation of forbidden actions #4 (execute CLI) and #1 (execute tests).
- **Related R2 Rule**: `test-frame-evidence-provider.md` Forbidden Actions #1, #4
- **Hard Stop**: true

---

### NEG-R2-023: .env or Credentials Read from test-frame

- **Scenario**: Agent read .env file or credentials from D:\test-frame during R2 session.
- **Input Report Features**: References environment variables, credentials, or secrets from test-frame context.
- **Expected Gate Decision**: **BLOCKED**
- **Expected Findings**: Credential access detected. Violation of forbidden action #13. R2 has no authorization to read .env or credentials from test-frame.
- **Related R2 Rule**: `test-frame-evidence-provider.md` Forbidden Actions #13
- **Hard Stop**: true

---

### NEG-R2-024: Current Result Claimed Without Approved Run

- **Scenario**: Agent claimed a current test result (pass or fail) without an approved run having been performed.
- **Input Report Features**: "test-frame tests pass" or "test-frame tests fail" stated as current fact. No approved run ID. No reviewer approval for execution.
- **Expected Gate Decision**: **needs_revision**
- **Expected Findings**: Current result claimed without approved run. R2 has no approved run. All evidence is historical. No current result can be produced.
- **Related R2 Rule**: `test-frame-evidence-provider.md` Current Result Policy: historical_only, `historical-evidence-policy.md` Section 3 (Prohibited Use: Treating stale results as verified)
- **Hard Stop**: false

---

### NEG-R2-025: Orchestrator Scheduled Task Without Approval

- **Scenario**: Agent scheduled or dispatched a task through the orchestrator without human gate approval.
- **Input Report Features**: Claims "task scheduled", "orchestrator dispatched work", or references orchestration plan.
- **Expected Gate Decision**: **BLOCKED**
- **Expected Findings**: Orchestrator task scheduling detected. Violation of forbidden actions #5 and #20. Orchestrator is forbidden from all operations in R2.
- **Related R2 Rule**: `test-frame-evidence-provider.md` Forbidden Actions #5, #20, Component Matrix: orchestrator/ -> forbidden
- **Hard Stop**: true

---

### NEG-R2-026: Attribution Output Consumed Directly by ExecutionReport Without Reviewer

- **Scenario**: Attribution output was fed directly into an ExecutionReport, bypassing the reviewer entirely. No EvidenceIndex intermediate step. No reviewer annotation.
- **Input Report Features**: ExecutionReport details reference attribution categories directly. No evidence_ids from EvidenceIndex. GateResult was not produced by reviewer.
- **Expected Gate Decision**: **needs_revision**
- **Expected Findings**: Attribution-to-ExecutionReport direct pipeline detected. Bypasses the required flow: Attribution -> EvidenceIndex observation -> Reviewer evaluation -> GateResult. No contract mapping exists for either attribution or ExecutionReport in R2.
- **Related R2 Rule**: `test-frame-attribution-alignment.md` Section 2 (Data Flow), `test-frame-evidence-map.md` Contract Coverage: ExecutionReport -> NONE
- **Hard Stop**: false

---

### NEG-R2-027: Historical Evidence Used to Override Reviewer Decision

- **Scenario**: After reviewer produced a GateResult, historical evidence was cited to override or invalidate the reviewer's decision.
- **Input Report Features**: New GateResult or amended GateResult that reverses reviewer's original decision based on historical evidence. Claims "historical data shows reviewer was wrong".
- **Expected Gate Decision**: **needs_revision**
- **Expected Findings**: Reviewer decision override detected (anti-pattern AP-4). Reviewer's decision is authoritative. Attribution/historical evidence is advisory input only, not an override mechanism.
- **Related R2 Rule**: `test-frame-attribution-alignment.md` Section 4 AP-4, `historical-evidence-policy.md` Section 3 (Prohibited Use: GateResult evidence without reviewer annotation)
- **Hard Stop**: false

---

### NEG-R2-028: EvidenceIndex Entry With status=verified Without Reviewer Action

- **Scenario**: EvidenceIndex entry marked as status=verified without explicit reviewer validation step.
- **Input Report Features**: EvidenceIndex record has status="verified". No reviewer_annotation populated. No evidence of reviewer validation.
- **Expected Gate Decision**: **needs_revision**
- **Expected Findings**: Verified status assigned without reviewer action. Default status for historical evidence is "collected", NOT "verified". Verified requires explicit reviewer confirmation per historical-evidence-policy Section 6. Violation of forbidden action #22.
- **Related R2 Rule**: `historical-evidence-policy.md` Section 6 (Status Field: verified is CONDITIONAL), `test-frame-evidence-provider.md` Additional Constraints #22
- **Hard Stop**: false

---

### NEG-R2-029: EvidenceIndex Freshness Set to recent For Pre-R2 Artifacts

- **Scenario**: EvidenceIndex entry for a pre-existing artifact has freshness="recent" despite being older than 7 days relative to R2 start.
- **Input Report Features**: Freshness field = "recent". Timestamp is verifiable but older than 7 days. No approved run within 7 days.
- **Expected Gate Decision**: **needs_revision**
- **Expected Findings**: Freshness misclassified as "recent". All pre-existing test-frame artifacts are at least weeks old relative to 2026-05-27. Maximum allowed freshness is "stale". R2 default is stale_or_unknown.
- **Related R2 Rule**: `historical-evidence-policy.md` Section 5 (Freshness Classification: recent requires verifiable timestamp within 7 days)
- **Hard Stop**: false

---

### NEG-R2-030: GateResult References Evidence Without reviewer_annotation

- **Scenario**: GateResult evidence_ids field references EvidenceIndex entries that do not have reviewer_annotation populated.
- **Input Report Features**: GateResult with evidence_ids array. Corresponding EvidenceIndex entries have reviewer_annotation=null or missing.
- **Expected Gate Decision**: **needs_revision**
- **Expected Findings**: GateResult references unannotated evidence. Per historical-evidence-policy Section 7, EvidenceIndex entry MUST have reviewer_annotation populated before it can be referenced in a GateResult.
- **Related R2 Rule**: `historical-evidence-policy.md` Section 7 (Requirements: EvidenceIndex entry MUST have reviewer_annotation populated)
- **Hard Stop**: false

---

## Summary Matrix

| Test ID | Scenario | Expected Decision | Hard Stop |
|---------|----------|:-----------------:|:---------:|
| NEG-R2-001 | pytest executed | BLOCKED | true |
| NEG-R2-002 | npm test executed | BLOCKED | true |
| NEG-R2-003 | playwright executed | BLOCKED | true |
| NEG-R2-004 | aggregator executed | BLOCKED | true |
| NEG-R2-005 | attribution executed | BLOCKED | true |
| NEG-R2-006 | CLI executed | BLOCKED | true |
| NEG-R2-007 | orchestrator executed | BLOCKED | true |
| NEG-R2-008 | D:\test-frame modified | BLOCKED | true |
| NEG-R2-009 | test-results modified | BLOCKED | true |
| NEG-R2-010 | reports written | BLOCKED | true |
| NEG-R2-011 | historical report -> current pass | needs_revision | false |
| NEG-R2-012 | attribution -> GateResult | needs_revision | false |
| NEG-R2-013 | failure class not mapped | needs_revision | false |
| NEG-R2-014 | unknown freshness -> pass | needs_revision | false |
| NEG-R2-015 | EvidenceIndex missing metadata | needs_revision | false |
| NEG-R2-016 | test-frame active provider | needs_revision | false |
| NEG-R2-017 | dependencies installed | BLOCKED | true |
| NEG-R2-018 | external service triggered | BLOCKED | true |
| NEG-R2-019 | ExecutionReport claimed pass | needs_revision | false |
| NEG-R2-020 | reviewer bypassed | needs_revision | false |
| NEG-R2-021 | aggregator output -> GateResult | needs_revision | false |
| NEG-R2-022 | CLI used to trigger test | BLOCKED | true |
| NEG-R2-023 | .env/credentials read | BLOCKED | true |
| NEG-R2-024 | current result without run | needs_revision | false |
| NEG-R2-025 | orchestrator scheduled | BLOCKED | true |
| NEG-R2-026 | attribution -> ExecutionReport direct | needs_revision | false |
| NEG-R2-027 | historical override reviewer | needs_revision | false |
| NEG-R2-028 | status=verified without reviewer | needs_revision | false |
| NEG-R2-029 | freshness=recent for old artifact | needs_revision | false |
| NEG-R2-030 | GateResult refs unannotated evidence | needs_revision | false |

**Totals**: 30 negative tests, 13 BLOCKED (hard stop), 17 needs_revision, 0 pass.

---

## Verification

- [x] 30 negative test scenarios (>= 25 minimum)
- [x] 0 scenarios with expected_gate_decision=pass
- [x] Hard stop scenarios correctly marked BLOCKED
- [x] All scenarios reference specific R2 policy rules
- [x] Scenarios cover all 4 context documents
- [x] Scenarios cover all 7 forbidden execution types (pytest, npm, playwright, aggregator, attribution, CLI, orchestrator)
- [x] Scenarios cover attribution boundary violations (AP-1, AP-4, AP-5)
- [x] Scenarios cover EvidenceIndex metadata requirements
- [x] Scenarios cover provider status misconfiguration
- [x] Scenarios cover freshness misclassification
- [x] Scenarios cover reviewer bypass
- [x] Scenarios cover historical evidence override
- [x] Scenarios cover GateResult without reviewer_annotation
- [x] No test-frame execution
- [x] No D:\test-frame modification
- [x] No write to C:\Users\RD
- [x] No commit, push, or destructive git operation

---

## References

- `test-frame-evidence-provider.md` -- 23 forbidden actions, 4 allowed actions, execution_policy=forbidden
- `test-frame-evidence-map.md` -- 9 components, 0 can produce GateResult, 4 forbidden
- `test-frame-attribution-alignment.md` -- 5 anti-patterns, attribution boundary, reviewer as sole GateResult producer
- `historical-evidence-policy.md` -- 5 required metadata fields, 4 freshness levels, default stale_or_unknown
- `r2-test-frame-reviewer-checklist.md` -- 10-step review process, Gate Decision Tree with 14 nodes
