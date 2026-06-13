# TaskSpec: PRODUCTION-READINESS-AUTOMATION-A1 - Formal-Use Readiness Gate

- **ID**: PRODUCTION-READINESS-AUTOMATION-A1
- **Batch**: production-readiness
- **Risk**: high
- **Priority**: P0
- **Goal**: Add a fail-closed, machine-checkable readiness gate that distinguishes local governance readiness, controlled multi-GPT pilot readiness, and formal production-use readiness.
- **Context**: Local tests and governance are green, but the repository has no single authoritative gate combining canonical tests, current Gate 0 state, dispatch state, real independent pilot evidence, and explicit production-promotion authorization. Historical reports contain stale claims and must not be used as authority.
- **Allowed Files**:
  - tasks/production-readiness-automation-a1.md
  - .ai/current-task.yaml
  - scripts/production_readiness_gate.py
  - scripts/multi_agent_gate0_preflight.py
  - scripts/multi_agent_dispatch_plan.py
  - schemas/agent-runtime/multi-agent-gate0-preflight.schema.json
  - schemas/agent-runtime/multi-agent-dispatch-plan.schema.json
  - tests/test_production_readiness_gate.py
  - tests/test_multi_agent_gate0_preflight.py
  - tests/test_multi_agent_dispatch_plan.py
  - docs/agent-runtime/production-readiness.md
  - .ai/verify-matrix.yaml
  - _reports/production-readiness-automation-a1/**
  - _reports/multi-agent-gate0-preflight-a1/PREFLIGHT_CURRENT.json
  - _reports/multi-agent-dispatch-plan-a1/DISPATCH_PLAN.json
  - _reports/multi-agent-dispatch-plan-a1/DISPATCH_PLAN_CURRENT.json
  - _evidence/PRODUCTION-READINESS-AUTOMATION-A1/**
  - hooks/sealed-files-manifest.json
  - _evidence/hook-output/**
- **Forbidden**:
  - No paper workflow execution or edits to paper authorization
  - No opencode run, WorkQueue consumption, cross-repo smoke, or external runtime execution without a separate run-bound human authorization record
  - No fabricated authorization, live-session, reviewer, pilot, or production-promotion evidence
  - No cleanup or mutation of unrelated dirty baseline artifacts
  - No weakening of existing Gate 0, dispatch, secret, or independent-review controls

- **Gate 0 Ledger**:
  ```yaml
  gate_0:
    triggered: true
    trigger_reason: "P0 formal-use readiness and fake-green prevention"
    inventory_evidence:
      queried_sources:
        - docs/agent-runtime/minimum-capability-set.md
        - docs/MULTI_AGENT_MULTI_GPT_PILOT_PLAN.md
        - scripts/multi_agent_gate0_preflight.py
        - scripts/multi_agent_dispatch_plan.py
        - _reports/multi-agent-multi-gpt-pilot-a1/PILOT_EXECUTION_REPORT.md
        - D:/dev-frame-opencode/PRODUCTION_PROMOTION_CRITERIA.md
      matched_capabilities:
        - local governance verification
        - multi-agent Gate 0 preflight
        - multi-agent dispatch planning
        - independent reviewer evidence
        - production promotion authorization
      compared_against_request:
        - "automate until formal use"
        - "real multi-agent and multi-GPT proof"
        - "fail-closed production readiness"
    rules_checked: [core-004, core-007, core-008, review-001]
    lessons_checked: [LL-independent-review-evidence, LL-structured-task-spec]
    sufficiency_decision: existing_partial
    decision: build_delta
    delta_justification: "Existing checks cover individual layers but no authoritative gate composes them into a formal-use decision."
  ```

- **Conflict Registry**:
  ```yaml
  conflict_registry:
    read_set:
      - docs/agent-runtime/minimum-capability-set.md
      - docs/MULTI_AGENT_MULTI_GPT_PILOT_PLAN.md
      - scripts/multi_agent_gate0_preflight.py
      - scripts/multi_agent_dispatch_plan.py
      - schemas/agent-runtime/execution-report.schema.json
      - _reports/multi-agent-multi-gpt-pilot-a1/
      - D:/dev-frame-opencode/PRODUCTION_PROMOTION_CRITERIA.md
    write_set:
      - tasks/production-readiness-automation-a1.md
      - .ai/current-task.yaml
      - scripts/production_readiness_gate.py
      - scripts/multi_agent_gate0_preflight.py
      - scripts/multi_agent_dispatch_plan.py
      - schemas/agent-runtime/multi-agent-gate0-preflight.schema.json
      - schemas/agent-runtime/multi-agent-dispatch-plan.schema.json
      - tests/test_production_readiness_gate.py
      - tests/test_multi_agent_gate0_preflight.py
      - tests/test_multi_agent_dispatch_plan.py
      - docs/agent-runtime/production-readiness.md
      - .ai/verify-matrix.yaml
      - _reports/production-readiness-automation-a1/**
      - _reports/multi-agent-gate0-preflight-a1/PREFLIGHT_CURRENT.json
      - _reports/multi-agent-dispatch-plan-a1/DISPATCH_PLAN.json
      - _reports/multi-agent-dispatch-plan-a1/DISPATCH_PLAN_CURRENT.json
      - _evidence/PRODUCTION-READINESS-AUTOMATION-A1/**
      - hooks/sealed-files-manifest.json
      - _evidence/hook-output/**
    protected_files_touched: true
    conflict_level: medium
  ```

- **Acceptance Gates**:
  1. Local-governance mode is READY only when canonical and stress verification evidence is current and passing.
  2. Controlled-pilot mode is HUMAN_REQUIRED unless current Gate 0 is PASS and dispatch status is READY.
  3. Formal-use mode is HUMAN_REQUIRED unless a real two-session pilot passed independent review and explicit production-promotion authorization is current.
  4. Missing, malformed, stale, contradictory, or repo-escaping evidence fails closed with structured diagnostics.
  5. Historical narrative reports cannot satisfy machine evidence requirements.
  6. Existing Priority 5/6 claims are tested against current code before any edit; already-fixed items are recorded, not rewritten.
  7. CAP-009 numbering and unknown-passport semantics are reported as protected-document debt; unavailable capabilities cannot satisfy readiness.
  8. The cumulative-trigger wording conflict is reported without bypassing the protected-file lock.
  9. Real task-runner probes cover allowed edit, forbidden edit, and finish artifact enforcement.
  10. Canonical tests pass with zero failures and independent review has no unresolved P0/P1 findings.

- **Expected Output**: Readiness gate, focused tests and docs, current structured readiness artifacts, real-path runner evidence, Reviewer Index, independent ChatGPT review, and final execution report.
- **Rollback**: Revert only this task's tracked diff; preserve unrelated worktree artifacts and historical evidence.
- **Report To**: ChatGPT conversation 6a297f76-3e7c-83a5-a0e5-b4413d923c7e
