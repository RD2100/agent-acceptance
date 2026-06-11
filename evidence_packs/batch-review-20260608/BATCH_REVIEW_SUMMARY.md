# Batch Review — Post-Automation Evidence Pack

> Generated: 2026-06-07T23:32:53.544282+00:00
> Session: 50+ tasks, 3 repos green

## 1. AI-WORKFLOW-HUB-RESTORE
- Before: 23 failed, monorepo smoke FAIL
- After: 147 passed, monorepo smoke PASS
- Root cause: Two missing modules after restore
  -  in run_governance.py
  -  (entire module)
- Fix: Added missing function + stubs for issue_ledger

## 2. CODEGRAPH-FORK-POOL-FIX
- Before: Worker exited unexpectedly on Windows
- After: 34/37 test files pass, 0 worker errors
- Fix: Added  to vitest.config.ts

## 3. CONTROL-PLANE-BYPASS-FIX
- Before: 3 tests failing with bypass_check_failed
- After: 72 tests passing
- Fix: Created  + 

## Current Health
- agent-acceptance: 269 PASS
- devframe-control-plane: 72 PASS
- dev-frame-opencode: 5/5 smoke
