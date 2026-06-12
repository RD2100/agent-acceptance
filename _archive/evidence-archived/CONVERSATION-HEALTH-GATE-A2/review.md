# CONVERSATION-HEALTH-GATE-A2 Review

## Scope
- Commits: 593d78fb
- Base: fbb08f08 -> Head: 593d78fb
- Generated: 2026-06-12T07:00:33.528244+08:00

## Test Results
- Result: PASS
- Summary: 1126 passed, 21 warnings in 45.19s

## Post-Commit State (all numbers consistent across files)
- Modified tracked: 0
- Untracked: 110
  - NEG-009 (deny_paths): 17
  - Secret scan (deny_list): 5
  - Session artifacts: 88
- Grand total: 110

## Evidence Coverage
- Combined diff (fbb08f08..HEAD): included
- Per-commit evidence: 1 commits with git-show + diff-stat
- Deferred files register: covers ALL untracked + modified entries
- Safety report: matches git-status and register exactly

## Internal Consistency
All evidence files use identical numbers from a single git status snapshot:
- modified_tracked: 0
- untracked: 110
- neg_009: 17
- secret_scan: 5
- session_artifacts: 88
- grand_total: 110

## Runtime Negative-Path Evidence
Source: extra/ (8 scenario files + 1 combined file)

| # | Scenario | Expected | Actual | Result |
|---|----------|----------|--------|--------|
| 1 | access denied records force | exit!=0 | exit=1 | PASS |
| 2 | auth required records human required | exit!=0 | exit=2 | PASS |
| 3 | force handoff blocks submit | exit!=0 | exit=1 | PASS |
| 4 | human required blocks submit | exit!=0 | exit=2 | PASS |
| 5 | latest json written for pre gpt gate | exit!=0 | exit=latest=True, snapshot=True | PASS |
| 6 | missing current json blocks without refresh | exit!=0 | exit=3 | PASS |
| 7 | stale metrics warns or suggests | exit!=0 | exit=0 | PASS |
| 8 | successful metrics refresh updates current json | exit!=0 | exit=20 | PASS |
| — | combined evidence summary | — | — | included |
