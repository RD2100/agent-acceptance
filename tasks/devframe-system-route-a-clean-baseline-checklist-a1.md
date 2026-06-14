# TaskSpec: DEVFRAME-SYSTEM-ROUTE-A-CLEAN-BASELINE-CHECKLIST-A1

**ID**: devframe-system-route-a-clean-baseline-checklist-a1
**Priority**: P1
**Status**: in_progress
**Type**: governance_noop_clean_baseline_checklist

## Intent

Create a no-op clean-baseline checklist for future Route A strict clean-baseline
bootstrap and add it to the Phase 0.5 navigation index. The checklist must
describe how to verify source baselines without creating `D:\devframe-system`,
adding submodules, executing external runtimes, or mutating external
repositories.

gate_0:
  triggered: true
  trigger_reason: "Continue Phase 0.5 by creating the Route A counterpart to the Route B no-op checklist."
  inventory_evidence:
    queried_sources:
      - "docs/agent-runtime/devframe-system-phase05-index.md"
      - "docs/agent-runtime/devframe-system-activation-gates.md"
      - "docs/agent-runtime/devframe-system-route-decision-packet.md"
      - "docs/agent-runtime/devframe-system-route-b-noop-dry-run.md"
    matched_capabilities:
      - sadp_governance
      - route_a_baseline_planning
      - human_gate_recording
      - external_runtime_non_execution_gate
  rules_checked: [core-001, core-004, core-005, core-007, core-008, review-001, git-001]
  sufficiency_decision: existing_sufficient
  decision: reuse
  delta_justification: "The task creates no-op governance documentation only and does not execute Route A."

conflict_registry:
  read_set:
    - "docs/agent-runtime/devframe-system-phase05-index.md"
    - "docs/agent-runtime/devframe-system-activation-gates.md"
    - "docs/agent-runtime/devframe-system-route-decision-packet.md"
    - "docs/agent-runtime/devframe-system-route-b-noop-dry-run.md"
    - ".ai/current-task.yaml"
  write_set:
    - tasks/devframe-system-route-a-clean-baseline-checklist-a1.md
    - .ai/current-task.yaml
    - docs/agent-runtime/devframe-system-phase05-index.md
    - docs/agent-runtime/devframe-system-route-a-clean-baseline-checklist.md
    - _reports/devframe-system-route-a-clean-baseline-checklist-a1/**
    - _evidence/DEVFRAME-SYSTEM-ROUTE-A-CLEAN-BASELINE-CHECKLIST-A1/**
    - hooks/sealed-files-manifest.json
    - _evidence/hook-output/**
  governance_adjacent_files_modified:
    - ".ai/current-task.yaml"
    - "docs/agent-runtime/devframe-system-phase05-index.md"
    - "docs/agent-runtime/devframe-system-route-a-clean-baseline-checklist.md"
  protected_files_touched: false
  conflict_level: medium

**Acceptance Gates**:
  1. Runner start, edit-check, and finish complete without blocking.
  2. Checklist is explicitly no-op and does not authorize Route A execution.
  3. Checklist contains baseline input, clean-state decision, pass/fail, evidence, and abort sections.
  4. Checklist forbids directory creation, submodule commands, runtime execution, external tests/builds, cleanup/reset/stash, and trusted-baseline claims from dirty repos.
  5. Phase 0.5 index links the new Route A checklist.
  6. No `D:\devframe-system` directory is created and no external repository is mutated.
