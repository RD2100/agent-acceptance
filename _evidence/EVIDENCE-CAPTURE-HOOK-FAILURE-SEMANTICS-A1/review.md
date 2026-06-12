# EVIDENCE-CAPTURE-HOOK-FAILURE-SEMANTICS-A1 Review

## Scope
- Commits: 6c47d32
- Base: 20a4aa2 -> Head: 6c47d32
- Generated: 2026-06-11T16:53:12.709157+08:00

## Test Results
- Result: PASS
- Summary: 1070 passed, 21 warnings in 43.73s

## Post-Commit State (all numbers consistent across files)
- Modified tracked: 0
- Untracked: 38
  - NEG-009 (deny_paths): 17
  - Secret scan (deny_list): 5
  - Session artifacts: 16
- Grand total: 38

## Evidence Coverage
- Combined diff (20a4aa2..HEAD): included
- Per-commit evidence: 1 commits with git-show + diff-stat
- Deferred files register: covers ALL untracked + modified entries
- Safety report: matches git-status and register exactly

## Internal Consistency
All evidence files use identical numbers from a single git status snapshot:
- modified_tracked: 0
- untracked: 38
- neg_009: 17
- secret_scan: 5
- session_artifacts: 16
- grand_total: 38
