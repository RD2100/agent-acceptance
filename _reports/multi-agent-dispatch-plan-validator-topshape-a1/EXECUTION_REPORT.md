# Execution Report: multi-agent-dispatch-plan-validator-topshape-a1

verdict: PASS

## Scope

Harden the dispatch plan consumer validator so malformed top-level packets fail with structured JSON reports instead of reaching semantic `.get()` calls and crashing.

This slice does not run `opencode`, `D:\dev-frame`, cross-repo pytest/smoke, live CDP, or paper workflow execution.

## Changed Files

- `scripts/validate_multi_agent_dispatch_plan.py`
- `tests/test_validate_multi_agent_dispatch_plan.py`
- `_reports/multi-agent-dispatch-plan-validator-topshape-a1/EXECUTION_REPORT.md`

## Critical Paths

- `validate_multi_agent_dispatch_plan._load_json(...)`
- `validate_multi_agent_dispatch_plan._validate_schema(...)`
- `validate_multi_agent_dispatch_plan.validate_dispatch_plan(...)`
- `tests/test_validate_multi_agent_dispatch_plan.py`

## What Changed

- JSON loading now returns `Any`, because valid JSON can be an array, string, number, or boolean, not only an object.
- Top-level schema validation now runs before semantic validation.
- If schema validation fails, semantic validation is skipped so malformed packets cannot trigger `.get()` crashes in the semantic layer.
- JSON loading now distinguishes a successful JSON `null` parse from file/parse failures, so `null` roots receive schema errors instead of load-failure errors.
- Report fields now handle non-object packets safely:
  - `dispatch_status=None`
  - `executed_external_runtime=None`
  - `assignment_count=0` unless `assignments` is a list
- Added regression tests for:
  - non-object top-level JSON
  - `null` top-level JSON
  - non-object assignment entries
  - CLI JSON reporting for malformed top-level shape

## Tests Run

```powershell
python -m pytest tests\test_validate_multi_agent_dispatch_plan.py -q
```

Result: 9 passed.

```powershell
python -m pytest tests\test_validate_multi_agent_dispatch_plan.py tests\test_multi_agent_dispatch_plan.py tests\test_multi_agent_gate0_preflight.py tests\test_conversation_registry.py tests\test_cross_repo_execution_guards.py tests\test_smoke_suite.py -q
```

Result: 96 passed.

```powershell
python -m compileall scripts\validate_multi_agent_dispatch_plan.py scripts\multi_agent_dispatch_plan.py
```

Result: exit 0.

```powershell
python scripts\validate_multi_agent_dispatch_plan.py _reports\multi-agent-dispatch-plan-a1\DISPATCH_PLAN.json
```

Result: `valid=true`, `dispatch_status=HUMAN_REQUIRED`, `executed_external_runtime=false`, `assignment_count=6`, `errors=[]`.

## Output Summary

- Malformed top-level packets, including JSON `null`, now produce schema errors in the JSON report.
- Malformed assignment entries now produce schema errors before semantic validation.
- The current dispatch plan remains valid but human-gated.
- No external runtime execution was attempted.

## Artifacts

- `_reports/multi-agent-dispatch-plan-validator-topshape-a1/EXECUTION_REPORT.md`
- `_reports/multi-agent-dispatch-plan-validator-topshape-rereview-a1/QUALITY_REREVIEW.md` -> initial FAILED on P2 JSON `null` sentinel.
- `_reports/multi-agent-dispatch-plan-validator-topshape-rereview-r2-a1/QUALITY_REREVIEW.md` -> PASS after fix, P0/P1/P2=0.

## Known Gaps

- The dispatch-plan JSON Schema still does not use a local `$ref` for embedded TaskSpec. The consumer validator remains the authoritative deep validation path.
- No full repository suite was run; verification was scoped to the multi-agent readiness path.
- Initial independent rereview found a P2 gap for JSON `null` root handling; this report reflects the follow-up fix, expanded tests, and R2 rereview PASS.

## Technical Debt Introduced

None.

## Governance Notes

This closes the previously noted optional malformed-top-level robustness gap. It does not change Gate 0 status, does not authorize `opencode run`, and does not convert `HUMAN_REQUIRED` into executable readiness.

## Review Notes

P0: pass. The validator only reads local JSON and schema files; it does not execute packet content or external runtimes.

P1: pass. Validation remains bounded by packet size and schema iteration; no new expensive loops or subprocesses were added.

P2: pass. Fail-closed behavior is stronger for malformed JSON shapes, and tests cover both new cases.

P3: unchanged. Schema-level embedded TaskSpec `$ref` remains a possible future cleanup, but the consumer validator provides the active safety path.

## Suggested Review Focus

- Confirm schema failures are sufficient to skip semantic validation for malformed top-level shapes.
- Confirm current valid `HUMAN_REQUIRED` dispatch packets remain accepted as plan packets, not execution proof.
- Confirm downstream consumers use `scripts\validate_multi_agent_dispatch_plan.py` rather than only the top-level JSON Schema.
