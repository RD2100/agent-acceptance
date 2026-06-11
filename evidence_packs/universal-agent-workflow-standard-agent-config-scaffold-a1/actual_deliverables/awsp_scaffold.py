#!/usr/bin/env python3
"""awsp_scaffold.py — Generate AWSP-compliant project directory structure.

Creates the standard directory layout required by Agent Workflow Standard Protocol
(AWSP) v1.1.0 for any project. Designed for cross-project use.

Usage:
    # Create scaffold in current directory:
    python scripts/awsp_scaffold.py --project-root /path/to/project

    # Dry run (preview only):
    python scripts/awsp_scaffold.py --project-root /path/to/project --dry-run

    # Force overwrite existing empty directories:
    python scripts/awsp_scaffold.py --project-root /path/to/project --force
"""

import argparse
import json
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path


AWSP_VERSION = "1.2.0"

# Standard AWSP directory layout
AWSP_DIRECTORIES = [
    "evidence_packs",
    "_reports",
    "docs",
    "scripts",
    "tests",
    ".agent",
]

# Template files to generate
AWSP_TEMPLATES = {
    "docs/AGENT_WORKFLOW_STANDARD.md": """# Agent Workflow Standard Protocol (AWSP) v__AWSP_VERSION__

## Purpose

Defines the canonical workflow for agent hardening tasks in this project.
Ensures consistency across all evidence packs, GPT review submissions, and verification steps.

## Core Principles

1. **Run-ID Consistency**: All run_id values MUST be identical across:
   - Evidence pack filename
   - `run_id.txt` and `R1_RUN_ID.txt` content
   - GPT review prompt `{{RUN_ID}}` substitution
   - GPT reply `run_id:` field

2. **Evidence Pack Standard**: Every pack MUST include:
   - `PACK_MANIFEST.md` with proper markdown table
   - All evidence files listed in manifest
   - PACK_MANIFEST.md itself listed as `core` role

3. **Prompt Template Standard**: Every GPT review prompt MUST:
   - Use `{{RUN_ID}}` template variable (not hardcoded)
   - Include `{{TASK_ID}}` template variable
   - End with `---END_OF_GPT_RESPONSE---` marker
   - Use `overall_judgment:` field name (not `verdict:`)

4. **Verification Standard**: After GPT reply:
   - Verify run_id in reply matches submitted run_id
   - Verify `END_OF_GPT_RESPONSE` marker present
   - Create GPT_REVIEW_RECORD with full metadata
""",
    ".awsp.json": """{
    "awsp_version": "__AWSP_VERSION__",
    "project_root": "__PROJECT_ROOT__",
    "created_at": "__TIMESTAMP__",
    "directories": __DIRS_JSON__,
    "validation": {
        "require_run_id_consistency": true,
        "require_evidence_pack": true,
        "require_prompt_template_vars": true,
        "require_end_marker": true,
        "require_overall_judgment": true
    }
}
""",
    ".agent/REQUIRED_READS.json": """{
    "schema_version": "1.0.0",
    "awsp_version": "__AWSP_VERSION__",
    "project_root": "__PROJECT_ROOT__",
    "required_reads": [
        {
            "path": ".agent/PROJECT_AGENT_CONFIG.json",
            "evidence_level": "P0",
            "must_read_at_startup": true,
            "fail_closed_if_missing": true,
            "description": "Project agent configuration — defines governance rules for this project"
        },
        {
            "path": ".agent/GATE_CONFIG.json",
            "evidence_level": "P0",
            "must_read_at_startup": true,
            "fail_closed_if_missing": true,
            "description": "Gate configuration — defines pre-task and pre-GPT review gates"
        },
        {
            "path": "docs/AGENT_WORKFLOW_STANDARD.md",
            "evidence_level": "P1",
            "must_read_at_startup": true,
            "fail_closed_if_missing": false,
            "description": "AWSP standard document — workflow rules and conventions"
        }
    ]
}
""",
    ".agent/PROJECT_AGENT_CONFIG.json": """{
    "schema_version": "1.0.0",
    "awsp_version": "__AWSP_VERSION__",
    "project_root": "__PROJECT_ROOT__",
    "created_at": "__TIMESTAMP__",
    "governance": {
        "enforce_startup_read_gate": true,
        "enforce_pre_task_gate": true,
        "enforce_pre_gpt_review_gate": true,
        "enforce_state_machine": true,
        "enforce_human_required_decision_record": true
    },
    "state_machine": {
        "enabled": true,
        "states": [
            "draft", "gate_passing", "gpt_reviewing",
            "accepted", "accepted_with_limitation",
            "blocked", "human_required", "closed"
        ],
        "max_review_rounds": 5,
        "fail_closed_on_unknown_state": true
    },
    "evidence_pack": {
        "required_files": [
            "CLOSURE_REPORT.md",
            "GPT_REVIEW_PROMPT.md",
            "PACK_MANIFEST.md",
            "SAFETY_ATTESTATION.md"
        ],
        "required_dirs": ["actual_deliverables", "reports"],
        "summary_only_risk_check": true
    },
    "scripts": {
        "validate_run_id": "scripts/validate_run_id_consistency.py",
        "verify_gpt_reply": "scripts/verify_gpt_reply.py",
        "evidence_pack_linter": "scripts/evidence_pack_linter.py",
        "pre_gpt_review_gate": "scripts/pre_gpt_review_gate.py",
        "startup_read_gate": "scripts/startup_read_gate.py",
        "state_machine_runtime": "scripts/state_machine_runtime.py",
        "human_decision_record": "scripts/human_decision_record.py"
    }
}
""",
    ".agent/GATE_CONFIG.json": """{
    "schema_version": "1.0.0",
    "awsp_version": "__AWSP_VERSION__",
    "gates": {
        "startup_read_gate": {
            "enabled": true,
            "strict_mode": true,
            "required_reads_path": ".agent/REQUIRED_READS.json",
            "proof_template_path": ".agent/startup_proof_template.json",
            "block_on_failure": true
        },
        "pre_task_gate": {
            "enabled": true,
            "checks": [
                "task_id_authorized",
                "previous_verdict_allows_continuation",
                "startup_read_gate_passed"
            ],
            "block_on_failure": true
        },
        "pre_gpt_review_gate": {
            "enabled": true,
            "checks": [
                "evidence_pack_linter_pass",
                "actual_deliverables_not_empty",
                "pack_manifest_has_sha256",
                "startup_read_gate_passed"
            ],
            "block_on_failure": true
        }
    }
}
""",
    ".agent/startup_proof_template.json": """{
    "schema_version": "1.0.0",
    "task_id": "<REPLACE_WITH_TASK_ID>",
    "gate_status": "pass",
    "agent_id": "<REPLACE_WITH_AGENT_ID>",
    "timestamp": "<REPLACE_AT_RUNTIME>",
    "reads_completed": [
        {
            "file": ".agent/PROJECT_AGENT_CONFIG.json",
            "summary_hash": "sha256:<COMPUTE_AT_RUNTIME>",
            "read_confirmed": true
        },
        {
            "file": ".agent/GATE_CONFIG.json",
            "summary_hash": "sha256:<COMPUTE_AT_RUNTIME>",
            "read_confirmed": true
        },
        {
            "file": "docs/AGENT_WORKFLOW_STANDARD.md",
            "summary_hash": "sha256:<COMPUTE_AT_RUNTIME>",
            "read_confirmed": true
        }
    ]
}
""",
}


def create_scaffold(project_root: str, dry_run: bool = False, force: bool = False) -> dict:
    """Create AWSP-compliant directory structure.

    Args:
        project_root: Root directory of the project.
        dry_run: If True, only preview what would be created.
        force: If True, overwrite existing empty directories.

    Returns:
        dict with created, skipped, errors, config.
    """
    root = Path(project_root)
    result = {"created": [], "skipped": [], "errors": [], "config": None}

    if not root.exists():
        result["errors"].append(f"Project root does not exist: {root}")
        return result

    # Resolve to absolute path for consistent project_root storage
    resolved_root = root.resolve()

    # Create directories
    for d in AWSP_DIRECTORIES:
        dir_path = root / d
        if dir_path.exists() and dir_path.is_dir():
            if force:
                result["skipped"].append(str(d))
            else:
                result["skipped"].append(str(d))
        elif dir_path.exists():
            result["errors"].append(f"{d} exists but is not a directory")
        else:
            if not dry_run:
                dir_path.mkdir(parents=True, exist_ok=True)
            result["created"].append(str(d))

    # Generate template files
    tz = timezone(timedelta(hours=8))
    now = datetime.now(tz=tz)
    timestamp = now.strftime("%Y-%m-%dT%H:%M:%S+08:00")

    for rel_path, template in AWSP_TEMPLATES.items():
        file_path = root / rel_path
        if file_path.exists() and not force:
            result["skipped"].append(rel_path)
            continue

        content = template.replace("__AWSP_VERSION__", AWSP_VERSION)
        content = content.replace("__PROJECT_ROOT__", str(resolved_root).replace("\\", "/"))
        content = content.replace("__TIMESTAMP__", timestamp)
        content = content.replace("__DIRS_JSON__", json.dumps(AWSP_DIRECTORIES))

        if not dry_run:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content, encoding="utf-8")
        result["created"].append(rel_path)

    # Generate .awsp.json config
    config = {
        "awsp_version": AWSP_VERSION,
        "project_root": str(resolved_root).replace("\\", "/"),
        "created_at": timestamp,
        "directories": AWSP_DIRECTORIES,
        "validation": {
            "require_run_id_consistency": True,
            "require_evidence_pack": True,
            "require_prompt_template_vars": True,
            "require_end_marker": True,
            "require_overall_judgment": True,
        },
    }
    result["config"] = config

    return result


def validate_scaffold(project_root: str) -> dict:
    """Validate that a project has the AWSP-compliant structure.

    Args:
        project_root: Root directory of the project.

    Returns:
        dict with valid, errors, details.
    """
    root = Path(project_root)
    errors = []
    details = {}

    if not root.exists():
        return {"valid": False, "errors": ["Project root does not exist"], "details": {}}

    # Check directories
    missing_dirs = []
    for d in AWSP_DIRECTORIES:
        dir_path = root / d
        if dir_path.exists() and dir_path.is_dir():
            details[f"dir_{d}"] = "exists"
        else:
            missing_dirs.append(d)
            details[f"dir_{d}"] = "missing"

    if missing_dirs:
        errors.append(f"Missing AWSP directories: {', '.join(missing_dirs)}")

    # Check config file
    config_path = root / ".awsp.json"
    if config_path.exists():
        try:
            config = json.loads(config_path.read_text(encoding="utf-8"))
            details["config_exists"] = True
            details["config_valid"] = True

            # Check awsp_version
            cfg_version = config.get("awsp_version")
            details["config_version"] = cfg_version or "unknown"
            if cfg_version != AWSP_VERSION:
                errors.append(
                    f".awsp.json awsp_version mismatch: "
                    f"found '{cfg_version}', expected '{AWSP_VERSION}'"
                )
                details["config_valid"] = False

            # Check required config fields
            required_fields = ["awsp_version", "project_root", "directories", "validation"]
            missing_fields = [f for f in required_fields if f not in config]
            if missing_fields:
                errors.append(
                    f".awsp.json missing required fields: {', '.join(missing_fields)}"
                )
                details["config_valid"] = False

            # Check validation config
            validation_cfg = config.get("validation", {})
            expected_checks = [
                "require_run_id_consistency",
                "require_evidence_pack",
                "require_prompt_template_vars",
                "require_end_marker",
                "require_overall_judgment",
            ]
            missing_validation = [c for c in expected_checks if c not in validation_cfg]
            if missing_validation:
                errors.append(
                    f".awsp.json validation section missing: {', '.join(missing_validation)}"
                )
                details["config_valid"] = False
            else:
                # Check that all validation values are true (fail-closed)
                false_checks = [c for c in expected_checks if not validation_cfg.get(c)]
                if false_checks:
                    errors.append(
                        f".awsp.json validation values not all true: {', '.join(false_checks)} = false"
                    )
                    details["config_valid"] = False

            # Check directories field matches AWSP_DIRECTORIES
            cfg_dirs = config.get("directories", [])
            if sorted(cfg_dirs) != sorted(AWSP_DIRECTORIES):
                errors.append(
                    f".awsp.json directories field mismatch: "
                    f"found {cfg_dirs}, expected {AWSP_DIRECTORIES}"
                )
                details["config_valid"] = False

        except (json.JSONDecodeError, OSError) as e:
            errors.append(f".awsp.json exists but is invalid: {e}")
            details["config_exists"] = True
            details["config_valid"] = False
    else:
        errors.append(".awsp.json config file not found")
        details["config_exists"] = False

    # Check AWSP standard doc
    doc_path = root / "docs" / "AGENT_WORKFLOW_STANDARD.md"
    if doc_path.exists():
        details["awsp_doc_exists"] = True
    else:
        errors.append("docs/AGENT_WORKFLOW_STANDARD.md not found")
        details["awsp_doc_exists"] = False

    # Check project_root matches actual project root
    config_path = root / ".awsp.json"
    if config_path.exists():
        try:
            config = json.loads(config_path.read_text(encoding="utf-8"))
            cfg_project_root = config.get("project_root", "")
            actual_root = str(root.resolve()).replace("\\", "/")
            cfg_root_normalized = cfg_project_root.replace("\\", "/").rstrip("/")
            actual_root_normalized = actual_root.rstrip("/")
            if cfg_root_normalized and cfg_root_normalized != actual_root_normalized:
                errors.append(
                    f".awsp.json project_root mismatch: "
                    f"found '{cfg_root_normalized}', actual '{actual_root_normalized}'"
                )
                details["project_root_valid"] = False
            else:
                details["project_root_valid"] = True
        except (json.JSONDecodeError, OSError):
            pass  # Already handled above

    # Check .agent/ governance config files (v1.2.0)
    agent_config_files = [
        ".agent/REQUIRED_READS.json",
        ".agent/PROJECT_AGENT_CONFIG.json",
        ".agent/GATE_CONFIG.json",
        ".agent/startup_proof_template.json",
    ]
    missing_agent_files = []
    for af in agent_config_files:
        af_path = root / af
        if af_path.exists():
            # Validate JSON structure
            try:
                data = json.loads(af_path.read_text(encoding="utf-8"))
                # Check schema_version exists
                if "schema_version" not in data:
                    errors.append(f"{af} missing required field: schema_version")
                details[f"agent_{af}"] = "exists"

                # Content validation per file type (R2 enhancement)
                if af == ".agent/PROJECT_AGENT_CONFIG.json":
                    cfg_awsp_ver = data.get("awsp_version")
                    if cfg_awsp_ver is None:
                        errors.append(
                            f".agent/PROJECT_AGENT_CONFIG.json missing required field: awsp_version"
                        )
                    elif cfg_awsp_ver != AWSP_VERSION:
                        errors.append(
                            f".agent/PROJECT_AGENT_CONFIG.json awsp_version "
                            f"mismatch: found '{cfg_awsp_ver}', expected '{AWSP_VERSION}'"
                        )
                    gov = data.get("governance", {})
                    required_gov_flags = [
                        "enforce_startup_read_gate",
                        "enforce_pre_task_gate",
                        "enforce_pre_gpt_review_gate",
                        "enforce_state_machine",
                        "enforce_human_required_decision_record",
                    ]
                    missing_flags = [f for f in required_gov_flags if f not in gov]
                    if missing_flags:
                        errors.append(
                            f".agent/PROJECT_AGENT_CONFIG.json missing governance flags: "
                            + ", ".join(missing_flags)
                        )
                elif af == ".agent/GATE_CONFIG.json":
                    gates = data.get("gates", {})
                    required_gates = [
                        "startup_read_gate",
                        "pre_task_gate",
                        "pre_gpt_review_gate",
                    ]
                    missing_gates = [g for g in required_gates if g not in gates]
                    if missing_gates:
                        errors.append(
                            f".agent/GATE_CONFIG.json missing required gates: "
                            + ", ".join(missing_gates)
                        )
                elif af == ".agent/REQUIRED_READS.json":
                    if "required_reads" not in data:
                        errors.append(
                            ".agent/REQUIRED_READS.json missing required field: required_reads"
                        )
                    elif not isinstance(data["required_reads"], list):
                        errors.append(
                            ".agent/REQUIRED_READS.json required_reads must be an array"
                        )
            except (json.JSONDecodeError, OSError) as e:
                errors.append(f"{af} exists but is invalid JSON: {e}")
                details[f"agent_{af}"] = "invalid"
        else:
            missing_agent_files.append(af)
            details[f"agent_{af}"] = "missing"

    if missing_agent_files:
        errors.append(
            f"Missing .agent/ governance config files: "
            + ", ".join(missing_agent_files)
        )

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "details": details,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Generate AWSP-compliant project directory structure",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--project-root", required=True,
                        help="Root directory of the project")
    parser.add_argument("--dry-run", action="store_true",
                        help="Preview only, do not create files")
    parser.add_argument("--force", action="store_true",
                        help="Overwrite existing files")
    parser.add_argument("--validate", action="store_true",
                        help="Validate existing scaffold instead of creating")
    args = parser.parse_args()

    if args.validate:
        result = validate_scaffold(args.project_root)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        sys.exit(0 if result["valid"] else 1)
    else:
        result = create_scaffold(args.project_root, dry_run=args.dry_run, force=args.force)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        if result["errors"]:
            print("\nERRORS:")
            for e in result["errors"]:
                print(f"  {e}")
            sys.exit(1)
        elif args.dry_run:
            print("\nDRY RUN: No files created. Use without --dry-run to create.")
        else:
            print(f"\nAWSP scaffold created at: {args.project_root}")
        sys.exit(0)


if __name__ == "__main__":
    main()
