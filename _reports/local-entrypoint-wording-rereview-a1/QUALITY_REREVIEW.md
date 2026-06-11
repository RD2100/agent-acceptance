verdict: PASS

changed files:
- Reviewed prior slice changes:
  - `scripts/smoke_suite.py`
  - `scripts/pre_push_verify.py`
  - `scripts/run_demo.py`
  - `tests/test_smoke_suite.py`
  - `docs/governance/RISK_REGISTER.md`
  - `docs/governance/VERIFY_MATRIX.md`
  - `docs/governance/HANDOFF.md`
  - `_reports/local-entrypoint-presence-only-a1/EXECUTION_REPORT.md`
- This rereview wrote:
  - `_reports/local-entrypoint-wording-rereview-a1/QUALITY_REREVIEW.md`

critical paths:
- `scripts/smoke_suite.py`: `external_runtime_presence_check(...)` returns `scope=presence_only`, `executed=false`, and `human_gate_required_for_execution=true` for external runtime probes.
- `scripts/pre_push_verify.py`: `external_runtime_presence_status(...)` returns the same presence-only metadata; the human-facing output says the control-plane check is presence-only and that no cross-repo tests executed.
- `scripts/run_demo.py`: `external_runtime_presence_command(...)` emits `scope=presence_only executed=false human_gate_required_for_execution=true` from a local `python -c` command, not from a sibling-repo runtime.
- `tests/test_smoke_suite.py`: regression tests assert the local entrypoint helpers/command preserve presence-only, non-execution, and human-gate semantics.

tests run:
- `python -m pytest tests\test_smoke_suite.py tests\test_cross_repo_execution_guards.py -q`
  - result: passed
  - output summary: `26 passed in 0.39s`
- `python -m compileall scripts\smoke_suite.py scripts\pre_push_verify.py scripts\run_demo.py`
  - result: passed
  - output summary: exit code 0, no compile errors

findings:
- P0: none.
- P1: none.
- P2: none.

output summary:
- `smoke_suite.py` structured JSON check entries include `scope: presence_only`, `executed: false`, and `human_gate_required_for_execution: true`, so a path-presence result is not represented as sibling-repo execution.
- `pre_push_verify.py` keeps the external runtime check as a presence-only status object and prints `presence-only; no cross-repo tests executed` instead of cross-repo health/pass wording.
- `run_demo.py` names the step `External Runtime Presence Preflight` and prints `scope=presence_only executed=false human_gate_required_for_execution=true`.
- `docs/governance/HANDOFF.md` explicitly warns not to treat local `Cross-Repo Health`/presence probes as proof that sibling repo tests ran.
- `docs/governance/VERIFY_MATRIX.md` records the local smoke/demo/pre-push requirement as passed with the same target command set.
- `docs/governance/RISK_REGISTER.md` still has `local health entrypoint wording` at `mitigated_pending_review`, which is expected before this rereview.

artifacts:
- `_reports/local-entrypoint-wording-rereview-a1/QUALITY_REREVIEW.md`
- Prior implementation report reviewed: `_reports/local-entrypoint-presence-only-a1/EXECUTION_REPORT.md`

known gaps:
- Full repository tests were not run; governance already tracks full-suite limitations separately.
- No external runtime was executed. This is intentional and required by the review scope.
- The current regression tests cover the production helpers and generated local command, but they do not run the full `main()` functions because those entrypoints launch broader local suites. This is not a blocking P2 for the wording risk because the reviewed production paths now expose or print presence-only/non-execution semantics.

governance recommendation:
- Recommend updating `docs/governance/RISK_REGISTER.md` entry `local health entrypoint wording` from `mitigated_pending_review` to `mitigated_verified`.
- Rationale: current code, tests, handoff language, and target verification support that local health entrypoints no longer present external runtime presence as cross-repo execution/health. No P0/P1/P2 findings remain in this rereview.

reviewer index:
- changed files reviewed: `scripts/smoke_suite.py`, `scripts/pre_push_verify.py`, `scripts/run_demo.py`, `tests/test_smoke_suite.py`, `docs/governance/RISK_REGISTER.md`, `docs/governance/VERIFY_MATRIX.md`, `docs/governance/HANDOFF.md`, `_reports/local-entrypoint-presence-only-a1/EXECUTION_REPORT.md`
- critical code paths: `smoke_suite.external_runtime_presence_check`, `pre_push_verify.external_runtime_presence_status`, `run_demo.external_runtime_presence_command`
- tests run: `python -m pytest tests\test_smoke_suite.py tests\test_cross_repo_execution_guards.py -q`; `python -m compileall scripts\smoke_suite.py scripts\pre_push_verify.py scripts\run_demo.py`
- generated artifacts: `_reports/local-entrypoint-wording-rereview-a1/QUALITY_REREVIEW.md`
- known gaps: no full-suite pass claimed; no sibling repo/runtime execution claimed; no live CDP/opencode/paper workflow execution performed
- suggested review focus: confirm future changes keep local presence checks visibly separate from cross-repo execution evidence and keep human-gate wording attached to any external runtime probe.
