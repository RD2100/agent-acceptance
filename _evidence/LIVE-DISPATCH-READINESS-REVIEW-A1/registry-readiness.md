# 6.1 Registry Readiness Check

**Task:** LIVE-DISPATCH-READINESS-REVIEW-A1
**Date:** 2026-06-12
**Source:** `.agent/PROJECT_REGISTRY.json`

## Registry State

| Field | Value |
|---|---|
| schema_version | 2.0.0 |
| awsp_version | 1.3.0 |
| architecture | single_chrome_shared_cdp |
| cdp_mode | shared_single_chrome |
| shared_cdp_port | 9222 |
| total_projects | 11 |

## Project Inventory

| # | project_id | binding_status | registered_at | project_root |
|---|---|---|---|---|
| 1 | agent-acceptance | active | 2026-06-10T16:00:00Z | D:\agent-acceptance |
| 2 | dev-frame-writing | active | 2026-06-10T16:00:00Z | D:\agent-acceptance\_projects\dev-frame-writing |
| 3 | dev-frame-opencode | active | 2026-06-11T01:35:26Z | D:\dev-frame-opencode |
| 4 | tripmark | active | 2026-06-10T16:00:00Z | D:\agent-acceptance\_projects\project-alpha |
| 5 | project-gamma | pending_binding | 2026-06-10T16:00:00Z | D:\agent-acceptance\_projects\project-gamma |
| 6 | project-delta | pending_binding | 2026-06-10T16:00:00Z | D:\agent-acceptance\_projects\project-delta |
| 7 | project-epsilon | pending_binding | 2026-06-10T16:00:00Z | D:\agent-acceptance\_projects\project-epsilon |
| 8 | project-zeta | pending_binding | 2026-06-10T16:00:00Z | D:\agent-acceptance\_projects\project-zeta |
| 9 | project-eta | pending_binding | 2026-06-10T16:00:00Z | D:\agent-acceptance\_projects\project-eta |
| 10 | project-theta | pending_binding | 2026-06-10T16:00:00Z | D:\agent-acceptance\_projects\project-theta |
| 11 | project-iota | pending_binding | 2026-06-10T16:00:00Z | D:\agent-acceptance\_projects\project-iota |

## Findings

### F-6.1-1: Capacity Exceeded
- **Severity:** MEDIUM
- Registry declares `total_projects: 11`. Schema `max_registered_projects` is 10.
- The registry exceeds its declared capacity by 1 project.
- This does not prevent operation but violates the schema constraint.

### F-6.1-2: Active vs Pending Ratio
- 4 active projects, 7 pending_binding projects.
- Only active projects are eligible for live dispatch.
- 7 projects registered over 24+ hours ago remain in pending state, indicating slow binding workflow.

### F-6.1-3: Duplicate Conversation ID (see also 6.2)
- dev-frame-writing and dev-frame-opencode share conversation_id `6a297e5f-c9c8-83a8-b413-a8fc414e0e85`.
- This creates an ambiguous dispatch target under shared-CDP tab resolution.

### F-6.1-4: Registry File Integrity
- JSON is well-formed.
- All project_id values are unique.
- All project_root values are distinct paths.
- `updated_at` (2026-06-11T01:35:26Z) is consistent with the most recent registration (dev-frame-opencode).

## Verdict

| Criterion | Status |
|---|---|
| Registry JSON valid | PASS |
| Unique project_ids | PASS |
| Capacity within limit | **FAIL** (11 > 10) |
| All active projects have bindings | PASS |
| No duplicate conversation_ids | **FAIL** (dev-frame-writing = dev-frame-opencode) |
| Stale pending projects (< 48h) | WARN (24-36h old) |

**Section verdict: PARTIAL_PASS** -- registry is functional but has 2 issues (capacity + duplicate conversation_id) that must be resolved before live dispatch.
