# Governance Reform — Final Audit Report

> Commit: 35ce5a8 | 2026-05-30 | D:\agent-acceptance

## What Changed

### P0: External Enforcement Points
- Codex `config.toml`: Added `[permissions.ai-dev]` + `[permissions.ai-risky]` profiles
  - ai-dev: workspace write, deny *.env/*.pem/*secret*/*token*, network off
  - ai-risky: extends ai-dev, network on (for deps install)
- Codex `default.rules`: Added forbidden rules (git push --force, git reset --hard, etc.) + prompt rules (npm publish, pip install, etc.)

### P1: Unified Rule Engine
- `tools/ai_guard.py`: Python guard — deny paths, scope check, secret scan, restricted paths
- `.ai/policy.yaml`: Canonical rule source (deny_paths, restricted_paths, secret_patterns)
- `scripts/sadp-audit.ps1`: Integrated ai_guard.py call (Rule 7)
- `@go` SKILL.md: Upgraded to 3-mode orchestrator (@go read/edit/risky), no longer claims "final judge"

### P2: GitHub Gate
- `.github/workflows/ai-guard.yml`: CI runs ai_guard.py on PR/push to main
- Branch protection: Required status check "AI Guard" on master, no force push, no delete

## Verification

| # | Check | Result |
|---|-------|--------|
| 1 | Codex permission profiles | PASS |
| 2 | Codex exec rules | PASS |
| 3 | ai_guard.py runs | PASS |
| 4 | sadp-audit integration | PASS |
| 5 | CI workflow exists | PASS |
| 6 | Branch protection enabled | PASS (AI Guard required) |
| 7 | SKILL.md in both locations | PASS |

## Architecture Shift

Before: Agent self-governs → voluntary audit → paper TaskSpec
After:  Codex sandbox enforces write scope → ai_guard.py checks real diff → CI re-verifies → branch protection blocks merge

@go is now an orchestrator, not a judge.