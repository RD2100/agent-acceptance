# Review — LIVE-DISPATCH-READINESS-REVIEW-A1

**Task ID:** LIVE-DISPATCH-READINESS-REVIEW-A1
**Reviewer:** Agent (automated audit)
**Date:** 2026-06-12
**Head commit at review start:** 7ddb641f

## Readiness Verdict

**NOT_READY_NEEDS_FIXES**

Two issues must be resolved before the system is ready for human authorization of live dispatch:
1. Duplicate conversation_id between dev-frame-writing and dev-frame-opencode (HIGH)
2. Registry capacity exceeded: 11 projects vs. max 10 (MEDIUM)

## Section Results

| Section | Verdict | Blocking? |
|---|---|---|
| 6.1 Registry readiness | PARTIAL_PASS | No |
| 6.2 Binding conflict | **FAIL** | **Yes** |
| 6.3 Dry-run evidence | PASS_WITH_STALE_RISK | No |
| 6.4 Evidence capture | PASS | No |
| 6.5 Hook failure semantics | PASS | No |
| 6.6 Workspace closure | PARTIAL_PASS | No |

## Blocking Issues

| # | Issue | Severity | Required Fix |
|---|---|---|---|
| 1 | Duplicate conversation_id (dev-frame-writing = dev-frame-opencode) | HIGH | Rebind one project to new conversation |
| 2 | Registry capacity exceeded (11 > 10) | MEDIUM | Remove project or raise schema limit |

## Non-Blocking Recommendations

| # | Recommendation | Priority |
|---|---|---|
| 1 | Execute fresh dry-run before live dispatch | HIGH |
| 2 | Clean up 193 untracked worktree entries | MEDIUM |
| 3 | Add test for raw_hook_output_capture | LOW |
| 4 | Archive or commit evidence directories | MEDIUM |

## Safety Assessment

| Constraint | Status |
|---|---|
| No live dispatch executed | PASS |
| No routing files modified | PASS |
| No hook files modified | PASS |
| deny_paths respected | PASS |
| human_required maintained | PASS |

## Evidence Chain

10 evidence items produced. See `_evidence/LIVE-DISPATCH-READINESS-REVIEW-A1/chain-evidence.json`.

## Files Produced

| File | Purpose |
|---|---|
| `docs/agent-runtime/live-dispatch-readiness-review.md` | Full readiness review (10 questions) |
| `docs/agent-runtime/live-dispatch-human-authorization-template.md` | Human authorization template |
| `docs/agent-runtime/live-dispatch-rollback-plan.md` | Rollback plan (4 levels) |
| `_evidence/LIVE-DISPATCH-READINESS-REVIEW-A1/registry-readiness.md` | 6.1 evidence |
| `_evidence/LIVE-DISPATCH-READINESS-REVIEW-A1/binding-conflict-check.md` | 6.2 evidence |
| `_evidence/LIVE-DISPATCH-READINESS-REVIEW-A1/dry-run-evidence-review.md` | 6.3 evidence |
| `_evidence/LIVE-DISPATCH-READINESS-REVIEW-A1/evidence-capture-readiness.md` | 6.4 evidence |
| `_evidence/LIVE-DISPATCH-READINESS-REVIEW-A1/hook-failure-semantics-status.md` | 6.5 evidence |
| `_evidence/LIVE-DISPATCH-READINESS-REVIEW-A1/workspace-closure-status.md` | 6.6 evidence |
| `_evidence/LIVE-DISPATCH-READINESS-REVIEW-A1/deferred-files-register.yaml` | Deferred files |
| `_evidence/LIVE-DISPATCH-READINESS-REVIEW-A1/safety-report.json` | Safety assessment |
| `_evidence/LIVE-DISPATCH-READINESS-REVIEW-A1/chain-evidence.json` | Evidence chain |

## Limitations Stated Plainly

1. **Audit-only:** This review did NOT execute live dispatch. It only inspected existing artifacts and code.
2. **No CDP probing:** Chrome DevTools Protocol was not actively tested during this review. The dry-run evidence is 36h old.
3. **Binding fix not performed:** The duplicate conversation_id was identified but not resolved (out of scope for audit-only review).
4. **Workspace not cleaned:** The 193 untracked entries were documented but not committed or archived (out of scope).
5. **No runtime validation:** Hook pipeline, router, and tab resolver were reviewed by code inspection and existing evidence, not by live execution.
