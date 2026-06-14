# Reviewer Index: devframe-system-route-a-preflight-a1

## Review Focus

- Confirm `scripts/devframe_system_route_a_preflight.py` is read-only.
- Confirm dirty repositories cannot produce `READY`.
- Confirm target path existence requires human approval before physical
  bootstrap.
- Confirm reports do not claim `devframe-system` is merged.
- Confirm registry migration remains a separate task.

## Critical Paths

- `evaluate_route_a_preflight`
- `probe_repo`
- `probe_target`
- `_git_status_text`
- `_status_counts`

## Tests

- `tests/test_devframe_system_route_a_preflight.py`

## Generated Artifacts

- `_reports/devframe-system-route-a-preflight-a1/ROUTE_A_PREFLIGHT.json`
- `_reports/devframe-system-route-a-preflight-a1/MERGE_DASHBOARD.md`
- `_reports/devframe-system-route-a-preflight-a1/EXECUTION_REPORT.md`

## Known Gaps

- The validator intentionally does not fetch remote refs. It compares against
  the locally available upstream ref.
- The validator intentionally does not run external repository tests.
- `devframe-system` remains `NOT_MERGED / HUMAN_REQUIRED`.

