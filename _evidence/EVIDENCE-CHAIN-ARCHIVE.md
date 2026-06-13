# Evidence Chain Archive: GOVERNANCE-READINESS-CONSOLIDATION-A1

**Date:** 2026-06-13
**Status:** NON-CONFORMANT / SUPERSEDED
**Archived by:** EVIDENCE-CHAIN-ARCHIVE task (per round 8 human review)

---

## Archive Decision

The human reviewer (round 8) concluded:

> "建议停止继续修补这些历史工件。将 R1-R4 整体归档为 NON-CONFORMANT / SUPERSEDED 的审计历史，不作为通过证据；另以本次独立人工审核作为结论。功能代码可以进入单独的最终审查，但这条历史证据链不能签署为 PASS。"

## What Is Archived

The following evidence chain is archived as NON-CONFORMANT audit history. It is NOT signed as PASS and must NOT be used as evidence of governance compliance.

| Round | Task ID | Evidence Dir | Verdict | Key Defect |
|-------|---------|-------------|---------|------------|
| R1 | GOVERNANCE-CONSOLIDATION-CORRECTION-R1 | `_evidence/GOVERNANCE-CONSOLIDATION-CORRECTION-R1/` | NON-CONFORMANT | Task runner evidence was post-hoc; R2 verdict missed issues |
| R2 | GOVERNANCE-FINAL-CLOSURE-R1 | `_evidence/GOVERNANCE-FINAL-CLOSURE-R1/` | NON-CONFORMANT | R2 Index never received edit-check in any subsequent round |
| R3 | GOVERNANCE-CLOSURE-ARTIFACTS-R1 | `_evidence/GOVERNANCE-CLOSURE-ARTIFACTS-R1/` | NON-CONFORMANT | False edit-check count; R3 timing claims inaccurate |
| R4 | GOVERNANCE-CLOSURE-R2 | `_evidence/GOVERNANCE-CLOSURE-R2/` | NON-CONFORMANT | Own Index lacked edit-check; verdict before own Report/Index |
| R5 | GOVERNANCE-CLOSURE-R3 | `_evidence/GOVERNANCE-CLOSURE-R3/` | NON-CONFORMANT | Checked wrong Index path; time sequence false; missing verdict file |
| R6 | GOVERNANCE-CLOSURE-R4 | `_evidence/GOVERNANCE-CLOSURE-R4/` | NON-CONFORMANT | Own Report+Index lacked edit-check; declared PASS with unresolved P0 |
| R7 | EVIDENCE-CHAIN-ARCHIVE | `_evidence/EVIDENCE-CHAIN-ARCHIVE/` | **This archive** | N/A — terminal action |

## What Is Accepted

**Functional code changes** (from the original GOVERNANCE-READINESS-CONSOLIDATION-A1 task) are accepted as passing human review independently:

- 1289 tests pass, 0 failures, 21 warnings
- Staleness fixes in 4 test files (dynamic timestamps)
- VM-004 mode-based semantics with correct counts
- Schema status enum expanded (4 → 9 values)
- Capability set accuracy (CAP-028 de-duplication, pilot=14)
- Main execution report: status = pending_review, no premature APPROVED claims

## What Is NOT Accepted

**Governance evidence chain** cannot be signed as PASS due to recursive defects:

1. **Unresolved P0**: CLOSURE-R2/REVIEWER_INDEX.md never received an edit-check in any round
2. **Recurring pattern**: Each correction round introduced the same defect (own artifacts lacking edit-check) in a different location
3. **False-green claims**: Multiple rounds declared PASS while containing unresolved P0/P1 defects
4. **Time sequence dishonesty**: Reports claimed edits occurred after tests when they actually occurred before

## Separation of Concerns

| Component | Status | Action |
|-----------|--------|--------|
| Functional code (source + tests) | ACCEPTED | May proceed to commit after separate human approval |
| Governance evidence chain (R1–R6 artifacts) | NON-CONFORMANT | Archived; not signed; serves as audit history only |
| Main execution report | pending_review | Factual content accepted; governance wrapper archived |

## Lesson Learned

The recursion pattern: each round's agent created its own Report and Index without edit-checking them, then claimed compliance. The root cause is that the enforcer's write_set check allows the evidence output directory (`**` glob) without per-file verification. Fix: the enforcer should require explicit edit-check for EVERY file write, including files in wildcard-matched directories.
