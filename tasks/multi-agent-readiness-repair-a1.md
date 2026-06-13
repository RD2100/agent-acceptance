# TaskSpec: MULTI-AGENT-READINESS-REPAIR-A1 - Readiness Semantics Repair

- **ID**: MULTI-AGENT-READINESS-REPAIR-A1
- **Batch**: multi-agent-readiness
- **Risk**: high
- **Priority**: P0
- **Goal**: Remove false-positive multi-agent readiness, restore strict TaskSpec validation, and produce independently reviewable evidence before any real multi-GPT pilot.
- **Context**: Commit 10d9515 reports Gate0 PASS and dispatch READY although live CDP evidence and run-bound authorization are absent. The same commit relaxed the canonical TaskSpec schema with additionalProperties=true.
- **Allowed Files**:
  - tasks/multi-agent-readiness-repair-a1.md
  - .ai/current-task.yaml
  - scripts/multi_agent_gate0_preflight.py
  - scripts/multi_agent_dispatch_plan.py
  - scripts/validate_execution_report.py
  - schemas/agent-runtime/task-spec.schema.json
  - schemas/agent-runtime/multi-agent-dispatch-plan.schema.json
  - schemas/agent-runtime/execution-report.schema.json
  - tests/test_multi_agent_gate0_preflight.py
  - tests/test_multi_agent_dispatch_plan.py
  - tests/test_validate_multi_agent_dispatch_plan.py
  - tests/test_governance_consistency.py
  - tests/test_execution_report_schema.py
  - tests/test_validate_execution_report.py
  - docs/agent-runtime/integration-contracts.md
  - _reports/multi-agent-multi-gpt-pilot-a1/ACTIVATION_RECORD.json
  - _reports/multi-agent-gate0-preflight-a1/GATE0_PREFLIGHT.json
  - _reports/multi-agent-dispatch-plan-a1/DISPATCH_PLAN.json
  - _reports/multi-agent-readiness-repair-a1/**
  - _evidence/MULTI-AGENT-READINESS-REPAIR-A1/**
  - hooks/sealed-files-manifest.json
  - _evidence/hook-output/**
- **Forbidden**:
  - No opencode, live CDP, cross-repo smoke, or paper workflow execution
  - No fabricated authorization, session verification, reviewer identity, or PASS verdict
  - No package installation or MCP configuration changes
  - No edits to unrelated dirty baseline files or archived evidence chains

- **Gate 0 Ledger**:
  ```yaml
  gate_0:
    triggered: true
    trigger_reason: "P0 fake-readiness risk in multi-agent authorization and dispatch state"
    inventory_evidence:
      queried_sources:
        - scripts/multi_agent_gate0_preflight.py
        - scripts/multi_agent_dispatch_plan.py
        - schemas/agent-runtime/task-spec.schema.json
        - schemas/agent-runtime/execution-report.schema.json
        - docs/agent-runtime/tool-policy.md
        - _reports/multi-agent-multi-gpt-pilot-a1/ACTIVATION_RECORD.json
      matched_capabilities:
        - multi-agent-gate0-preflight
        - multi-agent-dispatch-plan
        - SADP TaskSpec validation
        - independent reviewer evidence
      compared_against_request:
        - "run-bound human authorization"
        - "live independent session evidence"
        - "fail-closed dispatch readiness"
        - "independent ChatGPT review"
    rules_checked: [core-004, core-007, core-008, review-001]
    lessons_checked: [LL-independent-review-evidence, LL-structured-task-spec]
    sufficiency_decision: existing_partial
    decision: build_delta
    delta_justification: "Existing checks validate declarations but not current-run authority or live session evidence."
  ```

- **Conflict Registry**:
  ```yaml
  conflict_registry:
    read_set:
      - scripts/multi_agent_gate0_preflight.py
      - scripts/multi_agent_dispatch_plan.py
      - scripts/validate_execution_report.py
      - schemas/agent-runtime/
      - tests/
      - docs/agent-runtime/tool-policy.md
      - _reports/multi-agent-multi-gpt-pilot-a1/ACTIVATION_RECORD.json
    write_set:
      - tasks/multi-agent-readiness-repair-a1.md
      - .ai/current-task.yaml
      - scripts/multi_agent_gate0_preflight.py
      - scripts/multi_agent_dispatch_plan.py
      - scripts/validate_execution_report.py
      - schemas/agent-runtime/task-spec.schema.json
      - schemas/agent-runtime/multi-agent-dispatch-plan.schema.json
      - schemas/agent-runtime/execution-report.schema.json
      - tests/test_multi_agent_gate0_preflight.py
      - tests/test_multi_agent_dispatch_plan.py
      - tests/test_validate_multi_agent_dispatch_plan.py
      - tests/test_governance_consistency.py
      - tests/test_execution_report_schema.py
      - tests/test_validate_execution_report.py
      - docs/agent-runtime/integration-contracts.md
      - _reports/multi-agent-multi-gpt-pilot-a1/ACTIVATION_RECORD.json
      - _reports/multi-agent-gate0-preflight-a1/GATE0_PREFLIGHT.json
      - _reports/multi-agent-dispatch-plan-a1/DISPATCH_PLAN.json
      - _reports/multi-agent-readiness-repair-a1/**
      - _evidence/MULTI-AGENT-READINESS-REPAIR-A1/**
      - hooks/sealed-files-manifest.json
      - _evidence/hook-output/**
    protected_files_touched: true
    conflict_level: high
  ```

- **Acceptance Gates**:
  1. Missing or stale run-bound authorization yields HUMAN_REQUIRED.
  2. Active declarations without live independent session evidence yield HUMAN_REQUIRED.
  3. Dispatch cannot be READY while required human-gated assignments remain deferred or blocked.
  4. Canonical TaskSpec JSON rejects unknown or misspelled fields.
  5. Generated security reports default to not_run rather than implying a completed scan.
  6. Missing or malformed preflight JSON produces a structured BLOCKED result, not a traceback.
  7. Accepted ExecutionReport reviewer evidence identifies distinct executor and reviewer identities.
  8. Real CLI probes reproduce the original false-positive paths and now fail closed.
  9. Canonical tests/ suite passes with zero failures.
  10. Independent reviewer in the specified ChatGPT conversation returns no unresolved P0/P1 findings.

- **Expected Output**: Focused code/schema/test changes, regenerated HUMAN_REQUIRED artifacts, raw verification evidence, Reviewer Index, independent review response, and final execution report.
- **Rollback**: Revert only this task's tracked diff; do not clean or reset unrelated worktree artifacts.
- **Report To**: ChatGPT conversation 6a297f76-3e7c-83a5-a0e5-b4413d923c7e
