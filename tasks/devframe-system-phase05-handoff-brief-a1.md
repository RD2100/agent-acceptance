# TaskSpec: DEVFRAME-SYSTEM-PHASE05-HANDOFF-BRIEF-A1

**ID**: devframe-system-phase05-handoff-brief-a1
**Priority**: P1
**Status**: in_progress
**Type**: governance_handoff_brief

## Intent

Create a concise handoff brief for GPT-5.5 Pro or a future agent to continue
the devframe-system Phase 0.5 work safely. The brief must point to the canonical
index, summarize the current `HUMAN_REQUIRED` state, include copy-ready next
agent instructions, and preserve all non-execution boundaries.

gate_0:
  triggered: true
  trigger_reason: "Continue Phase 0.5 by packaging the current governance state into a compact handoff brief."
  inventory_evidence:
    queried_sources:
      - "docs/agent-runtime/devframe-system-phase05-index.md"
      - "docs/agent-runtime/devframe-system-route-decision-packet.md"
      - "docs/agent-runtime/devframe-system-route-a-clean-baseline-checklist.md"
      - "docs/agent-runtime/devframe-system-route-b-noop-dry-run.md"
    matched_capabilities:
      - sadp_governance
      - handoff_documentation
      - human_gate_recording
      - external_runtime_non_execution_gate
  rules_checked: [core-001, core-004, core-005, core-007, core-008, review-001, git-001]
  sufficiency_decision: existing_sufficient
  decision: reuse
  delta_justification: "The task creates a documentation handoff only and does not execute any bootstrap route."

conflict_registry:
  read_set:
    - "docs/agent-runtime/devframe-system-phase05-index.md"
    - "docs/agent-runtime/devframe-system-route-decision-packet.md"
    - "docs/agent-runtime/devframe-system-route-a-clean-baseline-checklist.md"
    - "docs/agent-runtime/devframe-system-route-b-noop-dry-run.md"
    - ".ai/current-task.yaml"
  write_set:
    - tasks/devframe-system-phase05-handoff-brief-a1.md
    - .ai/current-task.yaml
    - docs/agent-runtime/devframe-system-phase05-index.md
    - docs/agent-runtime/devframe-system-phase05-handoff-brief.md
    - _reports/devframe-system-phase05-handoff-brief-a1/**
    - _evidence/DEVFRAME-SYSTEM-PHASE05-HANDOFF-BRIEF-A1/**
    - hooks/sealed-files-manifest.json
    - _evidence/hook-output/**
  governance_adjacent_files_modified:
    - ".ai/current-task.yaml"
    - "docs/agent-runtime/devframe-system-phase05-index.md"
    - "docs/agent-runtime/devframe-system-phase05-handoff-brief.md"
  protected_files_touched: false
  conflict_level: medium

**Acceptance Gates**:
  1. Runner start, edit-check, and finish complete without blocking.
  2. Handoff brief identifies the canonical index and current default as `HUMAN_REQUIRED`.
  3. Handoff brief includes copy-ready next-agent instructions and the exact forbidden actions.
  4. Handoff brief preserves `test-frame` as controlled verification runtime candidate, not plugin and not GateResult authority.
  5. Phase 0.5 index links the handoff brief.
  6. No `D:\devframe-system` directory is created and no external repository is mutated.
