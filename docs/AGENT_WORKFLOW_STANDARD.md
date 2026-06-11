# Agent Workflow Standard Protocol (AWSP) v1.3.0

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

The scaffold tool generates six governance config files in `.agent/` (four from v1.2.0, two added in v1.3.0):

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

## Conversation Registry and GPT Review Isolation (v1.3.0)

### Motivation

When multiple agents operate in parallel — each potentially invoking GPT for review — there is a risk that one agent accidentally reuses or references another agent's GPT conversation. This leads to misattributed evidence, unverifiable review records, and cross-contamination of review sessions. The rules below eliminate that risk.

### Isolation Rules

1. **No Default Cross-Agent Conversation Reuse**
   One agent MUST NOT default to reusing another agent's GPT conversation. Each agent session MUST initiate its own, independent GPT conversation for every review task.

2. **Mandatory Conversation Binding**
   Every GPT review MUST be bound to the composite key:
   ```
   agent_id + project_id + task_id + run_id + conversation_id/chat_url
   ```
   This binding MUST be recorded in the GPT_REVIEW_RECORD and the evidence pack manifest before the review is considered complete.

3. **Capture Must Not Rely on "Last Assistant Message" Alone**
   Capturing GPT responses by reading only the last assistant message in a shared conversation thread is insufficient. The capture mechanism MUST positively identify the response by matching both `run_id` and `task_id` fields together with the `END_OF_GPT_RESPONSE` marker.

4. **Capture Must Match run_id + task_id + END_OF_GPT_RESPONSE**
   A valid GPT review capture MUST satisfy all three conditions simultaneously:
   - The response contains the expected `run_id` value
   - The response is associated with the correct `task_id`
   - The response includes the `END_OF_GPT_RESPONSE` marker

5. **Independent Browser Profiles for Parallel Sessions**
   Multi-agent parallel review sessions MUST use independent browser profiles and/or separate CDP (Chrome DevTools Protocol) sessions. Sharing a single browser profile across agents is prohibited.

6. **Unbound Reviews Are Incomplete**
   GPT reviews that lack conversation binding (i.e., missing `conversation_id` or `chat_url`) can only be marked as:
   - `pending_conversation_binding` — the review content exists but binding metadata has not been captured yet
   - `review_unverified` — the review cannot be verified without binding evidence

   Such reviews MUST NOT be marked as `review_complete` or `review_passed`.

7. **Evidence Packs Must Include Conversation Binding Evidence**
   Every evidence pack that contains a GPT review MUST include:
   - The `conversation_id` or `chat_url` recorded in GPT_REVIEW_RECORD
   - The browser profile identifier (when browser-based capture is used)
   - A binding assertion showing the composite key resolves unambiguously to one conversation

8. **No Fabrication of Binding Metadata**
   Agents MUST NOT fabricate any of the following values:
   - `chat_url`
   - `conversation_id`
   - Browser profile identifier
   - GPT capture screenshots or response text

   All binding metadata MUST originate from the actual browser session or API interaction that produced the GPT review.

### New .agent/ Configuration Files

Version 1.3.0 introduces two additional files in the `.agent/` directory:

#### .agent/CONVERSATION_BINDING.json

Project-level conversation binding configuration. Defines how the project enforces conversation isolation and which binding fields are required.

```json
{
  "schema_version": "1.0.0",
  "awsp_version": "1.3.0",
  "project_id": "agent-acceptance",
  "project_root": "D:/agent-acceptance",
  "default_conversation_policy": "one_agent_one_conversation",
  "bindings": [
    {
      "agent_id": "agent-local-001",
      "role": "reviewer",
      "binding_status": "pending_manual_binding",
      "conversation_id": null,
      "chat_url": null,
      "browser_profile_id": null,
      "cdp_endpoint": null,
      "allowed_task_scope": ["*"],
      "capture_policy": {
        "must_match_run_id": true,
        "must_match_task_id": true,
        "must_include_end_marker": true,
        "forbid_last_message_only_capture": true
      }
    }
  ]
}
```

Fresh scaffolds MUST default to `pending_manual_binding`. Agents MUST NOT set a binding to `active` unless a real `chat_url` or `conversation_id` has been captured from the actual GPT conversation.

#### External Runtime Governance Scope

Conversation Registry also records which external runtimes are inside the governed workflow boundary. Fresh scaffolds MUST include `governance_scope` with these entries:

| runtime_id | Governance Role | Default Status |
|------------|-----------------|----------------|
| `devframe-control-plane` | Control-plane / pipeline provenance layer at `D:/dev-frame/ai-workflow-hub` | `in_scope_read_only` |
| `dev-frame-opencode` | Agent dispatch layer for TaskSpec -> ExecutionReport work | `in_scope_human_gated` |
| `paper-workflow` | Governed business workflow for synthetic or sanitized paper review tasks | `in_scope_pilot_only` |

These entries do not authorize execution by themselves. The default execution policy is `human_gated_for_external_runtime_execution`, with ad-hoc GPT submission and cross-repo smoke runs forbidden unless a separate human authorization and evidence record exists.

#### .agent/CONVERSATION_REGISTRY.schema.json

Whole-file JSON Schema for `.agent/CONVERSATION_BINDING.json`. The schema validates top-level project policy fields and every entry under `bindings[]`.

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "schema_version": "1.0.0",
  "awsp_version": "1.3.0",
  "type": "object",
  "required": [
    "schema_version",
    "awsp_version",
    "project_id",
    "project_root",
    "default_conversation_policy",
    "governance_scope",
    "bindings"
  ],
  "properties": {
    "governance_scope": {
      "type": "object",
      "required": [
        "default_execution_policy",
        "forbid_ad_hoc_gpt_submission",
        "forbid_cross_repo_smoke_without_human_gate",
        "external_runtimes"
      ]
    },
    "bindings": {
      "type": "array",
      "minItems": 1,
      "items": {
        "type": "object",
        "required": ["agent_id", "role", "binding_status", "capture_policy"],
        "properties": {
          "role": {
            "type": "string",
            "enum": ["reviewer", "executor", "observer", "orchestrator"]
          },
          "binding_status": {
            "type": "string",
            "enum": ["pending_manual_binding", "active", "paused", "retired", "invalid"]
          }
        }
      }
    }
  }
}
```

### AWSP_DIRECTORIES Update (v1.3.0)

No new directories are added. The two new files reside within the existing `.agent/` directory introduced in v1.2.0.

### validate_scaffold() Enhancements (v1.3.0)

The `validate_scaffold()` function performs additional checks for conversation registry files:

```python
def validate_scaffold(project_root: str) -> ValidationResult:
    # ... existing checks (v1.1.0, v1.2.0) ...

    # New checks (v1.3.0)
    conversation_files = [
        "CONVERSATION_BINDING.json",
        "CONVERSATION_REGISTRY.schema.json"
    ]
    for config_file in conversation_files:
        config_path = project_root / ".agent" / config_file
        if not config_path.exists():
            return ValidationResult(
                status="FAIL",
                reason=f"Missing .agent/{config_file}"
            )

    # Validate CONVERSATION_BINDING.json using CONVERSATION_REGISTRY.schema.json
    binding_result = validate_binding(
        project_root / ".agent" / "CONVERSATION_BINDING.json",
        project_root=project_root
    )
    if not binding_result["valid"]:
        return ValidationResult(
            status="FAIL",
            reason="conversation binding validation failed"
        )

    return ValidationResult(status="PASS", reason="All checks passed")
```

## Version History

| Version | Changes |
|---------|---------|
| v1.0.0 | Initial: run_id consistency, evidence pack, prompt template, verification |
| v1.1.0 | Added: END_OF_GPT_RESPONSE marker check, overall_judgment field check, cross-project parameterization, scaffold tool |
| v1.2.0 | Added: .agent/ governance config directory, 4 agent config files (REQUIRED_READS.json, PROJECT_AGENT_CONFIG.json, GATE_CONFIG.json, startup_proof_template.json), enhanced validate_scaffold() with project_root verification and JSON schema validation |
| v1.3.0 | Added: Conversation Registry and GPT Review Isolation rules (8 isolation rules), 2 new .agent/ config files (CONVERSATION_BINDING.json, CONVERSATION_REGISTRY.schema.json), conversation binding enforcement in validate_scaffold() |
