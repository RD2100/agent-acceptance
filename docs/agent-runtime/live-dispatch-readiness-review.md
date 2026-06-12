# Live Dispatch Readiness Review

**Task ID:** LIVE-DISPATCH-READINESS-REVIEW-A1
**Date:** 2026-06-12
**Reviewer:** Agent (automated audit)
**Mode:** Audit and documentation only -- NO live dispatch executed
**Head commit at start:** 7ddb641f

---

## Readiness Verdict

**NOT_READY_NEEDS_FIXES**

The system demonstrates strong architectural foundations with proven evidence capture, hook enforcement, and fail-closed dispatch semantics. However, two issues must be resolved before human authorization for live dispatch can be responsibly requested:

1. **Duplicate conversation_id** between dev-frame-writing and dev-frame-opencode (HIGH severity) creates a dispatch collision under shared-CDP tab resolution.
2. **Registry capacity exceeded** (11 projects vs. max 10) violates the schema constraint.

Once these are fixed, the system is architecturally ready for limited live dispatch with human authorization.

---

## 10 Readiness Questions

### Q1: Is the project registry valid and complete?

**Partial Pass.** The registry contains 11 well-formed project entries with unique project_ids and distinct project_roots. However, it exceeds the declared `max_registered_projects: 10` capacity. Four projects are active (agent-acceptance, dev-frame-writing, dev-frame-opencode, tripmark) and seven remain in pending_binding state. See `_evidence/LIVE-DISPATCH-READINESS-REVIEW-A1/registry-readiness.md`.

### Q2: Are conversation bindings conflict-free?

**Fail.** Two active projects (dev-frame-writing and dev-frame-opencode) share the identical conversation_id `6a297e5f-c9c8-83a8-b413-a8fc414e0e85`, violating the `one_agent_one_conversation` policy. Under shared-CDP tab resolution, this creates either dispatch collision (if both tabs are open) or silent misdirection (if only one is open). The root project's two agent bindings (reviewer + executor) use distinct conversations and are conflict-free. See `_evidence/LIVE-DISPATCH-READINESS-REVIEW-A1/binding-conflict-check.md`.

### Q3: Has dry-run dispatch been proven?

**Pass with staleness risk.** A dry-run from 2026-06-11T00:01:04Z successfully constructed dispatch packets for 10 projects. One project (tripmark) was fully dispatchable with complete packet resolution. Eight were correctly classified as non-dispatchable (pending binding). One (agent-acceptance) was correctly classified as human_required (tab unresolved). The fail-closed architecture was validated: no fallback to active/last tab, no speculative dispatch. The dry-run is 36h old; a fresh run is recommended before authorization. See `_evidence/LIVE-DISPATCH-READINESS-REVIEW-A1/dry-run-evidence-review.md`.

### Q4: Is evidence capture ready for live dispatch?

**Pass.** The Evidence Capture Standard (ECS-A2) achieved `accepted_with_limitation` after 5 GPT review rounds. 1260 tests pass with zero failures. The two-pass ZIP builder with content_sha256 is operational. Evidence manifest schema is aligned. All infrastructure components (builder, linter, runtime evidence index) are functional. Four GPT-acknowledged limitations are informational and do not block live dispatch evidence capture. See `_evidence/LIVE-DISPATCH-READINESS-REVIEW-A1/evidence-capture-readiness.md`.

### Q5: Are hook failure semantics proven?

**Pass.** Four of five hook capabilities are proven: sadp_audit_blocks, ai_guard_blocks, test_governance_advisory, and json_schema_validation. The fifth (raw_hook_output_capture) is not independently proven but is low-risk. The latest hook run (v2.4.0, 2026-06-12T03:13:06Z) passed all 5 stages with zero failures. Over 100 historical runs exist as evidence. See `_evidence/LIVE-DISPATCH-READINESS-REVIEW-A1/hook-failure-semantics-status.md`.

### Q6: Is the workspace in acceptable closure state?

**Partial Pass.** The workspace is classified as `dirty_not_closed`. Zero modified tracked files existed at review start (current-task.yaml modification is expected for this task). However, 193 untracked entries accumulate in the worktree, representing ad-hoc scripts, evidence directories, ZIP archives, and test fixtures. A deferred-files-register has been created. Worktree hygiene should be improved before live dispatch but does not affect dispatch safety. See `_evidence/LIVE-DISPATCH-READINESS-REVIEW-A1/workspace-closure-status.md`.

### Q7: What is the minimal live dispatch candidate?

The only project eligible for live dispatch is **tripmark** (project-alpha), which was the sole dispatchable project in the dry-run. Tripmark has an active binding, a resolved tab target, and a complete dispatch packet. All other active projects have binding issues (duplicate conversation_id) or unresolved tab targets.

Minimal live dispatch scope for tripmark:
- Single project dispatch (not multi-project batch)
- Single conversation target
- Shared CDP on localhost:9222
- Human authorization required before send
- Evidence capture mandatory (ECS-A2 compliant)
- Hook pipeline must pass before dispatch commit

### Q8: What is the rollback plan?

See `docs/agent-runtime/live-dispatch-rollback-plan.md` for the full rollback plan. Summary:
- **Immediate rollback:** Disable dispatch by setting `live_dispatch: NOT_AUTHORIZED` in TaskSpec
- **Code rollback:** Git revert to pre-dispatch commit
- **State rollback:** No persistent state changes from dispatch (packets are constructed, not stored)
- **Registry rollback:** Remove tripmark binding if dispatch causes issues
- **Evidence rollback:** All evidence packs are additive; no rollback needed

### Q9: What limitations apply to live dispatch?

1. **Single project only** -- Only tripmark is dispatchable; multi-project dispatch is not ready.
2. **Human authorization required** -- Every dispatch must be explicitly authorized by a human operator.
3. **Fresh dry-run required** -- A new dry-run must be executed within 1 hour before live dispatch.
4. **Binding fix required** -- The dev-frame-writing / dev-frame-opencode duplicate conversation_id must be resolved before those projects can dispatch.
5. **Registry capacity fix required** -- Registry must be brought within the 10-project limit.
6. **Hook pipeline must pass** -- All blocking stages (sadp-audit, ai-guard) must pass before dispatch commit.
7. **Evidence capture mandatory** -- Every live dispatch must produce an ECS-A2 compliant evidence pack.

### Q10: What evidence supports this review?

| # | Evidence | Path |
|---|---|---|
| 1 | Git status before | `_evidence/LIVE-DISPATCH-READINESS-REVIEW-A1/git-status-before.txt` |
| 2 | Registry readiness | `_evidence/LIVE-DISPATCH-READINESS-REVIEW-A1/registry-readiness.md` |
| 3 | Binding conflict check | `_evidence/LIVE-DISPATCH-READINESS-REVIEW-A1/binding-conflict-check.md` |
| 4 | Dry-run evidence review | `_evidence/LIVE-DISPATCH-READINESS-REVIEW-A1/dry-run-evidence-review.md` |
| 5 | Evidence capture readiness | `_evidence/LIVE-DISPATCH-READINESS-REVIEW-A1/evidence-capture-readiness.md` |
| 6 | Hook failure semantics | `_evidence/LIVE-DISPATCH-READINESS-REVIEW-A1/hook-failure-semantics-status.md` |
| 7 | Workspace closure status | `_evidence/LIVE-DISPATCH-READINESS-REVIEW-A1/workspace-closure-status.md` |
| 8 | Deferred files register | `_evidence/LIVE-DISPATCH-READINESS-REVIEW-A1/deferred-files-register.yaml` |
| 9 | Safety report | `_evidence/LIVE-DISPATCH-READINESS-REVIEW-A1/safety-report.json` |
| 10 | Chain of evidence | `_evidence/LIVE-DISPATCH-READINESS-REVIEW-A1/chain-evidence.json` |

---

## Section Verdict Summary

| Section | Verdict | Blocking? |
|---|---|---|
| 6.1 Registry readiness | PARTIAL_PASS | No (capacity fix needed but not safety-critical) |
| 6.2 Binding conflict | **FAIL** | **Yes** (duplicate conversation_id) |
| 6.3 Dry-run evidence | PASS_WITH_STALE_RISK | No (fresh dry-run recommended) |
| 6.4 Evidence capture | PASS | No |
| 6.5 Hook failure semantics | PASS | No |
| 6.6 Workspace closure | PARTIAL_PASS | No |

## Required Fixes Before Authorization

1. **Resolve duplicate conversation_id:** Rebind dev-frame-writing or dev-frame-opencode to a new, distinct ChatGPT conversation.
2. **Fix registry capacity:** Either increase `max_registered_projects` in the schema or remove/archivate at least 1 project to bring the total to 10 or fewer.
3. **Execute fresh dry-run:** Run `dry_run_dispatch_10.py` within 1 hour before requesting live dispatch authorization.

## Overall Verdict

**NOT_READY_NEEDS_FIXES** -- The architectural foundations are strong (fail-closed dispatch, proven hooks, mature evidence capture), but the duplicate conversation_id is a blocking safety issue that must be resolved before human authorization for live dispatch can be responsibly requested. After fixing the two required items, the verdict would upgrade to **READY_FOR_HUMAN_AUTHORIZATION_WITH_LIMITATIONS**.
