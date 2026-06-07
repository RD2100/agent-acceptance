task_id: GROUP-06
task_name: VALIDATE-WORKFLOW-CLOSURE-CONTROL-PLANE-PATTERN
primary_repo: agent-acceptance
review_origin: DIRTY-WORKTREE-SPLIT-A1 triage
status: ready_for_review
final_status: ready_for_review

# GROUP-06 Closure Report

This pack isolates a small validator hardening change.

Scope:
- scripts/validate_workflow_closure.py
- tests/test_workflow_closure_validation.py

Change intent:
- Treat `control_plane/` files as actual deliverables during workflow closure validation.
- Add targeted test coverage proving `control_plane/stage_executor.py` is counted as an actual deliverable.

Exclusions:
- no historical runs changes
- no HANDOFF deletion
- no archive hooks
- no tools governance files
- no memory outputs
- no paper validator residuals
- no tmp/cache/root scratch files
