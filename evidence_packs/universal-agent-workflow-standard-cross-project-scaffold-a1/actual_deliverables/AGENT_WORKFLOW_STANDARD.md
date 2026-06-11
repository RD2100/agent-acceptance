# Agent Workflow Standard Protocol (AWSP) v1.1.0

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
- `.awsp.json` — AWSP configuration file

## Version History

| Version | Changes |
|---------|---------|
| v1.0.0 | Initial: run_id consistency, evidence pack, prompt template, verification |
| v1.1.0 | Added: END_OF_GPT_RESPONSE marker check, overall_judgment field check, cross-project parameterization, scaffold tool |
