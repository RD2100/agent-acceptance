# Devframe-System Route Approval Record Template

Status: template only
Default verdict without completed record: HUMAN_REQUIRED
Related worksheet: `docs/agent-runtime/devframe-system-route-decision-worksheet.md`

## Purpose

Use this template when a human explicitly chooses a `devframe-system` Phase 0.5
route. A blank or partially filled copy is not approval. Approval exists only
when a human decision record is filled with a concrete route and stored as
evidence.

This template does not authorize any action by itself.

## Copy-Ready Approval Record

```yaml
approval_record_id: DEVFRAME-SYSTEM-ROUTE-APPROVAL-YYYYMMDD-A1
record_type: human_route_approval
status: pending_human_signature
created_at: YYYY-MM-DDTHH:MM:SS+08:00
human_decision_source: "<chat message, signed note, or explicit instruction reference>"

route_selection:
  exact_route_name: "<CONTINUE_CONTRACT_ONLY_PLANNING | ROUTE_A_STRICT_CLEAN_BASELINE | ROUTE_B_DIRTY_AWARE_SKELETON>"
  rationale: "<why this route is selected now>"

allowed_file_system_scope:
  agent_acceptance: "allowed for governance records"
  devframe_system_creation_authorized: false
  devframe_system_path: "D:\\devframe-system"
  external_source_repos_mutation_authorized: false
  notes: "<scope limits or extra constraints>"

submodule_status:
  git_submodule_add_authorized: false
  gitmodules_creation_authorized: false
  trusted_submodule_baseline_claim_authorized: false

runtime_gate_status:
  external_runtime_execution_authorized: false
  external_tests_builds_package_installs_authorized: false
  paper_workflow_authorized: false
  runtime_execution_requires_separate_request: true

source_frame_authority:
  agent_acceptance: "local governance source of truth"
  dev_frame_opencode: "execution runtime candidate, no GateResult authority"
  devframe_control_plane: "control plane candidate, no GateResult authority"
  test_frame: "controlled verification runtime candidate, evidence-only until separately approved"
  devframe_system: "future superproject control surface, no authority until activated"

required_preflight_before_action:
  route_a_clean_baseline_required: true
  route_b_dirty_snapshot_required: true
  latest_source_status_artifact: "_reports/devframe-system-phase05-freshness-snapshot-a1/FRESHNESS_SNAPSHOT.md"
  stop_if_source_repo_dirty_for_route_a: true

explicit_non_authorizations:
  cleanup_reset_stash_checkout_delete_authorized: false
  source_repo_stage_commit_authorized: false
  secret_reading_authorized: false
  destructive_git_authorized: false

human_signature:
  approved_by: "<human name or account>"
  approved_at: YYYY-MM-DDTHH:MM:SS+08:00
  approval_text: "<exact human approval text>"
```

## Validity Rules

- `exact_route_name` must be one of the route names from the worksheet.
- `devframe_system_creation_authorized` can be `true` only for an explicitly
  approved Route A or Route B record.
- `git_submodule_add_authorized` must remain `false` unless a later separate
  human approval names submodule operations.
- `external_runtime_execution_authorized` must remain `false` unless a later
  separate `RuntimeExecutionRequest` or successor record authorizes execution.
- `test_frame` must remain evidence-only until a separate approved run exists.
- Route A must stop if any source repository is dirty.
- Route B must not claim trusted baselines.

## Storage Guidance

Store filled records in a route-specific evidence or report directory, not by
overwriting this template. The filled record path must be referenced from the
TaskSpec and execution report for the route activation task.
