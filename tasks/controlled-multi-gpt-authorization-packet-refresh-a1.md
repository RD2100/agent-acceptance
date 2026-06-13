# TaskSpec: CONTROLLED-MULTI-GPT-AUTHORIZATION-PACKET-REFRESH-A1 - Authorization Packet Refresh

- **ID**: CONTROLLED-MULTI-GPT-AUTHORIZATION-PACKET-REFRESH-A1
- **Batch**: controlled-multi-gpt-pilot
- **Risk**: high
- **Priority**: P1
- **Goal**: Refresh the controlled-pilot authorization packet so it reflects the current state: both live sessions are ready and only run-bound human authorization remains.
- **Context**: Executor binding repair created a stable executor ChatGPT conversation and Gate 0 now passes live-session checks. The old authorization request still lists session-evidence gaps that are no longer current.
- **Allowed Files**:
  - tasks/controlled-multi-gpt-authorization-packet-refresh-a1.md
  - .ai/current-task.yaml
  - _reports/controlled-multi-gpt-pilot-a1/AUTHORIZATION_REQUEST.json
  - _reports/controlled-multi-gpt-pilot-a1/NEXT_COMMANDS.md
  - _reports/controlled-multi-gpt-pilot-a1/HUMAN_AUTHORIZATION_TEMPLATE.json
  - _evidence/CONTROLLED-MULTI-GPT-AUTHORIZATION-PACKET-REFRESH-A1/**
  - hooks/sealed-files-manifest.json
  - _evidence/hook-output/**
- **Forbidden**:
  - No `authorization.authorized=true`.
  - No activation-record authorization mutation.
  - No opencode run, WorkQueue consumption, cross-repo smoke, paper workflow, controlled dispatch, or formal-use promotion.
  - No fabricated human decision.

- **Gate 0 Ledger**:
  ```yaml
  gate_0:
    triggered: true
    trigger_reason: "Authorization packet controls the final human gate before controlled pilot readiness."
    inventory_evidence:
      queried_sources:
        - _reports/controlled-multi-gpt-pilot-a1/AUTHORIZATION_REQUEST.json
        - _reports/controlled-multi-gpt-pilot-a1/CDP_DISCOVERY_RECHECK.json
        - _reports/multi-agent-gate0-preflight-a1/PREFLIGHT_LATEST_CHECK.json
        - _reports/multi-agent-multi-gpt-pilot-a1/ACTIVATION_RECORD.json
      matched_capabilities:
        - run_bound_authorization
        - controlled_pilot_readiness_gate
        - independent_session_evidence
      compared_against_request:
        - "advance toward formal use"
        - "make remaining human gate exact"
        - "avoid fake authorization"
    rules_checked: [core-001, core-007, core-008, review-001]
    lessons_checked: [LL-independent-review-evidence, LL-structured-task-spec]
    sufficiency_decision: existing_partial
    decision: build_delta
    delta_justification: "Existing authorization request is stale after executor binding repair; refresh it to match current Gate 0 evidence."
  ```

- **Conflict Registry**:
  ```yaml
  conflict_registry:
    read_set:
      - _reports/controlled-multi-gpt-pilot-a1/AUTHORIZATION_REQUEST.json
      - _reports/controlled-multi-gpt-pilot-a1/CDP_DISCOVERY_RECHECK.json
      - _reports/multi-agent-gate0-preflight-a1/PREFLIGHT_LATEST_CHECK.json
      - _reports/multi-agent-multi-gpt-pilot-a1/ACTIVATION_RECORD.json
    write_set:
      - tasks/controlled-multi-gpt-authorization-packet-refresh-a1.md
      - .ai/current-task.yaml
      - _reports/controlled-multi-gpt-pilot-a1/AUTHORIZATION_REQUEST.json
      - _reports/controlled-multi-gpt-pilot-a1/NEXT_COMMANDS.md
      - _reports/controlled-multi-gpt-pilot-a1/HUMAN_AUTHORIZATION_TEMPLATE.json
      - _evidence/CONTROLLED-MULTI-GPT-AUTHORIZATION-PACKET-REFRESH-A1/**
      - hooks/sealed-files-manifest.json
      - _evidence/hook-output/**
    protected_files_touched: false
    conflict_level: medium
  ```

- **Acceptance Gates**:
  1. Authorization packet says both live-session checks are ready.
  2. Authorization packet says only run-bound human authorization remains before Gate 0 PASS.
  3. Template keeps `authorized=false` and is not accepted as real authorization.
  4. No dispatch or external runtime is executed.
  5. ExecutionReport and Reviewer Index exist under _evidence/CONTROLLED-MULTI-GPT-AUTHORIZATION-PACKET-REFRESH-A1/.

- **Expected Output**: Refreshed authorization request and exact next-command packet.
- **Rollback**: Revert only this packet refresh.
