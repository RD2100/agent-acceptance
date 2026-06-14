# TaskSpec: DEVFRAME-SYSTEM-ROUTE-DECISION-PACKET-A1

**ID**: devframe-system-route-decision-packet-a1
**Priority**: P1
**Status**: in_progress
**Type**: governance_route_decision_packet

## Intent

Create a human-facing route decision packet for the future `devframe-system`
superproject. The packet must translate the existing activation gates into
copy-ready approval, rejection, and deferral language without selecting a route,
creating `D:\devframe-system`, adding submodules, executing external runtimes,
or mutating external repositories.

gate_0:
  triggered: true
  trigger_reason: "Continue Phase 0.5 by making Route A / Route B selection auditable and copy-ready."
  inventory_evidence:
    queried_sources:
      - "docs/agent-runtime/devframe-system-activation-gates.md"
      - "_reports/devframe-system-activation-gates-a1/ACTIVATION_GATES_REPORT.md"
      - "_reports/devframe-system-contract-only-plan-a1/CONTRACT_ONLY_PLAN.md"
      - "_reports/devframe-system-phase05-readiness-rollup-a1/READINESS_ROLLUP.md"
    matched_capabilities:
      - sadp_governance
      - route_decision_documentation
      - human_gate_recording
      - external_runtime_non_execution_gate
  rules_checked: [core-001, core-004, core-005, core-007, core-008, review-001, git-001]
  sufficiency_decision: existing_sufficient
  decision: reuse
  delta_justification: "The task creates governance documentation only and does not execute either bootstrap route."

conflict_registry:
  read_set:
    - "docs/agent-runtime/devframe-system-activation-gates.md"
    - "_reports/devframe-system-activation-gates-a1/ACTIVATION_GATES_REPORT.md"
    - "_reports/devframe-system-contract-only-plan-a1/CONTRACT_ONLY_PLAN.md"
    - "_reports/devframe-system-phase05-readiness-rollup-a1/READINESS_ROLLUP.md"
    - ".ai/current-task.yaml"
  write_set:
    - tasks/devframe-system-route-decision-packet-a1.md
    - .ai/current-task.yaml
    - docs/agent-runtime/devframe-system-route-decision-packet.md
    - _reports/devframe-system-route-decision-packet-a1/**
    - _evidence/DEVFRAME-SYSTEM-ROUTE-DECISION-PACKET-A1/**
    - hooks/sealed-files-manifest.json
    - _evidence/hook-output/**
  governance_adjacent_files_modified:
    - ".ai/current-task.yaml"
    - "docs/agent-runtime/devframe-system-route-decision-packet.md"
  protected_files_touched: false
  conflict_level: medium

**Acceptance Gates**:
  1. Runner start, edit-check, and finish complete without blocking.
  2. Decision packet provides copy-ready choices for Route A, Route B, and continue contract-only planning.
  3. Route B language explicitly forbids submodule add, external runtime execution, cleanup/reset/stash, and trusted-baseline claims.
  4. Packet states `test-frame` is a controlled verification runtime candidate, not a plugin and not GateResult authority.
  5. No `D:\devframe-system` directory is created and no external repository is mutated.
  6. Targeted checks pass and staged commit contains only this decision-packet package plus hook-managed manifest.
