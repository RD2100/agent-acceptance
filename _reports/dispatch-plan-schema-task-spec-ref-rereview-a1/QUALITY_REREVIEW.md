# Quality Rereview: dispatch-plan-schema-task-spec-ref-rereview-a1

verdict: PASS

changed files:
- Reviewed main-control changes:
  - `schemas/agent-runtime/multi-agent-dispatch-plan.schema.json`
  - `tests/test_multi_agent_dispatch_plan.py`
  - `tests/test_validate_multi_agent_dispatch_plan.py`
  - `_reports/dispatch-plan-schema-task-spec-ref-a1/EXECUTION_REPORT.md`
- Reviewer artifact written:
  - `_reports/dispatch-plan-schema-task-spec-ref-rereview-a1/QUALITY_REREVIEW.md`

critical paths:
- `schemas/agent-runtime/multi-agent-dispatch-plan.schema.json:225` now validates `assignment.task_spec` with local `"$ref": "#/$defs/task_spec"`.
- `schemas/agent-runtime/multi-agent-dispatch-plan.schema.json:240` defines local `$defs.task_spec`; no external `$ref` resolver is required.
- `schemas/agent-runtime/multi-agent-dispatch-plan.schema.json:256` covers TaskSpec `priority` enum `P0/P1/P2/P3`.
- `schemas/agent-runtime/multi-agent-dispatch-plan.schema.json:280` covers `gate_0` required evidence fields and sufficiency/decision enums.
- `schemas/agent-runtime/multi-agent-dispatch-plan.schema.json:342` covers `conflict_registry` required read/write sets and conflict-level enum.
- `schemas/agent-runtime/multi-agent-dispatch-plan.schema.json:365` covers `security_report` required boolean attestations.
- `tests/test_multi_agent_dispatch_plan.py:39` checks embedded TaskSpec required/enum parity against the core TaskSpec schema.
- `tests/test_multi_agent_dispatch_plan.py:76` is the schema-only `priority=P9` regression.
- `tests/test_validate_multi_agent_dispatch_plan.py:45` verifies consumer CLI rejection of invalid embedded TaskSpec.
- `scripts/validate_multi_agent_dispatch_plan.py:40` and `scripts/validate_multi_agent_dispatch_plan.py:65` run dispatch-plan schema validation before semantic validation.

tests run:
```powershell
$env:PYTHONDONTWRITEBYTECODE='1'; python -m pytest tests\test_multi_agent_dispatch_plan.py tests\test_validate_multi_agent_dispatch_plan.py -q -p no:cacheprovider
```
Result: passed; `17 passed in 1.09s`.

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'; python scripts\validate_multi_agent_dispatch_plan.py _reports\multi-agent-dispatch-plan-a1\DISPATCH_PLAN.json
```
Result: passed; validator returned `valid=true`, `dispatch_status=HUMAN_REQUIRED`, `executed_external_runtime=false`, `assignment_count=6`, `errors=[]`.

output summary:
- PASS: The top-level dispatch plan schema no longer accepts `assignment.task_spec` as an arbitrary object. It now uses the local `$defs.task_spec`.
- PASS: Schema-only validation catches embedded `task_spec.priority = "P9"` through `Draft202012Validator` against `multi-agent-dispatch-plan.schema.json`, before semantic validation.
- PASS: `$defs.task_spec` covers the current core TaskSpec root required fields, `priority` enum, `status` enum, `additionalProperties=false`, and the nested `gate_0`, `conflict_registry`, and `security_report` contracts.
- PASS: No external `$ref` resolution risk was introduced; the embedded TaskSpec validation is self-contained under local `$defs`.
- PASS: The current legal dispatch plan remains valid while preserving `HUMAN_REQUIRED` and `executed_external_runtime=false`.
- PASS: `HUMAN_REQUIRED` validity is correctly a plan-packet validity result, not execution readiness or authorization.
- Findings: P0=0, P1=0, P2=0. P3=1 accepted maintenance debt.

artifacts:
- `_reports/dispatch-plan-schema-task-spec-ref-rereview-a1/QUALITY_REREVIEW.md`
- Upstream execution artifact reviewed: `_reports/dispatch-plan-schema-task-spec-ref-a1/EXECUTION_REPORT.md`

known gaps:
- Forbidden external/runtime checks were not run, per boundary: no opencode, no `D:\dev-frame`, no real cross-repo smoke/pytest, no live CDP, no paper workflow.
- The parity test guards root `required`, `priority` enum, `status` enum, and top-level `additionalProperties=false`; it does not exhaustively compare every nested property under `gate_0`, `conflict_registry`, and `security_report`.
- The local embedded schema is slightly stricter than the current core schema for nested objects because it sets nested `additionalProperties=false`; this does not break the current plan, but future TaskSpec extensions must consciously update or accept dispatch-plan strictness.

technical debt introduced:
- P3: Local `$defs.task_spec` mirrors the core TaskSpec schema to avoid brittle external `$ref` resolution. The existing parity test is enough to prevent the requested core required/enum drift, but nested-shape drift remains a reviewer-maintained mirror debt. This debt is reasonable and documented in the upstream execution report.

governance notes:
- Read-only review boundary was preserved for business code, tests, schema, and governance docs.
- The only reviewer write was this report artifact.
- Current `valid=true` for a `HUMAN_REQUIRED` plan means the packet is structurally and semantically acceptable for human-gated planning; it does not permit dispatch execution.
- No external runtime execution was observed or attempted.

suggested review focus:
- On any future TaskSpec schema change, review `schemas/agent-runtime/multi-agent-dispatch-plan.schema.json` and `schemas/agent-runtime/task-spec.schema.json` together.
- Consider whether nested TaskSpec parity should be expanded if `gate_0`, `conflict_registry`, or `security_report` evolve frequently.
- Keep consumer guidance pointed at `scripts/validate_multi_agent_dispatch_plan.py` for semantic checks such as recomputed write conflicts.

suggested next task:
- Add a small nested-parity regression for `gate_0`, `conflict_registry`, and `security_report` required fields/enums if the project wants to reduce the accepted P3 mirror-maintenance debt.
