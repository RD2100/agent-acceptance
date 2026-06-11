# Governance Risk Register

| Date | Module | Risk | Level | Mitigation | Status |
|------|--------|------|-------|------------|--------|
| 2026-06-09 | devframe-control-plane | Old SADP wording could imply agents may update `D:/dev-frame/ai-workflow-hub/tasks.yaml`. | P1 | SADP 4.1 now marks the mapping as future/reference unless separately human-gated. | mitigated_pending_review |
| 2026-06-09 | dev-frame-opencode | `opencode run` could become an unregistered execution path. | P1 | CAP-029 added as proposed and tool policy blocks execution without human gate. | mitigated_pending_review |
| 2026-06-09 | paper-workflow | Paper tasks could bypass submission adapter using ad-hoc Playwright/GPT scripts. | P1 | Pilot plan and registry scope forbid ad-hoc GPT submission, live CDP, and real paper processing without authorization. | mitigated_pending_review |
| 2026-06-09 | full-suite verification | Repository full suite has known unrelated collection/Windows cleanup failures. | P2 | Report as limitation; use targeted tests for this change and do not claim full-suite pass. | open |
| 2026-06-09 | cross-repo verification scripts | `cross_repo_verify.py` and `multi_repo_smoke.py` could run tests/smoke in sibling repos without a human gate. | P2 | Both scripts now default to `HUMAN_REQUIRED`; tests assert default paths do not call `subprocess.run`. | mitigated_pending_review |
