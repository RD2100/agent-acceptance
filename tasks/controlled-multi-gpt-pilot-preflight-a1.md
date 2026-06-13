# TaskSpec: CONTROLLED-MULTI-GPT-PILOT-PREFLIGHT-A1 - Controlled Pilot Launch Packet

- **ID**: CONTROLLED-MULTI-GPT-PILOT-PREFLIGHT-A1
- **Batch**: controlled-multi-gpt-pilot
- **Risk**: high
- **Priority**: P1
- **Goal**: Produce a machine-checkable launch packet for the controlled multi-GPT pilot without fabricating authorization or live-session evidence.
- **Context**: Local governance is READY, but controlled pilot remains HUMAN_REQUIRED because the current activation record lacks run-bound authorization and live independent session evidence. The user has Chrome/CDP open, but the bound reviewer/executor conversation URLs must be verified by current CDP evidence before Gate 0 can pass.
- **Allowed Files**:
  - tasks/controlled-multi-gpt-pilot-preflight-a1.md
  - .ai/current-task.yaml
  - _reports/controlled-multi-gpt-pilot-a1/**
  - _reports/multi-agent-gate0-preflight-a1/PREFLIGHT_LATEST_CHECK.json
  - _evidence/CONTROLLED-MULTI-GPT-PILOT-PREFLIGHT-A1/**
  - hooks/sealed-files-manifest.json
  - _evidence/hook-output/**
- **Forbidden**:
  - No opencode run, WorkQueue consumption, cross-repo smoke, real paper workflow, or external runtime execution.
  - No fabricated authorization, fabricated ChatGPT replies, fabricated conversation IDs, or fabricated live-session evidence.
  - No mutation of .agent/CONVERSATION_BINDING.json, capability inventory, tool policy, or protected governance docs in this task.
  - No cleanup or mutation of unrelated dirty baseline artifacts.

- **Gate 0 Ledger**:
  ```yaml
  gate_0:
    triggered: true
    trigger_reason: "Controlled pilot launch requires run-bound authorization and current live session evidence."
    inventory_evidence:
      queried_sources:
        - docs/agent-runtime/production-readiness.md
        - docs/MULTI_AGENT_MULTI_GPT_PILOT_PLAN.md
        - docs/agent-runtime/live-dispatch-human-authorization-template.md
        - scripts/multi_agent_gate0_preflight.py
        - scripts/tab_target_resolver.py
        - .agent/CONVERSATION_BINDING.json
        - _reports/multi-agent-multi-gpt-pilot-a1/ACTIVATION_RECORD.json
      matched_capabilities:
        - controlled_pilot_readiness_gate
        - shared_cdp_tab_target_resolution
        - run_bound_activation_record
        - independent_session_evidence
      compared_against_request:
        - "automate until formal use"
        - "inspect opened Chrome/CDP flow"
        - "advance toward controlled multi-GPT pilot without fake green"
    rules_checked: [core-001, core-007, core-008, review-001]
    lessons_checked: [LL-independent-review-evidence, LL-structured-task-spec]
    sufficiency_decision: existing_partial
    decision: build_delta
    delta_justification: "Existing gates correctly block execution, but the operator needs an exact launch packet that turns HUMAN_REQUIRED into actionable evidence requirements."
  ```

- **Conflict Registry**:
  ```yaml
  conflict_registry:
    read_set:
      - docs/agent-runtime/production-readiness.md
      - docs/MULTI_AGENT_MULTI_GPT_PILOT_PLAN.md
      - docs/agent-runtime/live-dispatch-human-authorization-template.md
      - scripts/multi_agent_gate0_preflight.py
      - scripts/tab_target_resolver.py
      - .agent/CONVERSATION_BINDING.json
      - _reports/multi-agent-multi-gpt-pilot-a1/ACTIVATION_RECORD.json
      - _reports/production-readiness-automation-a1/LOCAL_VERIFICATION.json
      - _reports/multi-agent-dispatch-plan-a1/DISPATCH_PLAN_CURRENT.json
    write_set:
      - tasks/controlled-multi-gpt-pilot-preflight-a1.md
      - .ai/current-task.yaml
      - _reports/controlled-multi-gpt-pilot-a1/**
      - _reports/multi-agent-gate0-preflight-a1/PREFLIGHT_LATEST_CHECK.json
      - _evidence/CONTROLLED-MULTI-GPT-PILOT-PREFLIGHT-A1/**
      - hooks/sealed-files-manifest.json
      - _evidence/hook-output/**
    protected_files_touched: false
    conflict_level: medium
  ```

- **Acceptance Gates**:
  1. Latest CDP discovery and Gate 0 recheck are recorded with exact current blocking reasons.
  2. Authorization request remains pending unless a run-bound human authorization record exists.
  3. Required reviewer/executor ChatGPT URLs are listed exactly and not replaced by unrelated open tabs.
  4. The packet identifies the minimum evidence needed to promote Gate 0 to PASS and dispatch to READY.
  5. No external runtime, paper workflow, opencode dispatch, or live pilot execution is performed.
  6. ExecutionReport and Reviewer Index exist under _evidence/CONTROLLED-MULTI-GPT-PILOT-PREFLIGHT-A1/.

- **Expected Output**: A controlled-pilot launch packet under _reports/controlled-multi-gpt-pilot-a1/ plus SADP evidence under _evidence/CONTROLLED-MULTI-GPT-PILOT-PREFLIGHT-A1/.
- **Rollback**: Remove only this task's generated report/evidence files and TaskSpec changes; preserve unrelated worktree artifacts.
