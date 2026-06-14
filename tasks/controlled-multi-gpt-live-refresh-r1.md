# TaskSpec: CONTROLLED-MULTI-GPT-LIVE-REFRESH-R1

- **ID**: CONTROLLED-MULTI-GPT-LIVE-REFRESH-R1
- **Batch**: controlled-multi-gpt-pilot
- **Risk**: high
- **Priority**: P1
- **Goal**: Record the controlled multi-GPT refresh package as the current governance state, preserving `HUMAN_REQUIRED` because live-session evidence is stale.
- **Authorization**: `_reports/controlled-multi-gpt-pilot-a1/HUMAN_AUTHORIZATION.json`
- **Allowed Files**:
  - .ai/current-task.yaml
  - .agent/CONVERSATION_BINDING.json
  - _reports/controlled-multi-gpt-pilot-a1/live-session-evidence/**
  - _reports/multi-agent-multi-gpt-pilot-a1/ACTIVATION_RECORD.json
  - _reports/multi-agent-gate0-preflight-a1/PREFLIGHT_CURRENT.json
  - _reports/multi-agent-dispatch-plan-a1/DISPATCH_PLAN_CURRENT.json
  - scripts/multi_agent_dispatch_plan.py
  - tests/test_multi_agent_dispatch_plan.py
  - tests/test_multi_agent_gate0_preflight.py
  - tests/test_cdp_write_adapter.py
  - _evidence/CONTROLLED-MULTI-GPT-LIVE-REFRESH-R1/**
  - tasks/controlled-multi-gpt-live-refresh-r1.md
  - hooks/sealed-files-manifest.json
  - _evidence/hook-output/**
- **Forbidden**:
  - No paper-workflow execution
  - No dev-frame runtime execution
  - No fabricated session timestamps or unobserved target IDs
  - No destructive Git operations

- **Gate 0 Ledger**:
  ```yaml
  gate_0:
    triggered: true
    trigger_reason: "Authorized controlled-pilot session binding and freshness refresh"
    inventory_evidence:
      queried_sources:
        - .agent/CONVERSATION_BINDING.json
        - _reports/controlled-multi-gpt-pilot-a1/HUMAN_AUTHORIZATION.json
        - _evidence/CDP-LIVE-TRANSPORT-CLOSURE-R1/real-path-probe.txt
      matched_capabilities:
        - run_bound_authorization
        - shared_cdp_transport
        - multi_agent_gate0_preflight
        - multi_agent_dispatch_plan
    rules_checked: [core-004, core-007, core-008, review-001]
    sufficiency_decision: existing_sufficient
    decision: reuse
    delta_justification: "Refresh runtime state from current CDP observations; no new capability."
  ```

- **Conflict Registry**:
  ```yaml
  conflict_registry:
    read_set:
      - .agent/CONVERSATION_BINDING.json
      - _reports/controlled-multi-gpt-pilot-a1/HUMAN_AUTHORIZATION.json
      - scripts/multi_agent_gate0_preflight.py
      - scripts/multi_agent_dispatch_plan.py
    write_set:
      - .ai/current-task.yaml
      - .agent/CONVERSATION_BINDING.json
      - _reports/controlled-multi-gpt-pilot-a1/live-session-evidence/**
      - _reports/multi-agent-multi-gpt-pilot-a1/ACTIVATION_RECORD.json
      - _reports/multi-agent-gate0-preflight-a1/PREFLIGHT_CURRENT.json
      - _reports/multi-agent-dispatch-plan-a1/DISPATCH_PLAN_CURRENT.json
      - scripts/multi_agent_dispatch_plan.py
      - tests/test_multi_agent_dispatch_plan.py
      - tests/test_multi_agent_gate0_preflight.py
      - tests/test_cdp_write_adapter.py
      - _evidence/CONTROLLED-MULTI-GPT-LIVE-REFRESH-R1/**
      - tasks/controlled-multi-gpt-live-refresh-r1.md
      - hooks/sealed-files-manifest.json
      - _evidence/hook-output/**
    protected_files_touched: false
    conflict_level: low
  ```

- **Acceptance Gates**:
  1. Authorization evidence remains linked to the controlled pilot run.
  2. Binding and activation artifacts are recorded without fabricating fresh live-session timestamps.
  3. Gate 0 reports `HUMAN_REQUIRED` with `executed_external_runtime=false`.
  4. Dispatch plan validates with `dispatch_status=HUMAN_REQUIRED`.
  5. Targeted canonical tests pass.
  6. No paper workflow, dev-frame-opencode runtime, or devframe-control-plane runtime is executed.

- **Accepted Limitation**: The original READY target is superseded for this closeout because the user manually closed the real ChatGPT conversation session. A future live pilot must restore fresh independent sessions before claiming READY.
- **Expected Output**: Factual binding artifacts, current Gate 0 and dispatch reports, audit evidence, and an explicit `HUMAN_REQUIRED` verdict.
- **Rollback**: Restore only the files listed in the write set.
- **Report To**: Current session
