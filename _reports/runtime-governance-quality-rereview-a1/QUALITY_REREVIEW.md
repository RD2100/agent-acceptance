verdict: PASS

changed files:
- `_reports/runtime-governance-quality-rereview-a1/QUALITY_REREVIEW.md` - this review report only.

critical paths:
- `docs/agent-runtime/tool-policy.md` - external runtime execution policy, human-gated opencode/dev-frame/cross-repo/paper boundaries, and legacy authorization rejection requirement.
- `docs/agent-runtime/capability-inventory.md` - CAP-029 remains proposed and `usable_for_execution=false`.
- `docs/agent-runtime/sub-agent-dispatch-protocol.md` - dev-frame mapping is reference-only unless separately human-gated; reviewer/finalizer gates remain explicit.
- `docs/MULTI_AGENT_MULTI_GPT_PILOT_PLAN.md` - pilot scope includes devframe-control-plane, dev-frame-opencode, and paper-workflow without authorizing execution.
- `docs/governance/RISK_REGISTER.md`, `docs/governance/VERIFY_MATRIX.md`, `docs/governance/HANDOFF.md` - governance state, verification evidence, and "do not claim" boundaries.
- `scripts/cross_repo_verify.py`, `scripts/multi_repo_smoke.py` - cross-repo execution defaults and fail-closed authorization behavior.
- `scripts/multi_agent_gate0_preflight.py`, `scripts/multi_agent_dispatch_plan.py`, `scripts/validate_multi_agent_dispatch_plan.py` - Gate 0, dispatch packet, and consumer-side validation.
- `tests/test_cross_repo_execution_guards.py`, `tests/test_multi_agent_gate0_preflight.py`, `tests/test_multi_agent_dispatch_plan.py`, `tests/test_validate_multi_agent_dispatch_plan.py` - regression coverage for the reviewed gates.

tests run:
- `$env:PYTHONDONTWRITEBYTECODE='1'; python -m pytest -p no:cacheprovider tests\test_cross_repo_execution_guards.py tests\test_multi_agent_gate0_preflight.py tests\test_multi_agent_dispatch_plan.py tests\test_validate_multi_agent_dispatch_plan.py -q`
  - Result: `43 passed in 2.07s`.
- `$env:PYTHONDONTWRITEBYTECODE='1'; python scripts\multi_agent_gate0_preflight.py; Write-Output "LASTEXITCODE=$LASTEXITCODE"`
  - Result: `LASTEXITCODE=2`; `overall=HUMAN_REQUIRED`; `executed_external_runtime=false`; `human_gate_required=true`; current blockers are pending manual binding, pilot agent count, and CAP-029 execution approval.
- `$env:PYTHONDONTWRITEBYTECODE='1'; python scripts\validate_multi_agent_dispatch_plan.py _reports\multi-agent-dispatch-plan-a1\DISPATCH_PLAN.json; Write-Output "LASTEXITCODE=$LASTEXITCODE"`
  - Result: `LASTEXITCODE=0`; `valid=true`; `dispatch_status=HUMAN_REQUIRED`; `executed_external_runtime=false`; `assignment_count=6`; `errors=[]`.

findings:
- No P0 findings.
- No P1 findings.
- No P2 findings.

output summary:
- Fake-green resistance is currently intact for the reviewed paths. `HUMAN_REQUIRED` is preserved as a non-ready state in Gate 0 and dispatch validation output, not converted to `PASS` or `READY`.
- Presence-only / plan-only evidence is not reported as external runtime execution. Gate 0 and dispatch reports explicitly set `executed_external_runtime=false`.
- `KNOWN_ISSUES` in `multi_repo_smoke.py` cannot produce overall green status because overall success requires every repo status to be exactly `PASS`.
- Cross-repo execution is fail-closed by default. `cross_repo_verify.py` and `multi_repo_smoke.py` return `HUMAN_REQUIRED` unless `--execute` is paired with a valid authorization record.
- Legacy lightweight authorization is covered by `tests/test_cross_repo_execution_guards.py`; `authorized=true` without audit fields is rejected without calling `subprocess.run`.
- Paper / WriteLab metadata-only boundaries are not weakened by the reviewed external-runtime docs. The current docs keep paper workflow pilot-only or handoff/governance-only unless separately authorized, and HANDOFF explicitly forbids treating WriteLab handoff/export/download/E2E evidence as real-paper approval.

artifacts:
- `_reports/runtime-governance-quality-rereview-a1/QUALITY_REREVIEW.md`

known gaps:
- This review did not execute opencode, dev-frame, real cross-repo smoke/pytest, live CDP, or paper workflow, per scope.
- This review did not run the repository full suite; targeted local checks only.
- `scripts/cross_repo_authorization.py` was not in the allowed read list, so the shared validator implementation was not directly inspected. Its legacy/expired/unknown-repo behavior was verified through allowed tests and the importing scripts' public behavior.
- Local entrypoint files such as `scripts/smoke_suite.py`, `scripts/pre_push_verify.py`, `scripts/run_demo.py`, and `tests/test_smoke_suite.py` were outside this review's allowed read list. Do not use this report alone to reclassify the `local health entrypoint wording` risk unless accepting the existing VERIFY_MATRIX evidence.
- `docs/governance/PAPER_WORKFLOW_HANDOFF.md` was outside this review's allowed read list. Paper pause conclusions here are based on the allowed tool policy, pilot plan, HANDOFF, and risk/verify docs.

governance recommendation:
- Recommended to move these RISK_REGISTER entries from `mitigated_pending_review` to `mitigated_verified` based on this review:
  - `devframe-control-plane` P1: SADP and tool-policy keep dev-frame mapping/readiness reference-only without a separate human gate.
  - `dev-frame-opencode` P1: CAP-029 is registered but proposed/non-executable; tool-policy gates `opencode run`; current Gate 0 returns `HUMAN_REQUIRED`.
  - `paper-workflow` P1: reviewed runtime docs preserve pilot-only / synthetic-or-sanitized / human-gated boundaries and do not authorize real paper processing.
  - `cross-repo verification scripts` P2: default paths do not execute subprocesses; authorization is required.
  - `cross-repo authorization records` P2: legacy `authorized=true`, expired records, and unknown repo scopes are covered by target tests.
  - `multi-agent pilot startup` P2: current preflight is schema-valid, read-only, and returns `HUMAN_REQUIRED`, not executable readiness.
  - `multi-agent dispatch planning` P2: current dispatch packet is valid but remains `HUMAN_REQUIRED`; consumer validator rejects execution claims, invalid embedded TaskSpecs, stale conflict summaries, and malformed shapes.
- Keep `local health entrypoint wording` as `mitigated_pending_review` unless a reviewer also inspects/runs the out-of-scope local entrypoint files/tests.
- Keep `paper function pause` as `mitigated_pending_review` unless a reviewer also reads `docs/governance/PAPER_WORKFLOW_HANDOFF.md`, or explicitly accepts the existing VERIFY_MATRIX/HANDOFF evidence as sufficient.
- Leave already-open or unrelated risks unchanged: full-suite verification, dirty paper workflow baseline, WriteLab duplication.

reviewer index:
- Changed files: `_reports/runtime-governance-quality-rereview-a1/QUALITY_REREVIEW.md` only.
- Critical code paths reviewed: cross-repo execution guards, multi-repo smoke aggregation, Gate 0 preflight, dispatch plan generation, dispatch plan validation.
- Tests run: 43 targeted tests; Gate 0 CLI probe; dispatch plan validator CLI probe.
- Generated artifacts: this report only.
- Known gaps: no external runtime execution, no full suite, no direct read of `cross_repo_authorization.py`, no direct read of local health entrypoint files, no direct read of `PAPER_WORKFLOW_HANDOFF.md`.
- Suggested review focus: if governance docs are updated after this report, check only the recommended RISK_REGISTER status transitions and ensure no wording turns `HUMAN_REQUIRED` into `PASS`, `READY`, or proof of external execution.
