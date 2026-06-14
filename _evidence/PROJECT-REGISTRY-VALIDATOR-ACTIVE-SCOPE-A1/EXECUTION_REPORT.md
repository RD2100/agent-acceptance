# PROJECT-REGISTRY-VALIDATOR-ACTIVE-SCOPE-A1 Execution Report

## Summary

Fixed `scripts/validate_project_registry_bindings.py` so duplicate
conversation validation is scoped to dispatch-active registry projects and
active bindings only.

This preserves suspended historical bindings as audit records while preventing
them from blocking current readiness.

## Files Changed

- `scripts/validate_project_registry_bindings.py`
- `tests/test_validate_project_registry_bindings.py`
- `tests/test_router_10_project_stress.py`
- `.ai/current-task.yaml`
- `tasks/project-registry-validator-active-scope-a1.md`
- `_evidence/PROJECT-REGISTRY-VALIDATOR-ACTIVE-SCOPE-A1/EXECUTION_REPORT.md`
- `_evidence/PROJECT-REGISTRY-VALIDATOR-ACTIVE-SCOPE-A1/REVIEWER_INDEX.md`
- `_evidence/PROJECT-REGISTRY-VALIDATOR-ACTIVE-SCOPE-A1/CONFLICT_REGISTRY.json`

## Change Details

- Rule 8 now checks duplicate conversation IDs only for:
  - registry projects with `binding_status == "active"`
  - bindings with `binding_status == "active"`
- Suspended registry projects now print `suspended -> NO AUTO-SUBMIT -> SAFE`.
- Added tests proving:
  - suspended project duplicates are non-blocking
  - paused binding duplicates are non-blocking
  - duplicate active conversations still fail
- Updated router stress test constants to the current 17-project registry.

## Verification

1. `python -m pytest tests\test_validate_project_registry_bindings.py -q`
   - Result: PASS
   - `3 passed`

2. `python scripts\validate_project_registry_bindings.py`
   - Result: PASS
   - `RESULT: 8/8 rules passed, 0 failed`
   - `devframe-system: pending_binding -> NO AUTO-SUBMIT -> SAFE`
   - `dev-frame-writing: suspended -> NO AUTO-SUBMIT -> SAFE`

3. `python -m pytest tests\test_router_10_project_stress.py tests\test_multi_project_isolation.py tests\test_dry_run_dispatch_v2.py -q`
   - Result: PASS
   - `89 passed`

4. `python -m pytest tests\test_validate_project_registry_bindings.py tests\test_conversation_registry.py -q`
   - Result: PASS
   - `52 passed`

5. `python -m pytest tests\ -q`
   - Result: PASS
   - `1416 passed, 21 warnings`
   - Warnings are existing `PytestReturnNotNoneWarning` items in framework and paper contract tests.

## Runtime Boundaries

- No external runtime was executed.
- No `opencode run` was executed.
- No control-plane process was started.
- No test-frame runtime command was executed.
- Paper workflow remains paused.

## Verdict

PASS.

The registry validator now matches the intended dispatch-readiness semantics:
only active dispatchable bindings can collide.
