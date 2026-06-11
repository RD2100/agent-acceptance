# AWSP Shared CDP Architecture v2 Baseline

**Task ID**: SHARED-CDP-ARCHITECTURE-V2-BASELINE-A1
**Status**: ACCEPTED
**Architecture Version**: 2.0.0
**Date**: 2026-06-10

## Architecture Decision

Effective immediately, the AWSP multi-project architecture is:

**Single Chrome Shared CDP + Conversation-Level Logical Isolation**

All projects share ONE Chrome instance on a single CDP endpoint. Isolation is achieved through distinct ChatGPT conversation IDs, tab-level target resolution, and run_id/task_id-bound capture.

## What Changed From v1

| Aspect | v1 (Multi-CDP) | v2 (Shared CDP) |
|--------|----------------|-----------------|
| Chrome instances | 1 per project | 1 shared |
| CDP ports | 9222-9231 | Single 9222 |
| Profiles | 1 per project | 1 shared |
| Isolation boundary | profile + port + conversation | conversation + tab target + run_id |
| Login strategy | Per-profile login | One-time shared login |
| Profile sharing | Collision = blocker | Expected = known tradeoff |
| CDP sharing | Collision = blocker | Expected = design choice |

## v2 Isolation Model (Mandatory)

### Strong Isolation Boundaries

1. **conversation_id** -- MUST be unique per active project
2. **chat_url** -- MUST be unique per active project
3. **tab target_id** -- MUST be resolvable to exact conversation page
4. **run_id / task_id** -- MUST be matched in capture evidence
5. **capture_policy** -- MUST bind to specific target, forbid last-message-only

### Known Tradeoffs (Not Blockers)

1. All projects share `cdp_endpoint = http://localhost:9222` -- this is by design
2. All projects share `browser_profile_id = shared` -- this is by design
3. Single Chrome crash affects all projects -- mitigated by resource policy
4. Shared login state -- no account-level isolation

### Forbidden Practices

1. No fallback to "current active tab" for dispatch
2. No "last assistant message" capture without target binding
3. No dispatch without tab target_id resolution
4. No multiple projects sharing same conversation_id
5. No marking project active without verified unique conversation

## Gate0 Preflight v2 Rules

Gate0 MUST enforce these checks for v2:

1. Allow shared cdp_endpoint across projects
2. Allow shared browser_profile_id across projects
3. Check conversation_id uniqueness (DUPLICATE = BLOCKED)
4. Check chat_url uniqueness (DUPLICATE = BLOCKED)
5. Check CDP /json page list contains matching conversation URL
6. Check tab target_id resolves to unique page target
7. If no matching tab found: classification = human_required
8. If multiple tabs match same conversation: classification = blocked
9. CDP health check on shared port (single check for all)

## Dispatch Packet v2 Requirements

Every dispatch packet MUST include:

- `target_id` -- CDP page target identifier
- `target_url` -- exact page URL at dispatch time
- `conversation_id` -- the bound conversation
- `capture_policy` -- structured capture rules
- `expected_run_id` -- run_id to match in response
- `expected_task_id` -- task_id to match in response
- `expected_end_marker` -- END_OF_GPT_RESPONSE
- `forbid_last_message_only_capture` -- always true
- `dispatch_mode` -- dry_run | human_gated_live
- `cdp_mode` -- shared_single_chrome
- `isolation_model` -- conversation_target_bound

## Resource Policy

The shared Chrome is governed by MULTI_PROJECT_RESOURCE_POLICY.json:

- max_registered_projects: 10
- max_active_gpt_reviews: 2 (bounded concurrency)
- require_human_for_live_dispatch: true

## Expansion Path

1 active -> 2 active -> 4 active -> 6 active -> 10 active

Each step requires Gate0 v2 PASS + dry-run verification before proceeding.
