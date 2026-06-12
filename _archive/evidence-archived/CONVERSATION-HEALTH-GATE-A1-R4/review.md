# CONVERSATION-HEALTH-GATE-A1 Review

## Scope
- Commits: 892d445, 2b52579, dcc31a7, 40e4aba, fbb08f0
- Base: 8ccb446 -> Head: fbb08f0
- Generated: 2026-06-11T22:44:23.773525+08:00

## Test Results
- Result: PASS
- Summary: 1098 passed, 21 warnings in 45.82s

## Post-Commit State (all numbers consistent across files)
- Modified tracked: 0
- Untracked: 107
  - NEG-009 (deny_paths): 17
  - Secret scan (deny_list): 5
  - Session artifacts: 85
- Grand total: 107

## Evidence Coverage
- Combined diff (8ccb446..HEAD): included
- Per-commit evidence: 5 commits with git-show + diff-stat
- Deferred files register: covers ALL untracked + modified entries
- Safety report: matches git-status and register exactly

## Internal Consistency
All evidence files use identical numbers from a single git status snapshot:
- modified_tracked: 0
- untracked: 107
- neg_009: 17
- secret_scan: 5
- session_artifacts: 85
- grand_total: 107

## Runtime Negative-Path Evidence
Source: extra/ (9 scenario files + 1 combined file)

| # | Scenario | Expected | Actual | Result |
|---|----------|----------|--------|--------|
| 1 | composite force | exit!=0 | exit=1 | PASS |
| 2 | invalid json | exit=2 | exit=2 | PASS |
| 3 | manual estimate no force | exit=0 | exit=0 | PASS |
| 4 | message count force cdp | exit!=0 | exit=1 | PASS |
| 5 | missing current json | exit=0 | exit=0 | PASS |
| 6 | nav access denied | exit!=0 | exit=1 | PASS |
| 7 | nav auth required | exit!=0 | exit=1 | PASS |
| 8 | review rounds force | exit!=0 | exit=1 | PASS |
| 9 | stale metrics suggest | exit=0 | exit=0 | PASS |
| — | combined evidence summary | — | — | included |
