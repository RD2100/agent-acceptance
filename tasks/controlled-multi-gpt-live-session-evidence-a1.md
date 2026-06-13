# TaskSpec: CONTROLLED-MULTI-GPT-LIVE-SESSION-EVIDENCE-A1 - Live Session Evidence

- **ID**: CONTROLLED-MULTI-GPT-LIVE-SESSION-EVIDENCE-A1
- **Batch**: controlled-multi-gpt-pilot
- **Risk**: high
- **Priority**: P1
- **Goal**: Record current live CDP evidence for the two bound pilot conversations without authorizing or executing dispatch.
- **Context**: The controlled-pilot launch packet opened the two required ChatGPT conversation URLs in the shared Chrome CDP instance. Gate 0 still requires current activation-record session evidence and separate run-bound human authorization.
- **Allowed Files**:
  - tasks/controlled-multi-gpt-live-session-evidence-a1.md
  - .ai/current-task.yaml
  - _reports/multi-agent-multi-gpt-pilot-a1/ACTIVATION_RECORD.json
  - _reports/controlled-multi-gpt-pilot-a1/live-session-evidence/**
  - _reports/controlled-multi-gpt-pilot-a1/CDP_DISCOVERY_RECHECK.json
  - _reports/multi-agent-gate0-preflight-a1/PREFLIGHT_LATEST_CHECK.json
  - _evidence/CONTROLLED-MULTI-GPT-LIVE-SESSION-EVIDENCE-A1/**
  - hooks/sealed-files-manifest.json
  - _evidence/hook-output/**
- **Forbidden**:
  - No `authorized=true` unless a separate run-bound human authorization record exists.
  - No opencode run, WorkQueue consumption, cross-repo smoke, paper workflow, or external runtime execution.
  - No fabricated target IDs, fabricated session IDs, fabricated GPT replies, or last-message-only capture.
  - No formal-use promotion or production authorization.

- **Gate 0 Ledger**:
  ```yaml
  gate_0:
    triggered: true
    trigger_reason: "Live session evidence changes the activation record used by multi-agent Gate 0."
    inventory_evidence:
      queried_sources:
        - docs/agent-runtime/production-readiness.md
        - scripts/multi_agent_gate0_preflight.py
        - scripts/tab_target_resolver.py
        - .agent/CONVERSATION_BINDING.json
        - _reports/controlled-multi-gpt-pilot-a1/AUTHORIZATION_REQUEST.json
        - _reports/multi-agent-multi-gpt-pilot-a1/ACTIVATION_RECORD.json
      matched_capabilities:
        - run_bound_activation_record
        - independent_session_evidence
        - shared_cdp_tab_target_resolution
      compared_against_request:
        - "advance toward controlled multi-GPT pilot"
        - "record real live session evidence"
        - "do not bypass human authorization"
    rules_checked: [core-001, core-007, core-008, review-001]
    lessons_checked: [LL-independent-review-evidence, LL-structured-task-spec]
    sufficiency_decision: existing_partial
    decision: build_delta
    delta_justification: "Existing Gate 0 can validate session evidence, but the current activation record still contains stale false session fields."
  ```

- **Conflict Registry**:
  ```yaml
  conflict_registry:
    read_set:
      - docs/agent-runtime/production-readiness.md
      - scripts/multi_agent_gate0_preflight.py
      - scripts/tab_target_resolver.py
      - .agent/CONVERSATION_BINDING.json
      - _reports/controlled-multi-gpt-pilot-a1/AUTHORIZATION_REQUEST.json
      - _reports/multi-agent-multi-gpt-pilot-a1/ACTIVATION_RECORD.json
    write_set:
      - tasks/controlled-multi-gpt-live-session-evidence-a1.md
      - .ai/current-task.yaml
      - _reports/multi-agent-multi-gpt-pilot-a1/ACTIVATION_RECORD.json
      - _reports/controlled-multi-gpt-pilot-a1/live-session-evidence/**
      - _reports/controlled-multi-gpt-pilot-a1/CDP_DISCOVERY_RECHECK.json
      - _reports/multi-agent-gate0-preflight-a1/PREFLIGHT_LATEST_CHECK.json
      - _evidence/CONTROLLED-MULTI-GPT-LIVE-SESSION-EVIDENCE-A1/**
      - hooks/sealed-files-manifest.json
      - _evidence/hook-output/**
    protected_files_touched: false
    conflict_level: medium
  ```

- **Acceptance Gates**:
  1. Each bound pilot conversation has a current CDP page target and evidence JSON.
  2. The two session IDs are distinct and tied to the expected agent IDs.
  3. Activation record sets live-session fields from observed CDP state but keeps `authorization.authorized=false`.
  4. Gate 0 improves from live-session blockers to only human authorization blockers, or documents any remaining session blocker.
  5. No external runtime or live dispatch is executed.
  6. ExecutionReport and Reviewer Index exist under _evidence/CONTROLLED-MULTI-GPT-LIVE-SESSION-EVIDENCE-A1/.

- **Expected Output**: Updated activation record with live session evidence and a Gate 0 recheck that still respects human authorization.
- **Rollback**: Revert only this task's generated session evidence and activation-record changes.
