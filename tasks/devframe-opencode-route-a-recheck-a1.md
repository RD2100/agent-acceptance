# TaskSpec: devframe-opencode-route-a-recheck-a1

**ID**: devframe-opencode-route-a-recheck-a1
**Priority**: P1
**Status**: completed
**Type**: devframe_system_route_a_readiness_recheck

## Intent

Record the latest read-only Route A merge readiness check after the user
reported that `dev-frame-opencode` should be ready. This task must verify the
current local state instead of trusting the report, and must not mutate any
external repository or start any external runtime.

gate_0:
  triggered: true
  trigger_reason: "User reported dev-frame-opencode completion; Route A readiness needs current-state verification."
  inventory_evidence:
    queried_sources:
      - "D:\\agent-acceptance git status/rev-parse read-only output"
      - "D:\\devframe-control-plane git status/rev-parse read-only output"
      - "D:\\dev-frame-opencode git status/rev-parse read-only output"
      - "D:\\test-frame git status/rev-parse read-only output"
      - "D:\\devframe-system directory read-only output"
      - "scripts/devframe_system_route_a_preflight.py"
      - "_reports/devframe-system-route-a-preflight-a1/MERGE_DASHBOARD.md"
    matched_capabilities:
      - sadp_governance
      - route_a_read_only_preflight
      - merge_readiness_reporting
      - external_runtime_non_execution_gate
  rules_checked: [core-001, core-004, core-005, core-007, core-008, review-001, git-001]
  lessons_checked:
    - "Trust current worktree evidence over delegated completion reports."
    - "Do not claim Route A ready while any source repository is dirty."
    - "Do not mutate external repositories during readiness verification."
  sufficiency_decision: existing_sufficient
  decision: reuse
  delta_justification: "Existing read-only validator plus a scoped report are sufficient."

conflict_registry:
  read_set:
    - "scripts/devframe_system_route_a_preflight.py"
    - "_reports/devframe-system-route-a-preflight-a1/MERGE_DASHBOARD.md"
    - "D:\\agent-acceptance git status/rev-parse read-only output"
    - "D:\\devframe-control-plane git status/rev-parse read-only output"
    - "D:\\dev-frame-opencode git status/rev-parse read-only output"
    - "D:\\test-frame git status/rev-parse read-only output"
    - "D:\\devframe-system directory read-only output"
  write_set:
    - .ai/current-task.yaml
    - tasks/devframe-opencode-route-a-recheck-a1.md
    - _reports/devframe-opencode-route-a-recheck-a1/**
    - _evidence/devframe-opencode-route-a-recheck-a1/**
    - hooks/sealed-files-manifest.json
  governance_adjacent_files_modified:
    - ".ai/current-task.yaml"
    - "hooks/sealed-files-manifest.json"
  protected_files_touched: true
  protected_file_justification: "current task activation and possible sealed manifest refresh are required for commit-time governance."
  conflict_level: medium

**Acceptance Gates**:
  1. Report records current `dev-frame-opencode` branch, HEAD, upstream, dirty counts, and tracked dirty paths.
  2. Report records whether Route A physical merge is authorized by current evidence.
  3. Report explicitly states that no external repository mutation, runtime, tests, cleanup, reset, stash, checkout, or submodule command was executed.
  4. Runner start/edit-check/finish passes.
  5. `git diff --check` passes for staged governance artifacts.
  6. Targeted Route A/preflight tests pass.
