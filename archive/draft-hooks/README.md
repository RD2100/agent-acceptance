# Draft Hooks — Phase 6 Candidates (Inactive)

| Hook | Status | Reason |
|------|--------|--------|
| pre-final.audit.ps1 | Archived 2026-05-30 | Unregistered; fake-green logic migrated to scripts/checks/Test-FakeGreen.ps1 |
| pre-task.audit.ps1 | Archived 2026-05-30 | Dead-blocking: $hadViolation never set to $true |
| pre-tool.audit.ps1 | Archived 2026-05-30 | Dead-blocking: $hadViolation never set to $true |
| skill-intake-scan.audit.ps1 | Archived 2026-05-30 | Dead-blocking: $hadViolation never set to $true |

Restore conditions: implement reachable blocking logic, add negative canary, register in CI.
