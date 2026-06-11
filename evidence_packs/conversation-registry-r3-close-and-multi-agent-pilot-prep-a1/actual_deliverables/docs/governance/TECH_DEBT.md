# Technical Debt

| Date | Module | Debt | Level | Reason | Suggested Follow-Up |
|------|--------|------|-------|--------|---------------------|
| 2026-06-09 | capability inventory | Existing inventory numbering/order and passport totals are inconsistent before CAP-029. | P3 | Historical document drift; this task avoids broad cleanup. | Dedicated inventory normalization task with reviewer signoff. |
| 2026-06-09 | scripts/cross_repo_verify.py / scripts/multi_repo_smoke.py | Cross-repo verify scripts can execute tests/smoke outside the current repo. | P2 | Mitigated in this slice with fail-closed human-gated defaults and targeted tests. | Future authorized runs should require signed/recorded human decision records with exact repo scope. |
| 2026-06-09 | governance docs | `docs/governance/` was absent before this turn. | P3 | Objective requires these logs; initial skeleton now exists. | Continue appending factual records per worker completion. |
