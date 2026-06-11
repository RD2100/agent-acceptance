# GPT Review Prompt

Task ID: {{TASK_ID}}
Run ID: {{RUN_ID}}

You are reviewing the R3 closure of Conversation Registry and the preparation for multi-agent / multi-GPT pilot mode.

Focus areas:
1. Real JSON Schema
2. Schema-backed validation
3. CONVERSATION_BINDING template / schema consistency
4. role validation
5. pending_manual_binding vs active binding policy
6. active binding requiring chat_url/conversation_id
7. duplicate agent_id detection
8. project_root consistency
9. capture_policy strict true checks
10. validate_scaffold integration
11. multi-agent / multi-GPT pilot plan existence and safety
12. tests and evidence pack completeness
13. devframe-control-plane / dev-frame-opencode / paper-workflow governance scope
14. human-gated policy for opencode, ai-workflow-hub, cross-repo smoke, live CDP, and real paper workflow

Expected response format:

overall_judgment: accepted | accepted_with_limitation | blocked | human_required
run_id: {{RUN_ID}}
findings:
  - ...
next_task_authorization: ...
---END_OF_GPT_RESPONSE---
