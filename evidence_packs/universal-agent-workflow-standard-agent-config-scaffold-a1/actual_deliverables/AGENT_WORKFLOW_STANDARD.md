# Agent Workflow Standard Protocol (AWSP) v1.2.0

## Purpose

Defines the canonical workflow for agent hardening tasks across any project.
Ensures consistency across all evidence packs, GPT review submissions, and verification steps.
Designed for cross-project use via parameterized validators and scaffold tool.

## Core Principles

1. **Run-ID Consistency**: All run_id values MUST be identical across:
   - Evidence pack filename (e.g., `TASK_ID_20260609T140149_RD.zip`)
   - `run_id.txt` and `R1_RUN_ID.txt` content
   - GPT review prompt `{{RUN_ID}}` substitution (including Expected Verdict Format section)
   - GPT reply `run_id:` field

2. **Evidence Pack Standard**: Every pack MUST include:
   - `PACK_MANIFEST.md` with proper markdown table (Path, Role, SHA-256, Size)
   - All evidence files listed in manifest
   - PACK_MANIFEST.md itself listed as `core` role

3. **Prompt Template Standard** (v1.1.0): Every GPT review prompt MUST:
   - Use `{{RUN_ID}}` template variable (not hardcoded run_id)
   - Include `{{TASK_ID}}` template variable
   - Contain `END_OF_GPT_RESPONSE` marker
   - Use `overall_judgment:` field name (not `verdict:`)

4. **Verification Standard**: After GPT reply:
   - Verify run_id in reply matches submitted run_id
   - Verify `END_OF_GPT_RESPONSE` marker present
   - Create GPT_REVIEW_RECORD_Rn.json with full metadata

## Run-ID Generation

```
{TASK_ID_UNDERSCORE}_{YYYYMMDD}T{HHMMSS}_RD
```

Where:
- `TASK_ID_UNDERSCORE`: Task ID with hyphens replaced by underscores, uppercase
- Timestamp: CST (UTC+8) at pack build time
- Suffix: `_RD` (Review Deliverable)

## Prompt Template Fix

The Expected Verdict Format section MUST use:
```
run_id: {{RUN_ID}}
```
NOT a hardcoded run_id value.

## Cross-Project Support (v1.1.0)

### Parameterized Validator

`validate_run_id_consistency.py` accepts an optional `config` dict:
```python
result = validate_run_id_consistency(report_dir, config={
    "evidence_pack_dir": "/path/to/packs/task-a1/"
})
```

CLI usage:
```bash
python scripts/validate_run_id_consistency.py \
    --report-dir _reports/task-a1/ \
    --evidence-pack-dir evidence_packs/task-a1/
```

### AWSP Scaffold

`awsp_scaffold.py` generates AWSP-compliant project structure:
```bash
# Create scaffold:
python scripts/awsp_scaffold.py --project-root /path/to/project

# Validate existing scaffold:
python scripts/awsp_scaffold.py --project-root /path/to/project --validate
```

Generated structure:
- `evidence_packs/` — evidence pack archives
- `_reports/` — task execution reports
- `docs/` — documentation including AGENT_WORKFLOW_STANDARD.md
- `scripts/` — automation scripts
- `tests/` — test suites
- `.agent/` — agent governance configuration (v1.2.0)
- `.awsp.json` — AWSP configuration file

## Agent Governance Config Scaffold (v1.2.0)

### Overview

Version 1.2.0 introduces agent governance configuration files in the `.agent/` directory. These files enable project-level agent behavior governance, startup read gates, and task-level gate enforcement.

### AWSP_DIRECTORIES Update

The `AWSP_DIRECTORIES` constant now includes `.agent/`:
```python
AWSP_DIRECTORIES = [
    "evidence_packs",
    "_reports",
    "docs",
    "scripts",
    "tests",
    ".agent"  # v1.2.0
]
```

### Generated .agent/ Config Files

The scaffold tool generates four governance config files in `.agent/`:

1. **REQUIRED_READS.json** — Startup read gate configuration
   - Defines required files agents must read before starting work
   - Enforces context loading for AGENTS.md, ACTIVE.md, project rules
   - Schema version tracked for forward compatibility

2. **PROJECT_AGENT_CONFIG.json** — Project-level agent governance
   - Project-specific agent behavior rules
   - Capability restrictions and permissions
   - Integration with runtime governance framework

3. **GATE_CONFIG.json** — Gate configuration
   - Startup gates: pre-flight checks before agent begins
   - Pre-task gates: validation before task execution
   - Pre-GPT gates: checks before GPT review submission
   - Configurable gate enforcement (block, warn, log)

4. **startup_proof_template.json** — Startup read proof template
   - Template for agents to record startup read proofs
   - SHA-256 hashes of read files
   - Timestamp and agent session metadata

### validate_scaffold() Enhancements

The `validate_scaffold()` function now performs additional checks:

```python
def validate_scaffold(project_root: str) -> ValidationResult:
    # Existing checks (v1.1.0)
    check_directories_exist(project_root, AWSP_DIRECTORIES)
    check_awsp_json(project_root)
    
    # New checks (v1.2.0)
    # 1. Verify project_root in .awsp.json matches actual path
    awsp_config = load_json(project_root / ".awsp.json")
    if awsp_config["project_root"] != str(project_root):
        return ValidationResult(
            status="FAIL",
            reason=f"project_root mismatch: {awsp_config['project_root']} != {project_root}"
        )
    
    # 2. Check all 4 .agent/ config files exist
    agent_configs = [
        "REQUIRED_READS.json",
        "PROJECT_AGENT_CONFIG.json",
        "GATE_CONFIG.json",
        "startup_proof_template.json"
    ]
    for config_file in agent_configs:
        config_path = project_root / ".agent" / config_file
        if not config_path.exists():
            return ValidationResult(
                status="FAIL",
                reason=f"Missing .agent/{config_file}"
            )
    
    # 3. Validate JSON syntax and schema_version field
    for config_file in agent_configs:
        config_path = project_root / ".agent" / config_file
        try:
            data = load_json(config_path)
            if "schema_version" not in data:
                return ValidationResult(
                    status="FAIL",
                    reason=f".agent/{config_file} missing schema_version"
                )
        except json.JSONDecodeError as e:
            return ValidationResult(
                status="FAIL",
                reason=f".agent/{config_file} invalid JSON: {e}"
            )
    
    return ValidationResult(status="PASS", reason="All checks passed")
```

### Example .agent/ Config Structure

```json
// .agent/REQUIRED_READS.json
{
  "schema_version": "1.2.0",
  "required_reads": [
    "AGENTS.md",
    "C:\\Users\\RD\\.claude\\ACTIVE.md",
    "docs/AGENT_WORKFLOW_STANDARD.md"
  ],
  "enforcement": "block",
  "description": "Files agents must read before starting work"
}

// .agent/PROJECT_AGENT_CONFIG.json
{
  "schema_version": "1.2.0",
  "project_name": "agent-acceptance",
  "capabilities": {
    "allowed": ["read", "write", "execute", "search"],
    "restricted": ["network", "system_config"]
  },
  "runtime_governance": {
    "enabled": true,
    "rules_path": "D:\\agent-acceptance\\rules\\core.md"
  }
}

// .agent/GATE_CONFIG.json
{
  "schema_version": "1.2.0",
  "gates": {
    "startup": {
      "enabled": true,
      "checks": ["required_reads", "runtime_governance"],
      "enforcement": "block"
    },
    "pre_task": {
      "enabled": true,
      "checks": ["task_scope", "capability_check"],
      "enforcement": "block"
    },
    "pre_gpt": {
      "enabled": true,
      "checks": ["run_id_consistency", "evidence_pack_complete"],
      "enforcement": "block"
    }
  }
}

// .agent/startup_proof_template.json
{
  "schema_version": "1.2.0",
  "template": {
    "agent_session_id": "{{SESSION_ID}}",
    "timestamp": "{{TIMESTAMP}}",
    "reads": [
      {
        "file_path": "{{FILE_PATH}}",
        "sha256": "{{SHA256}}",
        "read_at": "{{READ_TIMESTAMP}}"
      }
    ],
    "validation_result": "{{VALIDATION_STATUS}}"
  }
}
```

## Version History

| Version | Changes |
|---------|---------|
| v1.0.0 | Initial: run_id consistency, evidence pack, prompt template, verification |
| v1.1.0 | Added: END_OF_GPT_RESPONSE marker check, overall_judgment field check, cross-project parameterization, scaffold tool |
| v1.2.0 | Added: .agent/ governance config directory, 4 agent config files (REQUIRED_READS.json, PROJECT_AGENT_CONFIG.json, GATE_CONFIG.json, startup_proof_template.json), enhanced validate_scaffold() with project_root verification and JSON schema validation |
