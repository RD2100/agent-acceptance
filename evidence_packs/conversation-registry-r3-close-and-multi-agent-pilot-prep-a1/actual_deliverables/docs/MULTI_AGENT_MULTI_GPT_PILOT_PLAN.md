# Multi-Agent Multi-GPT Pilot Plan

| Field | Value |
|-------|-------|
| pilot_id | multi-agent-multi-gpt-pilot-a1 |
| status | pending_manual_binding |
| prerequisite_task | CONVERSATION-REGISTRY-R3-CLOSE-AND-MULTI-AGENT-PILOT-PREP-A1 |

## 1. Pilot Goal

Run a controlled pilot with:

- 2 agents
- 2 projects
- 2 independent GPT conversations
- one agent bound to one conversation
- no shared capture context

The pilot is not allowed to start from fabricated conversation metadata. Any agent without a verified `chat_url` or `conversation_id` remains `pending_manual_binding`.

The pilot also covers the related runtime stack:

- `devframe-control-plane` (`D:/dev-frame/ai-workflow-hub`) is in scope as the control-plane / pipeline provenance layer.
- `dev-frame-opencode` is in scope as the human-gated agent dispatch layer.
- `paper-workflow` is in scope as a governed business workflow for synthetic or sanitized paper review tasks.

These entries being in scope does not authorize cross-repo writes, live CDP, real paper processing, or `opencode run` execution. External runtime execution remains governed by `human_gated_for_external_runtime_execution`.

## 2. Minimal Pilot Structure

```json
{
  "pilot_id": "multi-agent-multi-gpt-pilot-a1",
  "agents": [
    {
      "agent_id": "agent-alpha",
      "project_id": "project-alpha",
      "project_root": "D:/project-alpha",
      "binding_status": "pending_manual_binding",
      "conversation_id": null,
      "chat_url": null
    },
    {
      "agent_id": "agent-beta",
      "project_id": "project-beta",
      "project_root": "D:/project-beta",
      "binding_status": "pending_manual_binding",
      "conversation_id": null,
      "chat_url": null
    }
  ],
  "rules": {
    "one_agent_one_conversation": true,
    "human_gated_for_external_runtime_execution": true,
    "forbid_last_message_only_capture": true,
    "must_match_run_id": true,
    "must_match_task_id": true,
    "must_include_end_marker": true
  },
  "governance_scope": {
    "external_runtimes": [
      "devframe-control-plane",
      "dev-frame-opencode",
      "paper-workflow"
    ]
  }
}
```

## 3. Entry Preconditions

1. Conversation Registry A1-R3 is `accepted` or `accepted_with_limitation`.
2. Both projects pass AWSP scaffold validation.
3. Both projects have `.agent/CONVERSATION_BINDING.json`.
4. The two `agent_id` values are unique.
5. Each agent has either a real independent `chat_url` or remains `pending_manual_binding`.
6. Real parallel runs use independent browser profiles or independent CDP sessions.
7. GPT capture must not rely on the last assistant message only.
8. Evidence packs include conversation binding validation output.
9. `.agent/CONVERSATION_BINDING.json` declares `governance_scope.external_runtimes` for `devframe-control-plane`, `dev-frame-opencode`, and `paper-workflow`.
10. `docs/agent-runtime/capability-inventory.md` includes the dispatch/control-plane capabilities used by the pilot.
11. `docs/agent-runtime/tool-policy.md` permits the exact command class to be used; otherwise runtime execution remains blocked.
12. Any `opencode run`, `D:/dev-frame/ai-workflow-hub` execution, cross-repo smoke, or real paper processing has a separate human gate and evidence record.

## 4. Forbidden Actions

- Do not fabricate `chat_url`.
- Do not fabricate `conversation_id`.
- Do not fabricate GPT replies.
- Do not let two agents share one active conversation.
- Do not infer binding from the last ChatGPT conversation.
- Do not report `pending_manual_binding` as `active`.
- Do not mark a GPT review complete without matching `run_id`, `task_id`, and `END_OF_GPT_RESPONSE`.
- Do not run `D:/dev-frame/ai-workflow-hub`, `D:/dev-frame/smoke_test.py`, or cross-repo pytest as an implicit pilot preflight.
- Do not let `dev-frame-opencode` submit directly to GPT or create authoritative closure evidence outside SADP/reviewer gates.
- Do not process real user papers or enable live CDP for paper workflow without explicit authorization.

## 5. Pilot Activation Checklist

- [ ] `agent-alpha` has independent binding evidence or remains pending.
- [ ] `agent-beta` has independent binding evidence or remains pending.
- [ ] Each binding validates against `CONVERSATION_REGISTRY.schema.json`.
- [ ] Each GPT review prompt uses `{{RUN_ID}}` and `{{TASK_ID}}`.
- [ ] Each GPT reply capture contains matching `run_id`, `task_id`, and `END_OF_GPT_RESPONSE`.
- [ ] Each evidence pack includes `CONVERSATION_BINDING.json` and validator output.
- [ ] `governance_scope` validates all three runtime entries.
- [ ] Capability inventory and tool policy both allow the selected dispatch path.
- [ ] Paper workflow input is synthetic or sanitized, or there is a recorded human authorization.
