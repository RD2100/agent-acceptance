# 6.2 Binding Conflict Check

**Task:** LIVE-DISPATCH-READINESS-REVIEW-A1
**Date:** 2026-06-12
**Sources:** `.agent/CONVERSATION_BINDING.json`, per-project `.agent/CONVERSATION_BINDING.json` files

## Root Binding State

The root project (agent-acceptance) has 2 active agent bindings:

| agent_id | role | conversation_id | binding_status |
|---|---|---|---|
| agent-local-001 | reviewer | 6a26cc03-235c-83a2-a0fc-cd29be615959 | active |
| agent-pilot-beta | executor | 6a28d545-f918-83a5-b122-dc1503386374 | active |

Both bindings use `http://localhost:9222` as CDP endpoint with strict capture policies (must_match_run_id, must_match_task_id, must_include_end_marker, forbid_last_message_only_capture).

## Cross-Project Binding Audit

### CRITICAL: Duplicate Conversation ID

| Project | Agent ID | Conversation ID | Chat URL |
|---|---|---|---|
| dev-frame-writing | agent-writing-001 | **6a297e5f-c9c8-83a8-b413-a8fc414e0e85** | https://chatgpt.com/c/6a297e5f... |
| dev-frame-opencode | agent-opencode-001 | **6a297e5f-c9c8-83a8-b413-a8fc414e0e85** | https://chatgpt.com/c/6a297e5f... |

Both projects point to the identical ChatGPT conversation. Under the shared-CDP architecture, `tab_target_resolver.py` uses exact URL match to resolve a Chrome tab to a `target_id`. If both projects' conversations are open in the same Chrome instance:

- **If only one tab is open:** Only that project resolves; the other gets `human_required_tab_unresolved`.
- **If both tabs are open:** The resolver would return the same `target_id` for both, creating a dispatch collision.
- **Policy violation:** `default_conversation_policy: "one_agent_one_conversation"` is violated because two distinct projects share one conversation.

### Orphan Binding Check

The root CONVERSATION_BINDING.json only covers `agent-acceptance`. The 7 pending_binding projects (gamma through iota) have no binding files -- this is expected for their status.

No orphan bindings detected (no binding references a non-existent project_id).

### Stale Binding Check

- agent-local-001 (reviewer): registered 2026-06-10, still active. Age: ~48h. Within acceptable range.
- agent-pilot-beta (executor): registered 2026-06-10, still active. Age: ~48h. Within acceptable range.
- No stale bindings (> 7 days) found.

## Findings

| # | Finding | Severity | Impact |
|---|---|---|---|
| F-6.2-1 | Duplicate conversation_id between dev-frame-writing and dev-frame-opencode | **HIGH** | Dispatch collision or misdirection |
| F-6.2-2 | Policy violation: one_agent_one_conversation | **MEDIUM** | Governance non-compliance |
| F-6.2-3 | No orphan bindings | PASS | N/A |
| F-6.2-4 | No stale bindings | PASS | N/A |

## Verdict

**Section verdict: FAIL** -- The duplicate conversation_id between dev-frame-writing and dev-frame-opencode is a blocking issue for live dispatch. This must be resolved (one project must rebind to a new conversation) before live dispatch can be authorized.
