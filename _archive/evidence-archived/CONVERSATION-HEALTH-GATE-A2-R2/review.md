# CONVERSATION-HEALTH-GATE-A2 Review

## Scope
- Commits: 9336d56
- Base: 593d78fb -> Head: 9336d56
- Generated: 2026-06-12T07:12:11.680404+08:00

## Test Results
- Result: PASS
- Summary: 1128 passed, 21 warnings in 45.51s

## Post-Commit State (all numbers consistent across files)
- Modified tracked: 2
  - M evidence/conversation-health/current-snapshot.json
  - M _evidence/conversation-health/latest.json
- Untracked: 112
  - NEG-009 (deny_paths): 17
  - Secret scan (deny_list): 5
  - Session artifacts: 90
- Grand total: 114

## Evidence Coverage
- Combined diff (593d78fb..HEAD): included
- Per-commit evidence: 1 commits with git-show + diff-stat
- Deferred files register: covers ALL untracked + modified entries
- Safety report: matches git-status and register exactly

## Internal Consistency
All evidence files use identical numbers from a single git status snapshot:
- modified_tracked: 2
- untracked: 112
- neg_009: 17
- secret_scan: 5
- session_artifacts: 90
- grand_total: 114

## Runtime Negative-Path Evidence
Source: extra/ (10 scenario files + 1 combined file)

| # | Scenario | Expected | Actual | Result |
|---|----------|----------|--------|--------|
| 1 | access denied records force | exit!=0 | exit=1 | PASS |
| 2 | auth required records human required | exit!=0 | exit=2 | PASS |
| 3 | force handoff blocks submit | exit!=0 | exit=1 | PASS |
| 4 | human required blocks submit | exit!=0 | exit=2 | PASS |
| 5 | latest json written for pre gpt gate | exit!=0 | exit=0 | PASS |
| 6 | legacy helper import failure blocks | exit!=0 | exit=0 | PASS |
| 7 | legacy script post response updates current json | exit!=0 | exit=0 | PASS |
| 8 | missing current json blocks without refresh | exit!=0 | exit=3 | PASS |
| 9 | stale metrics warns or suggests | exit!=0 | exit=0 | PASS |
| 10 | successful metrics refresh updates current json | exit!=0 | exit=0 | PASS |
| — | combined evidence summary | — | — | included |
