# Final Report — LIVE-DISPATCH-READINESS-REVIEW-A1

**Task ID:** LIVE-DISPATCH-READINESS-REVIEW-A1
**Date:** 2026-06-12
**Type:** Readiness Review (Audit Only)
**Mode:** No live dispatch executed, no routing/hook files modified

---

## Verdict: NOT_READY_NEEDS_FIXES

The agent-runtime system demonstrates strong architectural foundations for live dispatch, but two issues prevent readiness for human authorization.

## What Works

The shared-CDP architecture with fail-closed tab resolution is sound. The router correctly refuses to dispatch when targets cannot be unambiguously resolved. Evidence capture (ECS-A2) is mature with 1260 passing tests and formal GPT review acceptance. Hook failure semantics are proven for 4 of 5 capabilities with over 100 historical runs. The dry-run dispatch script successfully validates the full packet construction pipeline without sending anything.

In summary: the infrastructure to safely dispatch tasks to ChatGPT conversations via Chrome DevTools Protocol exists and has been formally reviewed. The system's safety properties (fail-closed, no fallback, human-gated) are architecturally enforced and tested.

## What Must Be Fixed

**Issue 1 (HIGH): Duplicate Conversation ID.** Two active projects, dev-frame-writing and dev-frame-opencode, share the ChatGPT conversation `6a297e5f-c9c8-83a8-b413-a8fc414e0e85`. Under shared-CDP tab resolution, the tab target resolver uses exact URL matching. If both projects point to the same URL, dispatching for one project could land on the other's conversation tab — or fail ambiguously if the resolver detects both. This violates the `one_agent_one_conversation` policy and creates a genuine dispatch misdirection risk. One of these projects must rebind to a new, distinct conversation before live dispatch can be safely authorized.

**Issue 2 (MEDIUM): Registry Capacity Exceeded.** The registry has 11 projects but the schema caps at 10. This is a governance compliance issue rather than a safety issue — the system operates correctly with 11 entries — but it violates the declared schema constraint and should be resolved by either removing an unused project or updating the schema limit.

## Limitations Stated Plainly

This review is an audit of existing artifacts and code. It did not execute live dispatch, probe the Chrome CDP connection, or modify any runtime files. The dry-run evidence reviewed is 36 hours old; the Chrome tab state at time of review was not verified. The workspace has 193 untracked entries that should be cleaned up, though this does not affect dispatch safety.

The verdict is based on static analysis and evidence inspection. A live dispatch test (with human authorization) would be needed to fully validate end-to-end behavior, but the prerequisites for such a test are not yet met due to the binding conflict.

## Path to Authorization

Once the two blocking issues are resolved:

1. Rebind dev-frame-writing or dev-frame-opencode to a new conversation
2. Fix registry capacity (remove project or raise limit)
3. Execute a fresh dry-run to verify the fix
4. Update this review's verdict to READY_FOR_HUMAN_AUTHORIZATION_WITH_LIMITATIONS
5. Complete the human authorization template (`docs/agent-runtime/live-dispatch-human-authorization-template.md`)
6. Execute live dispatch with tripmark as the minimal candidate

## Minimal Live Dispatch Candidate

**tripmark** (project-alpha) is the only project currently eligible for live dispatch. It was the sole dispatchable project in the dry-run, with complete packet resolution (target_id, conversation_id, chat_url, capture_policy). All dispatch to tripmark must be human-authorized, single-event, and evidence-captured.

## Evidence Produced

13 files produced across 3 documentation files and 10 evidence artifacts. All evidence is in `_evidence/LIVE-DISPATCH-READINESS-REVIEW-A1/`. Documentation is in `docs/agent-runtime/`. See `chain-evidence.json` for the complete evidence chain.

## Safety Report

No live dispatch was executed. No routing files were modified. No hook enforcement files were modified. All deny_paths were respected. The `human_required` governance policy remains in effect. See `safety-report.json` for the detailed safety assessment.
