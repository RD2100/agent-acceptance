# TaskSpec: DEVFRAME-SYSTEM-PHASE05-ROUTE-PROMPT-SOURCE-REFRESH-A1

**ID**: devframe-system-phase05-route-prompt-source-refresh-a1
**Priority**: P1
**Status**: completed
**Type**: governance_route_prompt_source_refresh

## Intent

Refresh the route decision packet so future GPT-5.5 Pro or agent prompts use
the latest freshness snapshot for repository facts. The readiness rollup remains
owner-action context, but it should not be the only source listed for physical
bootstrap readiness decisions.

The task must stay inside `D:\agent-acceptance`. It must not create
`D:\devframe-system`, add submodules, run external runtimes/tests/builds/package
installs, run paper workflow, or mutate external repositories.

gate_0:
  triggered: true
  trigger_reason: "The route decision packet still points GPT-5.5 Pro primarily at the older readiness rollup after the freshness snapshot became the latest source-status record."
  inventory_evidence:
    queried_sources:
      - "docs/agent-runtime/devframe-system-route-decision-packet.md"
      - "docs/agent-runtime/devframe-system-phase05-index.md"
      - "_reports/devframe-system-phase05-freshness-snapshot-a1/FRESHNESS_SNAPSHOT.md"
      - "_reports/devframe-system-phase05-readiness-rollup-a1/READINESS_ROLLUP.md"
    matched_capabilities:
      - sadp_governance
      - route_decision_prompting
      - documentation_navigation
      - external_runtime_non_execution_gate
  rules_checked: [core-001, core-004, core-005, core-007, core-008, review-001, git-001]
  sufficiency_decision: existing_sufficient
  decision: reuse
  delta_justification: "The task updates governance documentation only and does not require new runtime capability."

conflict_registry:
  read_set:
    - "docs/agent-runtime/devframe-system-route-decision-packet.md"
    - "docs/agent-runtime/devframe-system-phase05-index.md"
    - "_reports/devframe-system-phase05-freshness-snapshot-a1/FRESHNESS_SNAPSHOT.md"
    - "_reports/devframe-system-phase05-readiness-rollup-a1/READINESS_ROLLUP.md"
    - ".ai/current-task.yaml"
  write_set:
    - tasks/devframe-system-phase05-route-prompt-source-refresh-a1.md
    - .ai/current-task.yaml
    - docs/agent-runtime/devframe-system-route-decision-packet.md
    - _reports/devframe-system-phase05-route-prompt-source-refresh-a1/**
    - _evidence/DEVFRAME-SYSTEM-PHASE05-ROUTE-PROMPT-SOURCE-REFRESH-A1/**
    - hooks/sealed-files-manifest.json
    - _evidence/hook-output/**
  governance_adjacent_files_modified:
    - ".ai/current-task.yaml"
    - "docs/agent-runtime/devframe-system-route-decision-packet.md"
  protected_files_touched: false
  conflict_level: medium

**Acceptance Gates**:
  1. Runner start, edit-check, and finish complete without blocking.
  2. Route decision packet names the freshness snapshot as the latest repository-fact source.
  3. GPT-5.5 Pro minimum prompt includes the freshness snapshot and treats readiness rollup as owner-action context.
  4. Verdict remains HUMAN_REQUIRED and no physical bootstrap/runtime/submodule/paper workflow action is performed.
  5. Targeted checks pass and staged commit contains only this route-prompt refresh package plus hook-managed manifest.
