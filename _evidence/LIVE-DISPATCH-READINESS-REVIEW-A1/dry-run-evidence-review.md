# 6.3 Dry-Run Evidence Review

**Task:** LIVE-DISPATCH-READINESS-REVIEW-A1
**Date:** 2026-06-12
**Source:** `_evidence/SHARED-CDP-GPT-REVIEW-DRY-RUN-2-A1/DRY_RUN_DISPATCH_10.json`

## Dry-Run Report Metadata

| Field | Value |
|---|---|
| report_id | DRY_RUN_DISPATCH_10 |
| phase | MULTI-PROJECT-GPT-REVIEW-DRY-RUN-10-A1 |
| generated_at | 2026-06-11T00:01:04Z |
| sent | false (dry-run only) |
| Age at review | ~36 hours |

## Dispatch Classification Results

| # | Project | Classification | Dispatchable | Root Cause |
|---|---|---|---|---|
| 1 | tripmark | dispatchable | **true** | Exact tab match, packet fully built |
| 2 | agent-acceptance | human_required_tab_unresolved | false | Binding active but tab not found in Chrome CDP |
| 3 | project-beta | non_dispatchable_pending | false | pending_manual_binding |
| 4 | project-gamma | non_dispatchable_pending | false | pending_manual_binding |
| 5 | project-delta | non_dispatchable_pending | false | pending_manual_binding |
| 6 | project-epsilon | non_dispatchable_pending | false | pending_manual_binding |
| 7 | project-zeta | non_dispatchable_pending | false | pending_manual_binding |
| 8 | project-eta | non_dispatchable_pending | false | pending_manual_binding |
| 9 | project-theta | non_dispatchable_pending | false | pending_manual_binding |
| 10 | project-iota | non_dispatchable_pending | false | pending_manual_binding |

## Summary Statistics

| Metric | Value |
|---|---|
| Total projects | 10 |
| Dispatchable | 1 (10%) |
| Human required (tab unresolved) | 1 (10%) |
| Non-dispatchable pending | 8 (80%) |
| Collisions | 0 |

## Architecture Validation

The dry-run demonstrates that the shared-CDP architecture functions correctly:

- **Packet construction:** Complete for dispatchable project (tripmark) with target_id, conversation_id, chat_url, and capture_policy all resolved.
- **Fail-closed behavior:** agent-acceptance correctly classified as `human_required_tab_unresolved` when its tab was not found -- no fallback to active/last tab.
- **Pending handling:** 8 projects correctly classified as `non_dispatchable_pending` with clear root cause.
- **No collisions:** Zero ambiguous-tab or duplicate-target scenarios.

## Staleness Assessment

| Criterion | Status |
|---|---|
| Dry-run age | 36h (MEDIUM stale risk) |
| Registry changes since dry-run | dev-frame-opencode added after dry-run |
| Chrome state | Unknown (CDP not probed during review) |
| Re-run recommended | Yes, before live dispatch |

## Findings

| # | Finding | Severity |
|---|---|---|
| F-6.3-1 | Dry-run proves packet construction works for bound projects | PASS |
| F-6.3-2 | Only 1/10 projects dispatchable (tripmark) | INFO |
| F-6.3-3 | Dry-run is 36h old; registry has changed since | MEDIUM |
| F-6.3-4 | Fail-closed semantics verified in dry-run | PASS |
| F-6.3-5 | No collision or ambiguous target scenarios | PASS |

## Verdict

**Section verdict: PASS_WITH_STALE_RISK** -- The dry-run evidence demonstrates correct architecture behavior. The 36h staleness is a medium risk; a fresh dry-run should be executed before live dispatch authorization.
