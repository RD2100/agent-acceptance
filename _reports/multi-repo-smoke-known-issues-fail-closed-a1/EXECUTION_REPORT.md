# Execution Report: multi-repo-smoke-known-issues-fail-closed-a1

verdict: PASS

## Scope

Fix the P1 fake-green finding from `_reports/multi-agent-quality-review-a1/QUALITY_REVIEW.md`.

The fix is local to authorized smoke result classification. It does not execute `opencode`, `D:\dev-frame`, cross-repo pytest/smoke, live CDP, or paper workflow.

## Changed Files

- `scripts/multi_repo_smoke.py`
- `tests/test_cross_repo_execution_guards.py`
- `tests/test_multi_agent_dispatch_plan.py`
- `_reports/multi-repo-smoke-known-issues-fail-closed-a1/EXECUTION_REPORT.md`

## Critical Paths

- `multi_repo_smoke.run_smoke(...)`
- `tests/test_cross_repo_execution_guards.py::test_multi_repo_smoke_known_issues_do_not_fake_green`
- `tests/test_multi_agent_dispatch_plan.py::test_validate_plan_detects_directory_file_write_conflict`

## Tests Run

```powershell
python -m pytest tests\test_cross_repo_execution_guards.py tests\test_smoke_suite.py tests\test_multi_agent_dispatch_plan.py -q
```

Result: 26 passed.

```powershell
python -m pytest tests\test_multi_agent_dispatch_plan.py tests\test_multi_agent_gate0_preflight.py tests\test_conversation_registry.py tests\test_cross_repo_execution_guards.py tests\test_smoke_suite.py -q
```

Result: 83 passed.

```powershell
python -m compileall scripts\multi_repo_smoke.py scripts\multi_agent_dispatch_plan.py scripts\multi_agent_gate0_preflight.py scripts\validate_conversation_registry.py scripts\cross_repo_authorization.py scripts\cross_repo_verify.py scripts\smoke_suite.py
```

Result: exit 0.

```powershell
python scripts\multi_agent_dispatch_plan.py --preflight _reports\multi-agent-gate0-preflight-a1\GATE0_PREFLIGHT.json --output _reports\multi-agent-dispatch-plan-a1\DISPATCH_PLAN.json
```

Result: `DISPATCH_LASTEXITCODE=2`; artifact summary `HUMAN_REQUIRED False 6 False False`.

## Output Summary

- `KNOWN_ISSUES` can still label a known non-zero repo result, but only true `PASS` statuses count toward overall PASS.
- A valid authorization plus simulated `devframe-control-plane` non-zero now returns exit 1 and `overall=FAIL`.
- The regression test exercises the production `multi_repo_smoke.run_smoke(..., execute=True, authorization_record=...)` path with a valid authorization record and mocked subprocess output.
- Dispatch plan conflict coverage now includes parent-directory vs child-file write overlap.

## Artifacts

- `_reports/multi-repo-smoke-known-issues-fail-closed-a1/EXECUTION_REPORT.md`

## Known Gaps

- Cross-repo subprocess exception/timeout classification remains a P2 improvement area.
- Full repository test suite was not claimed; targeted governance/runtime tests were run.
- Real external runtime execution remains human-gated and was not attempted.

## Technical Debt Introduced

None.

## Governance Notes

This closes the P1 fake-green path identified by Quality-Reviewer. `KNOWN_ISSUES` no longer makes the batch green.

## Suggested Review Focus

- Confirm `all_ok` only accepts `PASS`.
- Confirm the new regression test would have failed before this fix.
- Confirm no external runtime execution was introduced by the test.
