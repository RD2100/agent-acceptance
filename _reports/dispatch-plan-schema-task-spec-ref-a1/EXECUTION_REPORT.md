# Execution Report: dispatch-plan-schema-task-spec-ref-a1

verdict: PASS

## Scope

Strengthen `multi-agent-dispatch-plan.schema.json` so the top-level dispatch plan schema validates embedded `task_spec` objects against a local TaskSpec definition, instead of accepting any object.

This slice does not run `opencode`, `D:\dev-frame`, real cross-repo pytest/smoke, live CDP, or paper workflow execution.

## Changed Files

- `schemas/agent-runtime/multi-agent-dispatch-plan.schema.json`
- `tests/test_multi_agent_dispatch_plan.py`
- `tests/test_validate_multi_agent_dispatch_plan.py`
- `_reports/dispatch-plan-schema-task-spec-ref-a1/EXECUTION_REPORT.md`

## Critical Paths

- `schemas/agent-runtime/multi-agent-dispatch-plan.schema.json`
- `tests/test_multi_agent_dispatch_plan.py::test_plan_schema_task_spec_definition_tracks_core_task_schema_contract`
- `tests/test_multi_agent_dispatch_plan.py::test_plan_schema_validates_embedded_task_spec_priority`
- `tests/test_validate_multi_agent_dispatch_plan.py::test_validator_rejects_invalid_embedded_task_spec`
- `scripts/validate_multi_agent_dispatch_plan.py`

## What Changed

- Replaced assignment `task_spec: { "type": "object" }` with `"$ref": "#/$defs/task_spec"`.
- Added local `$defs.task_spec` and `$defs.string_array` to make the dispatch plan schema self-contained for core TaskSpec checks.
- Added schema-only regression proving `priority=P9` in an embedded TaskSpec is rejected by the plan schema itself.
- Added parity regression to keep the embedded TaskSpec definition aligned with the core TaskSpec schema for:
  - required fields
  - `priority` enum
  - `status` enum
  - `additionalProperties=false`
- Updated validator test expectations now that invalid embedded TaskSpecs are caught at schema level before semantic validation.

## Tests Run

```powershell
python -m pytest tests\test_multi_agent_dispatch_plan.py tests\test_validate_multi_agent_dispatch_plan.py -q
```

Result: 17 passed.

```powershell
python -m pytest tests\test_validate_multi_agent_dispatch_plan.py tests\test_multi_agent_dispatch_plan.py tests\test_multi_agent_gate0_preflight.py tests\test_conversation_registry.py tests\test_cross_repo_execution_guards.py tests\test_smoke_suite.py -q
```

Result: 100 passed.

```powershell
python scripts\validate_multi_agent_dispatch_plan.py _reports\multi-agent-dispatch-plan-a1\DISPATCH_PLAN.json
```

Result: `valid=true`, `dispatch_status=HUMAN_REQUIRED`, `executed_external_runtime=false`, `assignment_count=6`, `errors=[]`.

```powershell
python -m compileall scripts\multi_agent_dispatch_plan.py scripts\validate_multi_agent_dispatch_plan.py
```

Result: exit 0.

## Output Summary

- Current dispatch plan remains schema-valid and semantically valid as a human-gated plan packet.
- A downstream consumer that validates only `multi-agent-dispatch-plan.schema.json` now catches core embedded TaskSpec enum drift such as `priority=P9`.
- Consumer validator remains the authoritative path for full semantic checks, including recomputed write conflicts and external runtime claims.
- No external runtime execution was attempted.

## Artifacts

- `_reports/dispatch-plan-schema-task-spec-ref-a1/EXECUTION_REPORT.md`
- `_reports/dispatch-plan-schema-task-spec-ref-rereview-a1/QUALITY_REREVIEW.md` -> PASS, P0/P1/P2=0.

## Known Gaps

- The local embedded TaskSpec definition intentionally tracks the current core contract instead of using external schema resolution, because standalone file `$ref` resolution is brittle across consumers.
- Independent rereview accepted this as a P3 mirror-maintenance debt.
- `schemas/agent-runtime/task-spec.schema.json` still contains a UTF-8 BOM; readers in this path use `utf-8-sig`.

## Technical Debt Introduced

P3: Local `$defs.task_spec` mirrors the core TaskSpec schema for self-contained validation. A parity test now guards core required fields and enums, but future TaskSpec schema changes should update both definitions or move to a well-supported schema registry/resolver. Rereview found no P0/P1/P2.

## Governance Notes

This reduces the prior schema-depth risk without changing the human gate. `HUMAN_REQUIRED` remains a valid plan-packet status and does not authorize dispatch execution.

## Suggested Review Focus

- Confirm the schema-only test catches invalid embedded TaskSpec priority without relying on semantic validation.
- Confirm the parity test is enough to prevent dangerous drift in required fields and priority/status enums.
- Confirm downstream guidance still points consumers to `scripts\validate_multi_agent_dispatch_plan.py` for semantic validation.
