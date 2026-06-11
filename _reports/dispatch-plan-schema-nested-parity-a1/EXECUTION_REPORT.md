# Execution Report: dispatch-plan-schema-nested-parity-a1

verdict: PASS

## Scope

Reduce the accepted P3 mirror-maintenance debt for the local `$defs.task_spec` embedded in `multi-agent-dispatch-plan.schema.json` by adding nested parity tests.

This slice changes tests only. It does not run `opencode`, `D:\dev-frame`, real cross-repo pytest/smoke, live CDP, or paper workflow execution.

## Changed Files

- `tests/test_multi_agent_dispatch_plan.py`
- `_reports/dispatch-plan-schema-nested-parity-a1/EXECUTION_REPORT.md`

## Critical Paths

- `tests/test_multi_agent_dispatch_plan.py::test_plan_schema_task_spec_definition_tracks_nested_contracts`
- `schemas/agent-runtime/multi-agent-dispatch-plan.schema.json`
- `schemas/agent-runtime/task-spec.schema.json`

## What Changed

Added a nested parity regression that compares the embedded dispatch-plan TaskSpec mirror against the core TaskSpec schema for:

- `gate_0.required`
- `gate_0.properties` keys
- `gate_0.sufficiency_decision` enum
- `gate_0.decision` enum
- `gate_0.inventory_evidence.required`
- `gate_0.inventory_evidence.properties` keys
- `conflict_registry.required`
- `conflict_registry.properties` keys
- `conflict_registry.conflict_level` enum
- `security_report.required`
- `security_report.properties` keys

## Tests Run

```powershell
python -m pytest tests\test_multi_agent_dispatch_plan.py tests\test_validate_multi_agent_dispatch_plan.py -q
```

Result: 18 passed.

```powershell
python -m pytest tests\test_validate_multi_agent_dispatch_plan.py tests\test_multi_agent_dispatch_plan.py tests\test_multi_agent_gate0_preflight.py tests\test_conversation_registry.py tests\test_cross_repo_execution_guards.py tests\test_smoke_suite.py -q
```

Result: 101 passed.

```powershell
python scripts\validate_multi_agent_dispatch_plan.py _reports\multi-agent-dispatch-plan-a1\DISPATCH_PLAN.json
```

Result: `valid=true`, `dispatch_status=HUMAN_REQUIRED`, `executed_external_runtime=false`, `assignment_count=6`, `errors=[]`.

```powershell
git diff --check -- tests\test_multi_agent_dispatch_plan.py
```

Result: exit 0.

## Output Summary

- Nested TaskSpec mirror parity is now covered for the high-risk governance subcontracts.
- Current legal dispatch plan remains valid and human-gated.
- No external runtime execution was attempted.

## Artifacts

- `_reports/dispatch-plan-schema-nested-parity-a1/EXECUTION_REPORT.md`
- `_reports/dispatch-plan-schema-nested-parity-rereview-a1/QUALITY_REREVIEW.md`

## Known Gaps

- The test intentionally compares required fields, enum values, and property keys rather than complete schema objects, so description/formatting drift does not fail tests.
- Independent rereview passed with P0/P1/P2=0. The remaining P3 note is that required-array comparisons are order-sensitive even though JSON Schema treats required order as semantically irrelevant.

## Technical Debt Introduced

None. This reduces the previously accepted P3 mirror-maintenance debt.

## Governance Notes

This is a test hardening slice only. It does not change dispatch authorization and does not convert `HUMAN_REQUIRED` into execution readiness.

## Suggested Review Focus

- Confirm the parity test guards meaningful nested contract drift without becoming overly brittle.
- Confirm `HUMAN_REQUIRED` remains a valid plan packet state only.
- Confirm no P0/P1/P2 remains before updating governance records.
