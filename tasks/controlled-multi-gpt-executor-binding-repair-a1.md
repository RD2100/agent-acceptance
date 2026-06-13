# TaskSpec: CONTROLLED-MULTI-GPT-EXECUTOR-BINDING-REPAIR-A1 - Executor Binding Repair

- **ID**: CONTROLLED-MULTI-GPT-EXECUTOR-BINDING-REPAIR-A1
- **Batch**: controlled-multi-gpt-pilot
- **Risk**: high
- **Priority**: P1
- **Goal**: Replace the unstable `agent-pilot-beta` ChatGPT conversation binding with a real, current, independently captured executor conversation URL.
- **Context**: Gate 0 shows `agent-pilot-beta` lacks live CDP verification because the existing bound URL redirects to the ChatGPT home page. A stable executor conversation is required before controlled pilot readiness can progress.
- **Allowed Files**:
  - tasks/controlled-multi-gpt-executor-binding-repair-a1.md
  - .ai/current-task.yaml
  - .agent/CONVERSATION_BINDING.json
  - _reports/controlled-multi-gpt-pilot-a1/executor-binding-repair/**
  - _reports/controlled-multi-gpt-pilot-a1/live-session-evidence/**
  - _reports/controlled-multi-gpt-pilot-a1/CDP_DISCOVERY_RECHECK.json
  - _reports/multi-agent-multi-gpt-pilot-a1/ACTIVATION_RECORD.json
  - _reports/multi-agent-gate0-preflight-a1/PREFLIGHT_LATEST_CHECK.json
  - _evidence/CONTROLLED-MULTI-GPT-EXECUTOR-BINDING-REPAIR-A1/**
  - hooks/sealed-files-manifest.json
  - _evidence/hook-output/**
- **Forbidden**:
  - No `opencode run`, WorkQueue consumption, cross-repo smoke, paper workflow, or external runtime execution.
  - No controlled-pilot dispatch and no formal-use promotion.
  - No fabricated conversation URL, conversation ID, GPT response, target ID, or session evidence.
  - No reuse of the reviewer conversation as executor.
  - No `authorization.authorized=true`; run-bound authorization remains separate.

- **Gate 0 Ledger**:
  ```yaml
  gate_0:
    triggered: true
    trigger_reason: "Executor conversation binding repair changes multi-agent identity evidence."
    inventory_evidence:
      queried_sources:
        - docs/MULTI_AGENT_MULTI_GPT_PILOT_PLAN.md
        - docs/AGENT_WORKFLOW_STANDARD.md
        - scripts/validate_conversation_registry.py
        - scripts/tab_target_resolver.py
        - .agent/CONVERSATION_BINDING.json
        - _reports/controlled-multi-gpt-pilot-a1/live-session-evidence/agent-pilot-beta.json
      matched_capabilities:
        - conversation_registry_binding
        - shared_cdp_tab_target_resolution
        - independent_session_evidence
      compared_against_request:
        - "make controlled pilot executable"
        - "repair missing executor live session"
        - "avoid fabricated binding metadata"
    rules_checked: [core-001, core-007, core-008, review-001]
    lessons_checked: [LL-independent-review-evidence, LL-structured-task-spec]
    sufficiency_decision: existing_partial
    decision: build_delta
    delta_justification: "Existing binding validates structurally but points to a conversation that is not live; a real replacement URL must be captured from the browser session."
  ```

- **Conflict Registry**:
  ```yaml
  conflict_registry:
    read_set:
      - docs/MULTI_AGENT_MULTI_GPT_PILOT_PLAN.md
      - docs/AGENT_WORKFLOW_STANDARD.md
      - scripts/validate_conversation_registry.py
      - scripts/tab_target_resolver.py
      - .agent/CONVERSATION_BINDING.json
      - _reports/controlled-multi-gpt-pilot-a1/live-session-evidence/agent-pilot-beta.json
    write_set:
      - tasks/controlled-multi-gpt-executor-binding-repair-a1.md
      - .ai/current-task.yaml
      - .agent/CONVERSATION_BINDING.json
      - _reports/controlled-multi-gpt-pilot-a1/executor-binding-repair/**
      - _reports/controlled-multi-gpt-pilot-a1/live-session-evidence/**
      - _reports/controlled-multi-gpt-pilot-a1/CDP_DISCOVERY_RECHECK.json
      - _reports/multi-agent-multi-gpt-pilot-a1/ACTIVATION_RECORD.json
      - _reports/multi-agent-gate0-preflight-a1/PREFLIGHT_LATEST_CHECK.json
      - _evidence/CONTROLLED-MULTI-GPT-EXECUTOR-BINDING-REPAIR-A1/**
      - hooks/sealed-files-manifest.json
      - _evidence/hook-output/**
    protected_files_touched: false
    conflict_level: medium
  ```

- **Acceptance Gates**:
  1. A new executor conversation URL is captured from actual Chrome/CDP state.
  2. The new executor conversation ID differs from the reviewer conversation ID.
  3. `.agent/CONVERSATION_BINDING.json` validates after repair.
  4. Live session evidence for `agent-pilot-beta` becomes `live=true`.
  5. Activation record keeps `authorization.authorized=false`.
  6. Gate 0 no longer reports executor live-session blockers; remaining blockers, if any, are documented.
  7. No external runtime, dispatch, paper workflow, or formal promotion is executed.
  8. ExecutionReport and Reviewer Index exist under _evidence/CONTROLLED-MULTI-GPT-EXECUTOR-BINDING-REPAIR-A1/.

- **Expected Output**: Updated executor binding, real binding probe evidence, refreshed activation record, and Gate 0 recheck.
- **Rollback**: Restore the previous `agent-pilot-beta` binding and remove this task's generated evidence files.
