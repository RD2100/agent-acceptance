# Execution Report: cross-repo-subprocess-fail-classification-a1

verdict: PASS

## Scope

Close the P2 governance-evidence gap for authorized cross-repo subprocess failures.

This slice does not run real cross-repo pytest/smoke, `opencode`, `D:\dev-frame`, live CDP, or paper workflow. Tests use monkeypatched subprocess calls and valid synthetic authorization records.

## Changed Files

- `scripts/cross_repo_verify.py`
- `scripts/multi_repo_smoke.py`
- `tests/test_cross_repo_execution_guards.py`
- `_reports/cross-repo-subprocess-fail-classification-a1/EXECUTION_REPORT.md`

## Critical Paths

- `cross_repo_verify._run_repo_command(...)`
- `multi_repo_smoke._run_repo_smoke(...)`
- `tests/test_cross_repo_execution_guards.py::test_cross_repo_verify_timeout_is_structured_fail`
- `tests/test_cross_repo_execution_guards.py::test_cross_repo_verify_missing_cwd_is_structured_fail`
- `tests/test_cross_repo_execution_guards.py::test_multi_repo_smoke_timeout_is_structured_fail`
- `tests/test_cross_repo_execution_guards.py::test_multi_repo_smoke_execution_exception_is_structured_fail`

## Tests Run

```powershell
python -m pytest tests\test_cross_repo_execution_guards.py tests\test_smoke_suite.py -q
```

Result: 24 passed.

```powershell
python -m pytest tests\test_multi_agent_dispatch_plan.py tests\test_multi_agent_gate0_preflight.py tests\test_conversation_registry.py tests\test_cross_repo_execution_guards.py tests\test_smoke_suite.py -q
```

Result: 87 passed.

```powershell
python -m compileall scripts\multi_repo_smoke.py scripts\cross_repo_verify.py scripts\multi_agent_dispatch_plan.py scripts\multi_agent_gate0_preflight.py scripts\validate_conversation_registry.py scripts\cross_repo_authorization.py scripts\smoke_suite.py
```

Result: exit 0.

```powershell
python scripts\multi_agent_gate0_preflight.py --output _reports\multi-agent-gate0-preflight-a1\GATE0_PREFLIGHT.json
python scripts\multi_agent_dispatch_plan.py --preflight _reports\multi-agent-gate0-preflight-a1\GATE0_PREFLIGHT.json --output _reports\multi-agent-dispatch-plan-a1\DISPATCH_PLAN.json
```

Result: `GATE0_LASTEXITCODE=2`, `DISPATCH_LASTEXITCODE=2`; summaries: `gate0 HUMAN_REQUIRED False True 1 9`, `dispatch HUMAN_REQUIRED False 6 False False`.

## Output Summary

- Authorized `cross_repo_verify` timeout now returns structured repo result: `status=FAIL`, `exit=null`, `error_type=timeout`, `timeout_seconds=<value>`.
- Authorized `cross_repo_verify` missing cwd now returns `error_type=missing_cwd` and overall `FAIL`.
- Authorized `multi_repo_smoke` timeout now returns `error_type=timeout` and overall `FAIL`.
- Authorized `multi_repo_smoke` generic execution `OSError` now returns `error_type=execution_exception` and overall `FAIL`.
- Existing default mode remains `HUMAN_REQUIRED` and non-executing.

## Artifacts

- `_reports/cross-repo-subprocess-fail-classification-a1/EXECUTION_REPORT.md`

## Known Gaps

- No real external runtime execution was attempted.
- Full repository suite was not claimed; targeted governance/runtime tests were run.

## Technical Debt Introduced

None.

## Governance Notes

This closes the previously recorded P2 evidence-quality gap for timeout, missing cwd, and execution exceptions in the authorized cross-repo execution path.

## Suggested Review Focus

- Confirm exception handling cannot produce overall PASS.
- Confirm the tests exercise authorized execution paths without invoking real external repos.
- Confirm current Gate 0 and dispatch plan remain human-gated.
