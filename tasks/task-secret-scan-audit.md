# TaskSpec: task-secret-scan-audit

- **task_id**: task-secret-scan-audit
- **title**: Enhance sadp-audit.ps1 with secret scanning rules
- **priority**: P0
- **status**: ready
- **description**: Add RULE 5 (secret pattern detection) and RULE 6 (.env.example integrity) to sadp-audit.ps1. The script currently has 4 rules covering TaskSpec/governance but is missing the secret scanning rules referenced by AGENTS.md Agent Secret Safety Rules #4 and SECURITY_SECRETS_POLICY.md §5. This gap means pre-commit hook cannot actually block secrets from being committed.

## gate_0
- **triggered**: true
- **trigger_reason**: AGENTS.md Security Rules reference sadp-audit.ps1 but script lacks secret scanning
- **inventory_evidence**:
  - queried_sources: [sadp-audit.ps1, SECURITY_SECRETS_POLICY.md, AGENTS.md, dependency-canaries.md]
  - matched_capabilities: [CAP-005: Pre-commit hooks, sadp-audit.ps1]
  - unmatched_gaps: [Secret pattern detection in pre-commit audit]
- **sufficiency_decision**: existing_partial
- **decision**: build_delta
- **delta_justification**: sadp-audit.ps1 exists with 4 rules (file count, governance, strict, TaskSpec coverage) but needs 2 new rules: secret pattern scan (RULE 5) and .env.example integrity (RULE 6). This is a surgical addition, not a rewrite.

## conflict_registry
- **read_set**: [scripts/sadp-audit.ps1, docs/SECURITY_SECRETS_POLICY.md, AGENTS.md]
- **write_set**: [scripts/sadp-audit.ps1]
- **protected_files_touched**: false
- **conflict_level**: none

## security_report
- **new_external_api**: false
- **new_env_variable**: false
- **env_example_placeholders_only**: true
- **real_key_patterns_found**: false
- **staged_diff_secret_scan_run**: true
- **key_rotation_needed**: false
