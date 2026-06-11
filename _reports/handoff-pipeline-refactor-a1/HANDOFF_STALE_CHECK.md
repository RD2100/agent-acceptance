# Handoff Stale Check

- generated_at: 2026-06-08T12:47:13.494683+00:00
- findings: 4

## Findings
- **BOOT_CONTEXT_TEST_COUNT_CONFLICT** (HIGH): BOOT_CONTEXT.md contains conflicting test counts: [65, 232, 247]
- **TEST_COUNT_WITHOUT_FRESH_P0** (MEDIUM): Test count claims exist in handoff/memory/history but no fresh P0 test output was found.
- **MEMORY_FROZEN_REPO_ACTIVE** (MEDIUM): Memory describes paper workflow as frozen, while repo has active paper index/evidence. Treat memory as stale reference.
- **UNVERIFIED_CONVERSATIONAL_CLAIM** (INFO): '296 PASS' is an unverified conversational claim; no local source-of-truth text matched it.
