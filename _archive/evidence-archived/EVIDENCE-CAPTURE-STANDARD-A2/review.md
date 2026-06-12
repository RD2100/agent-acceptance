# EVIDENCE-CAPTURE-STANDARD-A2 Review

## Scope
- Commits: b474d4b, ceb9ed0, 148c550, 442ad78, c96de98
- Base: 2d5f902 -> Head: c96de98
- Generated: 2026-06-12T11:07:40.169909+08:00

## Test Results
- Result: PASS
- Summary: 1260 passed, 21 warnings in 46.57s

## Post-Commit State (all numbers consistent across files)
- Modified tracked: 0
- Untracked: 187
  - NEG-009 (deny_paths): 17
  - Secret scan (deny_list): 6
  - Session artifacts: 164
- Grand total: 187

## Evidence Coverage
- Combined diff (2d5f902..HEAD): included
- Per-commit evidence: 5 commits with git-show + diff-stat
- Deferred files register: covers ALL untracked + modified entries
- Safety report: matches git-status and register exactly

## Internal Consistency
All evidence files use identical numbers from a single git status snapshot:
- modified_tracked: 0
- untracked: 187
- neg_009: 17
- secret_scan: 6
- session_artifacts: 164
- grand_total: 187

## Runtime Negative-Path Evidence
Source: extra/ (9 scenario files)

| # | Scenario | Expected | Actual | Result |
|---|----------|----------|--------|--------|
| 1 | ai guard failure blocks | 0 (correct semantics — blocking stage failure → BLOCKED) | exit_code=0 | PASS |
| 2 | ai guard failure mismatch rejected | nonzero (mismatch/invalid input rejected by validator) | exit_code=1 | PASS |
| 3 | invalid json rejected | nonzero (mismatch/invalid input rejected by validator) | exit_code=1 | PASS |
| 4 | missing ai guard rejected | nonzero (mismatch/invalid input rejected by validator) | exit_code=1 | PASS |
| 5 | missing sadp audit rejected | nonzero (mismatch/invalid input rejected by validator) | exit_code=1 | PASS |
| 6 | null exit code rejected | nonzero (mismatch/invalid input rejected by validator) | exit_code=1 | PASS |
| 7 | pass with warnings forbidden | nonzero (mismatch/invalid input rejected by validator) | exit_code=1 | PASS |
| 8 | sadp audit failure blocks | 0 (correct semantics — blocking stage failure → BLOCKED) | exit_code=0 | PASS |
| 9 | test governance failure advisory | 0 (advisory semantics — failure logged but not blocking) | exit_code=0 | PASS |
