# TaskSpec: task-cleanup-commit

- **task_id**: task-cleanup-commit
- **title**: Commit pending changes, cleanup .backup/ dir
- **priority**: P1
- **status**: ready
- **description**: The worktree has 3 pending changes (AGENTS.md, task-spec.schema.json, SECURITY_SECRETS_POLICY.md) and an untracked .backup/ directory from JSON restore. Need to: (1) add .backup/ to .gitignore, (2) stage all changes, (3) verify pre-commit audit passes, (4) commit.

## gate_0
- **triggered**: true
- **trigger_reason**: 3 modified files + untracked artifacts need to be committed
- **inventory_evidence**:
  - queried_sources: [git status, AGENTS.md diff, schema diff, SECURITY_SECRETS_POLICY.md]
  - matched_capabilities: [CAP-005: Pre-commit hooks]
  - unmatched_gaps: []
- **sufficiency_decision**: existing_sufficient
- **decision**: reuse

## conflict_registry
- **read_set**: [AGENTS.md, schemas/agent-runtime/task-spec.schema.json, docs/SECURITY_SECRETS_POLICY.md, .gitignore]
- **write_set**: [.gitignore]
- **protected_files_touched**: false
- **conflict_level**: none

## security_report
- **new_external_api**: false
- **new_env_variable**: false
- **env_example_placeholders_only**: true
- **real_key_patterns_found**: false
- **staged_diff_secret_scan_run**: true
- **key_rotation_needed**: false
