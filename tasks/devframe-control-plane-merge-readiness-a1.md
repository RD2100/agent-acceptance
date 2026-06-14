# TaskSpec: devframe-control-plane-merge-readiness-a1

**ID**: devframe-control-plane-merge-readiness-a1
**Priority**: P1
**Status**: completed
**Type**: devframe_system_merge_readiness

## Intent

Determine and record whether `D:\devframe-control-plane` can enter the
`devframe-system` merge admission chain as a clean baseline candidate.

This task is governance-only inside `D:\agent-acceptance`. It must not mutate
`D:\devframe-control-plane`, `D:\dev-frame-opencode`, `D:\test-frame`, or
`D:\devframe-system`. It must not run external runtimes, external repository
tests, builds, package installs, cleanup, reset, stash, or submodule commands.

gate_0:
  triggered: true
  trigger_reason: "devframe-control-plane reached a clean candidate state and needs a devframe-system merge-admission record without physical merge."
  inventory_evidence:
    queried_sources:
      - "D:\\devframe-control-plane git status/rev-parse/diff-check"
      - "_reports/devframe-control-plane-registry-decision-a1/DECISION_PACKET.md"
      - ".agent/PROJECT_REGISTRY.json diff"
      - "docs/agent-runtime/devframe-system-phase05-index.md"
      - "docs/agent-runtime/devframe-system-phase05-handoff-brief.md"
    matched_capabilities:
      - sadp_governance
      - devframe_system_route_governance
      - merge_readiness_reporting
      - registry_migration_human_gate
      - external_runtime_non_execution_gate
  rules_checked: [core-001, core-004, core-005, core-007, core-008, review-001, git-001]
  lessons_checked:
    - "Do not claim physical merge completion from a single clean source repository."
    - "Do not commit registry migration without explicit human authorization."
  sufficiency_decision: existing_sufficient
  decision: reuse
  delta_justification: "This task records status using existing governance/reporting capability only."

conflict_registry:
  read_set:
    - "D:\\devframe-control-plane git status/rev-parse/diff-check output"
    - "_reports/devframe-control-plane-registry-decision-a1/DECISION_PACKET.md"
    - ".agent/PROJECT_REGISTRY.json"
    - "docs/agent-runtime/devframe-system-phase05-index.md"
    - "docs/agent-runtime/devframe-system-phase05-handoff-brief.md"
    - "scripts/qoderwork_task_runner.py"
    - "scripts/sadp_pre_task_enforcer.py"
    - ".ai/current-task.yaml"
    - "hooks/sealed-files-manifest.json"
  write_set:
    - .ai/current-task.yaml
    - tasks/devframe-control-plane-merge-readiness-a1.md
    - _reports/devframe-control-plane-merge-readiness-a1/**
    - _evidence/devframe-control-plane-merge-readiness-a1/**
    - docs/agent-runtime/devframe-system-phase05-index.md
    - docs/agent-runtime/devframe-system-phase05-handoff-brief.md
    - hooks/sealed-files-manifest.json
  governance_adjacent_files_modified:
    - ".ai/current-task.yaml"
    - "docs/agent-runtime/devframe-system-phase05-index.md"
    - "docs/agent-runtime/devframe-system-phase05-handoff-brief.md"
    - "hooks/sealed-files-manifest.json"
  protected_files_touched: true
  protected_file_justification: "hooks/sealed-files-manifest.json is pre-commit auto-regenerated because sealed docs changed; no manual policy change."
  conflict_level: medium

**Acceptance Gates**:
  1. Phase 0 read-only checks prove `D:\devframe-control-plane` is clean and HEAD equals `origin/codex/route-a-baseline-candidate`.
  2. Report conclusion is exactly `READY_AS_CLEAN_BASELINE_CANDIDATE` for `devframe-control-plane`.
  3. Report does not claim `devframe-system` is merged or full-merge ready.
  4. Registry migration remains `HUMAN_REQUIRED` unless explicit approval is provided.
  5. No mutation occurs in `D:\devframe-control-plane`, `D:\dev-frame-opencode`, `D:\test-frame`, or `D:\devframe-system`.
  6. Runner start/edit-check/finish and requested validation commands complete with pass or documented non-blocking warnings.
  7. Any sealed manifest change is limited to pre-commit hash/timestamp regeneration for touched sealed docs.
