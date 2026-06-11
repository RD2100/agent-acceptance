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


AWSP_VERSION = "1.1.0"

# Standard AWSP directory layout
AWSP_DIRECTORIES = [
    "evidence_packs",
    "_reports",
    "docs",
    "scripts",
    "tests",
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
        content = content.replace("__PROJECT_ROOT__", str(root).replace("\\", "/"))
        content = content.replace("__TIMESTAMP__", timestamp)
        content = content.replace("__DIRS_JSON__", json.dumps(AWSP_DIRECTORIES))

        if not dry_run:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content, encoding="utf-8")
        result["created"].append(rel_path)

    # Generate .awsp.json config
    config = {
        "awsp_version": AWSP_VERSION,
        "project_root": str(root),
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
