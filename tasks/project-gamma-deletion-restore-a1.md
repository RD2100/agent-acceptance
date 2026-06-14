# TaskSpec: project-gamma-deletion-restore-a1

**ID**: project-gamma-deletion-restore-a1
**Priority**: P1
**Status**: completed
**Type**: scoped_workspace_restore

## Intent

Restore the tracked `_projects/project-gamma/**` deletion set only, because it
is blocking the local `agent-acceptance` Route A readiness baseline and previous
decision packets recommended restore unless the owner explicitly intended the
large governance-heavy deletion.

gate_0:
  triggered: true
  trigger_reason: "User authorized continuing the remaining small merge-readiness items; project-gamma deletion set is a scoped local blocker."
  inventory_evidence:
    queried_sources:
      - "_reports/project-gamma-deletion-decision-a1/DECISION_PACKET.md"
      - "_reports/devframe-system-workspace-risk-triage-a1/WORKSPACE_RISK_TRIAGE.md"
      - "git status --porcelain=v1 -uall -- _projects/project-gamma"
      - "git diff --stat -- _projects/project-gamma"
    matched_capabilities:
      - sadp_governance
      - scoped_workspace_restore
      - route_a_readiness_governance
  rules_checked: [core-001, core-004, core-005, core-008, review-001, git-001]
  lessons_checked:
    - "Do not broad-stage unrelated dirty work."
    - "Resolve local baseline deletion risk before claiming Route A readiness."
    - "Use scoped restore only after confirming every target status entry is a tracked deletion."
  sufficiency_decision: existing_sufficient
  decision: restore
  delta_justification: "Restoring a tracked deletion set is the smallest action that removes this local baseline blocker."

conflict_registry:
  read_set:
    - "_reports/project-gamma-deletion-decision-a1/DECISION_PACKET.md"
    - "_reports/devframe-system-workspace-risk-triage-a1/WORKSPACE_RISK_TRIAGE.md"
    - "git status --porcelain=v1 -uall -- _projects/project-gamma"
    - "git diff --stat -- _projects/project-gamma"
  write_set:
    - .ai/current-task.yaml
    - tasks/project-gamma-deletion-restore-a1.md
    - _projects/project-gamma/**
    - _reports/project-gamma-deletion-restore-a1/**
    - _evidence/project-gamma-deletion-restore-a1/**
    - hooks/sealed-files-manifest.json
  governance_adjacent_files_modified:
    - ".ai/current-task.yaml"
    - "hooks/sealed-files-manifest.json"
  protected_files_touched: true
  protected_file_justification: "The target restore set contains nested governance fixtures by design; no top-level active governance policy is changed."
  conflict_level: medium

**Acceptance Gates**:
  1. Pre-restore evidence proves every `_projects/project-gamma` status entry is a tracked deletion.
  2. Restore operation is scoped to `_projects/project-gamma/**` only.
  3. Post-restore status for `_projects/project-gamma` is clean.
  4. No external repository mutation, runtime execution, cleanup, reset, stash, checkout, submodule command, or paper workflow is performed.
  5. Runner start/edit-check/finish passes.
  6. `git diff --check` and targeted Route A/router tests pass.
