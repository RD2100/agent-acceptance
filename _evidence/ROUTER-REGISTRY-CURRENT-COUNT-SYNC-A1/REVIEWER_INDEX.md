# Reviewer Index: ROUTER-REGISTRY-CURRENT-COUNT-SYNC-A1

## Review Focus

Confirm this is a narrow test-governance alignment, not a weakening of router
coverage.

## Changed Files

| File | Purpose |
|---|---|
| `tests/test_router_10_project_stress.py` | Replace stale hard-coded project count with registry-derived count while preserving status checks |
| `tasks/router-registry-current-count-sync-a1.md` | Task scope and gates |
| `.ai/current-task.yaml` | Commit-time write scope |
| `_reports/router-registry-current-count-sync-a1/EXECUTION_REPORT.md` | Human-readable execution summary |
| `_evidence/ROUTER-REGISTRY-CURRENT-COUNT-SYNC-A1/EXECUTION_REPORT.md` | SADP execution evidence |
| `_evidence/ROUTER-REGISTRY-CURRENT-COUNT-SYNC-A1/REVIEWER_INDEX.md` | This review guide |

## Critical Checks

- `total_projects` is still verified against actual registry length.
- Active project identities are still explicitly asserted.
- Required pending identities are still explicitly asserted.
- `devframe-control-plane` is optional because the registry change is currently
  uncommitted in the worktree; when present it must be `pending_binding`.
- The test remains compatible with both the committed 17-project registry and
  the current 18-project dirty registry.

## Suggested Verification

```powershell
python -m pytest tests/test_validate_project_registry_bindings.py tests/test_router_10_project_stress.py -q
git diff --check -- tests/test_router_10_project_stress.py tasks/router-registry-current-count-sync-a1.md .ai/current-task.yaml _reports/router-registry-current-count-sync-a1/EXECUTION_REPORT.md _evidence/ROUTER-REGISTRY-CURRENT-COUNT-SYNC-A1/EXECUTION_REPORT.md _evidence/ROUTER-REGISTRY-CURRENT-COUNT-SYNC-A1/REVIEWER_INDEX.md
```
