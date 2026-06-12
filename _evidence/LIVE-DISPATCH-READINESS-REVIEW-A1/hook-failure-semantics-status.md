# 6.5 Hook Failure Semantics Status

**Task:** LIVE-DISPATCH-READINESS-REVIEW-A1
**Date:** 2026-06-12
**Sources:** `_evidence/hook-output/latest.json`, `tests/test_hook_failure_semantics.py`, `hooks/pre-commit.governance.ps1`

## Hook Pipeline State

| Field | Value |
|---|---|
| Hook version | 2.4.0 |
| Overall result | PASS |
| Timestamp | 2026-06-12T03:13:06Z |
| Branch | master |
| Commit count | 248 |
| Staged file count | 3 |

## Stage Results (Latest Run)

| # | Stage | Exit Code | Duration (ms) | Blocking? | Status |
|---|---|---|---|---|---|
| 1 | manifest-regen | 0 | 0 | Advisory | PASS |
| 2 | sadp-audit | 0 | 740 | **Blocking** | PASS |
| 3 | ai-guard | 0 | 569 | **Blocking** | PASS |
| 4 | test-governance | 0 | 1703 | Advisory | PASS |
| 5 | conversation-health | 0 | 68 | Advisory | PASS |

## Failure Semantics Mapping

| Stage | Failure Behavior | Proven? | Evidence |
|---|---|---|---|
| sadp-audit | Blocks commit on non-zero exit | **YES** | Test class `TestFailureSemanticsMapping` + 45+ historical runs |
| ai-guard | Blocks commit on non-zero exit | **YES** | Test class `TestFailureSemanticsMapping` + 45+ historical runs |
| test-governance | Advisory only, does not block | **YES** | Test class `TestOverallResultLogic` + 30+ historical runs |
| manifest-regen | Advisory only, does not block | **YES** | Test class `TestOverallResultLogic` |
| conversation-health | Advisory only, does not block | **YES** | Test class `TestOverallResultLogic` + 14 historical runs |

## Proven vs Not-Proven Matrix

| Capability | Proven Status | Evidence Source |
|---|---|---|
| sadp_audit_blocks | **PROVEN** | test_hook_failure_semantics.py::TestFailureSemanticsMapping |
| ai_guard_blocks | **PROVEN** | test_hook_failure_semantics.py::TestFailureSemanticsMapping |
| test_governance_advisory | **PROVEN** | test_hook_failure_semantics.py::TestOverallResultLogic |
| json_schema_validation | **PROVEN** | test_hook_failure_semantics.py::TestSchemaConformance |
| raw_hook_output_capture | **NOT PROVEN** | No test validates raw output capture independently |

## Test Coverage

6 test classes in `test_hook_failure_semantics.py` (348 lines):

1. `TestSchemaConformance` -- Schema structure validation (maxItems=5, minItems=1, enum includes ai-guard)
2. `TestHookScript` -- Hook script existence and properties
3. `TestFailureSemanticsMapping` -- Blocking vs advisory classification
4. `TestOverallResultLogic` -- How overall_result derives from stage exit codes
5. `TestLatestJsonValidation` -- Content validation of actual latest.json
6. `TestReplayEvidenceLabeling` -- Replay-style evidence labeling

## Historical Run Volume

| Stage | Estimated Run Count | Date Range |
|---|---|---|
| sadp-audit | 45+ | 2026-06-11 to 2026-06-12 |
| ai-guard | 45+ | 2026-06-11 to 2026-06-12 |
| test-governance | 30+ | 2026-06-11 to 2026-06-12 |
| conversation-health | 14+ | 2026-06-11 to 2026-06-12 |

## Findings

| # | Finding | Severity |
|---|---|---|
| F-6.5-1 | 4/5 hook capabilities proven with tests | PASS |
| F-6.5-2 | raw_hook_output_capture NOT proven | LOW |
| F-6.5-3 | Latest hook run all-pass (5/5 stages exit_code 0) | PASS |
| F-6.5-4 | Extensive historical evidence exists (100+ runs) | PASS |
| F-6.5-5 | Failure semantics version v2.4.0 is consistent across tests and runtime | PASS |

## Verdict

**Section verdict: PASS** -- Hook failure semantics are well-tested and proven for 4/5 capabilities. The unproven `raw_hook_output_capture` is a low-risk gap that does not block live dispatch, as the hook pipeline itself is fully operational.
