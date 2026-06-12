# EVIDENCE-CAPTURE-STANDARD-A2 -- Final Execution Report

## Task
Task ID: EVIDENCE-CAPTURE-STANDARD-A2
Generated: 2026-06-12T11:07:40.169909+08:00
Builder version: 1.0.0

## Execution Summary
- Commits in scope: 5 (b474d4b, ceb9ed0, 148c550, 442ad78, c96de98)
- Base: 2d5f902 -> Head: c96de98
- Tests: PASS (1260 passed, 21 warnings in 46.57s)

## Post-Commit Workspace State
Total entries in git status: 187

### Modified tracked files (0)
- (none)

### Untracked files (187)
- NEG-009 fixtures (deny_paths): 17
- Secret scan outputs (deny_list): 6
- Session artifacts (pending commit): 164

## Internal Consistency Verification
All files generated from a single `git status --porcelain` snapshot.
Numbers MUST agree across: git-status-after.txt, deferred-files-register.yaml,
safety-report.json, review.yaml, review.md, final-report.md.

- modified_tracked: 0
- untracked_total: 187
  - neg_009: 17
  - secret_scan: 6
  - session_artifacts: 164
- grand_total: 187
- sum_check: 17 + 6 + 164 = 187 (must equal 187)

## Evidence Pack
- ZIP: D:\agent-acceptance\_evidence/EVIDENCE_PACK_ECS_A2_R5.zip
- Size: 120254 bytes (117.4 KB)
- SHA-256: 80899ed4a1b2cedc5c39bcfb32d11c9c442231fdce18d3ac60047db7d89419d7
- Files: 50

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
