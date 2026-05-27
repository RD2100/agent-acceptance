# test-frame Evidence Provider Policy -- R2

> Batch R2-A, 2026-05-27
> RD2100 Agent Runtime v2
> Phase: R2 (Evidence Provider Registration)
> Status: Evidence Provider Candidate (NOT an active provider)

---

## R2 Boundary Banner

```
R2 = evidence provider registration only.
No test execution. No aggregator. No attribution. No CLI. No orchestrator.
All reports are historical evidence. No current result is produced.
```

---

## Provider Status

**test-frame is registered as a potential evidence source. It is NOT an active provider.**

All evidence from test-frame is classified as **historical** until a future approved run. No test execution has been performed in this runtime. No aggregator has been invoked. No attribution has produced a GateResult. No orchestrator has dispatched a task. No CLI command has been triggered.

The provider is in **candidate** status. It must pass the R2 exit gate (section below) before transition to any future phase that permits execution.

---

## Component Matrix

| Component | Path | R2 Access | R2 Status | Forbidden Actions |
|-----------|------|:---:|:---:|-------------------|
| evidence/ | D:\test-frame\evidence | read_only (directory listing) | historical | read/modify evidence files |
| reports/ | D:\test-frame\reports | read_only (directory listing) | historical | read/modify report files, treat as current |
| test-results/ | D:\test-frame\test-results | read_only (directory listing) | historical | read/modify result files, treat as current |
| aggregator/ | D:\test-frame\aggregator | forbidden | human_gated | execute, import, call any function |
| attribution/ | D:\test-frame\attribution | forbidden | human_gated | execute, import, produce GateResult |
| cli/ | D:\test-frame\cli | forbidden | human_gated | execute, trigger any command |
| orchestrator/ | D:\test-frame\orchestrator | forbidden | human_gated | execute, schedule, dispatch |
| tests/ | D:\test-frame\tests | read_only (directory listing) | historical | execute any test |
| config/ | D:\test-frame\config | read_only (directory listing) | reference | modify configuration |

---

## Evidence Classification

### Historical Evidence

All existing reports/, test-results/, and evidence/ artifacts are classified as **historical context only**. They may be used to understand the test-frame structure and past results, but they carry no currency and cannot serve as gate-check evidence.

| Artifact Path | Type | Status | Notes |
|---------------|------|--------|-------|
| reports/allure-results/ | report | historical | Pre-existing Allure reports |
| reports/jest-results/ | report | historical | Pre-existing Jest reports |
| reports/failure_history/ | report | historical | Historical failure logs |
| test-results/ | result | historical | Pre-existing test result files |
| evidence/ | evidence | historical | Log evidence from past runs |

### Current Evidence

**NONE.** R2 produces no current evidence. No test is executed. No report is generated. No aggregator runs. No attribution produces GateResult.

### Future Evidence

Only after an **approved run** with explicit human gate may test-frame produce current evidence. The conditions are defined in the R2 Exit Gate section below.

---

## Forbidden Actions

The following 15 actions are explicitly forbidden at R2:

1. execute pytest / npm test / playwright
2. execute aggregator
3. execute attribution
4. execute CLI commands
5. execute orchestrator
6. modify D:\test-frame
7. write test results
8. write reports
9. install dependencies
10. treat historical report as current pass
11. allow attribution to produce GateResult
12. trigger external services
13. read .env or credentials in test-frame
14. consume test-frame evidence in GateResult without reviewer approval
15. register test-frame as active provider

### Additional Constraints

16. import or call any aggregator function
17. import or call any attribution function
18. import or call any orchestrator function
19. import or call any CLI function
20. schedule or dispatch any task through orchestrator
21. treat any historical artifact as a gate-check pass
22. produce evidence_index records with status=verified
23. produce gate_result records referencing test-frame evidence as current

---

## Allowed Actions

Only the following 4 actions are permitted at R2:

1. read_directory -- list directory structure and file names
2. read_docs -- read README.md, ARCHITECTURE.md, PIPELINE.md
3. validate_json -- validate JSON fixture structure (no execution)
4. git_status -- run git status --short for baseline awareness

---

## R2 Exit Gate

The following conditions must ALL be satisfied before test-frame can transition from R2 (evidence provider registration) to any future phase (R? -- a phase yet to be defined where test-frame execution might be approved):

| # | Condition | Status |
|---|-----------|:------:|
| 1 | Evidence provider record registered and validated | [] |
| 2 | All 23 forbidden actions enumerated and enforced | [] |
| 3 | execution_policy confirmed as `forbidden` | [] |
| 4 | current_result_policy confirmed as `historical_only` | [] |
| 5 | Human gate acknowledged (human_gate_required = true) | [] |
| 6 | Reviewer has approved the provider registration | [] |
| 7 | Contract mappings (EvidenceIndex, GateResult) documented | [] |
| 8 | Evidence classification (historical/current/future) clear | [] |
| 9 | Component matrix with per-directory access mode complete | [] |
| 10 | Attribution policy constraint documented (no GateResult from R2) | [] |
| 11 | Future run scope defined and approved by reviewer | [] |
| 12 | Rollback plan documented for any future execution | [] |
| 13 | Dry-run scope defined (read-only, no side effects) | [] |
| 14 | No blocking verification gaps remain | [] |
| 15 | Reviewer-approved handoff to next phase | [] |

**Note:** This exit gate defines conditions to move to a future phase (R?), NOT to an existing R3. The R3 slot is occupied by dev-frame Orchestration Adapter. The future phase for test-frame execution must be defined and sequenced separately.

---

## Execution Policy: forbidden

```
EXECUTION_POLICY = forbidden

R2 CANNOT:
  - Execute pytest, npm test, or playwright
  - Execute aggregator, attribution, CLI, or orchestrator
  - Trigger any external service
  - Install any dependency
  - Modify any file in D:\test-frame

R2 CAN:
  - List directories
  - Read documentation (README, ARCHITECTURE, PIPELINE)
  - Validate JSON structure
  - Check git status
```

---

## Current Result Policy: historical_only

```
CURRENT_RESULT_POLICY = historical_only

R2 PRODUCES:
  - Evidence provider registration record
  - Component access matrix
  - Forbidden/allowed action lists
  - Exit gate conditions

R2 DOES NOT PRODUCE:
  - Current test results
  - Current reports
  - EvidenceIndex records marked as verified
  - GateResult records with current evidence
  - Any assertion about test-frame state beyond directory existence
```

---

## Verification

- [x] Evidence provider record schema created (evidence-provider-record.schema.json)
- [x] Policy document created (test-frame-evidence-provider.md)
- [x] execution_policy schema enum: ONLY `forbidden` -- `human_gated` and `dry_run_allowed` rejected by allOf constraint
- [x] current_result_policy schema enum: ONLY `historical_only` -- `current_after_approved_run` and `current_pass` rejected by allOf constraint
- [x] next_phase_blocked: MUST be true
- [x] human_gate_required: MUST be true
- [x] 23 forbidden actions documented (15 primary + 8 additional)
- [x] 4 allowed actions documented
- [x] Component matrix: 9 components with access mode, status, and forbidden actions
- [x] Exit gate: 15 conditions enumerated
- [x] No test-frame execution
- [x] No D:\test-frame modification
- [x] No write to C:\Users\RD
- [x] No commit, push, or destructive git operation
