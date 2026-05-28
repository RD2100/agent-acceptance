# TaskSpec: task-canary-verification

- **task_id**: task-canary-verification
- **title**: Run dependency canary tests (CANARY-001 through CANARY-004)
- **priority**: P1
- **status**: ready
- **description**: Execute the 4 dependency canaries defined in dependency-canaries.md to verify model behavior, CLI compatibility, and schema compliance. Canaries were defined but never executed in current session.

## gate_0
- **triggered**: true
- **trigger_reason**: Canaries defined but never run; pre-governance-change verification required
- **inventory_evidence**:
  - queried_sources: [dependency-canaries.md, dispatch-model-profiles.md]
  - matched_capabilities: [CAP-004: SADP, dependency-canaries.md]
  - unmatched_gaps: []
- **sufficiency_decision**: existing_sufficient
- **decision**: reuse

## conflict_registry
- **read_set**: [docs/agent-runtime/dependency-canaries.md]
- **write_set**: [tasks/canary-results.md]
- **protected_files_touched**: false
- **conflict_level**: none

## security_report
- **new_external_api**: false
- **new_env_variable**: false
- **env_example_placeholders_only**: true
- **real_key_patterns_found**: false
- **staged_diff_secret_scan_run**: true
- **key_rotation_needed**: false
