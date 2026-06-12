# Binding Fix Evidence — LIVE-DISPATCH-READINESS-FIX-A1

**Date:** 2026-06-12T05:57:20Z
**Fix:** Suspend dev-frame-writing to resolve duplicate conversation_id + registry capacity

## Pre-Fix State

| Project | Binding Status | Conversation ID | Chat URL |
|---|---|---|---|
| dev-frame-writing | active | 6a297e5f-c9c8-83a8-b413-a8fc414e0e85 | https://chatgpt.com/c/6a297e5f... |
| dev-frame-opencode | active | 6a297e5f-c9c8-83a8-b413-a8fc414e0e85 | https://chatgpt.com/c/6a297e5f... |

Both projects shared the same ChatGPT conversation, violating the `shared_conversation_id` forbidden practice in MULTI_PROJECT_RESOURCE_POLICY.json.

## Fix Rationale

| Factor | dev-frame-writing | dev-frame-opencode |
|---|---|---|
| Project root | D:\agent-acceptance\_projects\dev-frame-writing | D:\dev-frame-opencode |
| Type | Bootstrap stub (AGENTS.md only) | Real project (.agent, .ai, .git, .codegraph) |
| Activity | No commits, no code | Active development |
| Agent ID | agent-writing-001 | agent-opencode-001 |

Decision: Suspend dev-frame-writing (the stub). Keep dev-frame-opencode (the real project).

## Changes Made

### PROJECT_REGISTRY.json
- dev-frame-writing.binding_status: `active` → `suspended`
- Added suspended_at: 2026-06-12T05:00:00Z
- Added suspension_reason: "duplicate conversation_id with dev-frame-opencode (LIVE-DISPATCH-READINESS-FIX-A1)"
- total_projects: 11 → 10

### _projects/dev-frame-writing/.agent/CONVERSATION_BINDING.json
- agent-writing-001.binding_status: `active` → `suspended`

## Post-Fix State

| Metric | Value |
|---|---|
| total_projects | 10 (= max_registered_projects) |
| Active projects | 3 (agent-acceptance, dev-frame-opencode, tripmark) |
| Suspended projects | 1 (dev-frame-writing) |
| Pending projects | 7 (gamma through iota) |
| Duplicate conversation_ids | 0 |
| Forbidden practices violations | 0 |

## Dry-Run Validation

Fresh dry-run at 2026-06-12T05:58:45Z confirms:
- dev-frame-writing classified as `human_required` (not dispatchable — correct)
- 0 collisions, 0 blocked ambiguous tabs
- dev-frame-opencode: dispatchable (tab resolved)
- agent-acceptance: dispatchable (tab resolved)
- tripmark: human_required_tab_unresolved (tab not currently open)

## Reversibility

To reactivate dev-frame-writing:
1. Create a new ChatGPT conversation for the project
2. Update its CONVERSATION_BINDING.json with the new conversation_id
3. Set binding_status back to `active` in both binding and registry
4. Increment total_projects in registry
5. Re-run dry-run to validate no conflicts
