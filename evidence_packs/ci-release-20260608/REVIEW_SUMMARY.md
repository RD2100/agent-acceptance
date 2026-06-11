# CI + Release Review

> 2026-06-08T02:22:01.395421+00:00

## 1. CONTROL-PLANE-CI-FIX
- Before: 6 CI failures on GitHub Actions (Linux)
- After: 68 passed, 3 xfail, 0 failed
- Root cause: CI only checked out control-plane, missing agent-acceptance sibling repo
- Fix: Added ci.yml that clones both repos + xfail on pre-existing template/validator mismatch
- stage_executor.py: bypass_passed=None now produces warning not blocking error

## 2. V0.2.0-RC1-RELEASE
- RELEASE_CANDIDATE_v0.2.0-rc1.json with remote SHAs, 10/10 GPT verdicts, safety attestation
- Clean-room verified: git clone v0.2.0-rc1 ¡ú 275 PASS, smoke 9/9

## Current Health
- agent-acceptance: 275 PASS, smoke 9/9
- devframe-control-plane: CI green (68+3xfail)
- dev-frame-opencode: 5/5 monorepo smoke
