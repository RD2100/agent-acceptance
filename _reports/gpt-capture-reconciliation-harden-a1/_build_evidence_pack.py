#!/usr/bin/env python3
"""_build_evidence_pack.py — Build evidence pack for GPT-CAPTURE-RECONCILIATION-HARDEN-A1.

Packages deliverables + references into a ZIP for GPT review submission.
"""

import hashlib
import json
import shutil
import sys
import zipfile
from datetime import datetime, timezone, timedelta
from pathlib import Path

TZ_CST = timezone(timedelta(hours=8))
REPO = Path(__file__).resolve().parent.parent.parent
REPORT_DIR = Path(__file__).resolve().parent
TASK_ID = "GPT-CAPTURE-RECONCILIATION-HARDEN-A1"

def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    now = datetime.now(tz=TZ_CST)
    run_id = f"GPT_CAPTURE_RECONCILIATION_HARDEN_A1_REVIEW_{now.strftime('%Y%m%dT%H%M%S')}_RD"
    pack_dir_name = TASK_ID.lower()
    pack_dir = REPO.parent / "evidence_packs" / pack_dir_name
    zip_name = f"{run_id.replace('_REVIEW_', '_')}.zip"

    # Create pack directory
    pack_dir.mkdir(parents=True, exist_ok=True)

    # Files to include
    files_to_pack = []

    # Core deliverables
    core_files = [
        REPORT_DIR / "GPT_CAPTURE_RECONCILIATION_REPORT.json",
        REPORT_DIR / "GPT_CAPTURE_RECONCILIATION_REPORT.md",
        REPORT_DIR / "EXECUTION_REPORT.md",
        REPORT_DIR / "_validate_reconciliation.py",
        REPORT_DIR / "GPT_REVIEW_PROMPT.md",
    ]

    # Generator script
    generator = REPO / "scripts" / "generate_reconciliation_report.py"

    # Reference files from prior tasks
    ref_files = [
        REPO / "_reports" / "process-state-machine-define-a1" / "PROCESS_STATE_MACHINE.json",
        REPO / "_reports" / "process-state-machine-define-a1" / "CHANGED_FILES_SCHEMA.json",
        REPO / "_reports" / "process-state-machine-define-a1" / "changed_files_utils.py",
        REPO / "scripts" / "verify_gpt_reply.py",
    ]

    # Changed files evidence
    changed_files = REPORT_DIR / "CHANGED_FILES_EVIDENCE.json"

    # Validate all files exist
    all_files = core_files + [generator] + ref_files + [changed_files]
    missing = [f for f in all_files if not f.exists()]
    if missing:
        print(f"WARNING: Missing files: {[str(f) for f in missing]}")
        all_files = [f for f in all_files if f.exists()]

    # Build manifest
    manifest_rows = []
    for f in all_files:
        rel_path = f.relative_to(REPO)
        sha = sha256_file(f)
        size = f.stat().st_size
        role = "core" if f in core_files or f == generator else "reference"
        manifest_rows.append({
            "path": str(rel_path),
            "role": role,
            "sha256": sha,
            "size_bytes": size,
        })

    # PACK_MANIFEST.md
    manifest_md = f"""# PACK_MANIFEST — {TASK_ID}

| Field | Value |
|-------|-------|
| task_id | {TASK_ID} |
| run_id | {run_id} |
| generated_at | {now.isoformat()} |
| pack_dir | {pack_dir_name} |

## Files

| # | Path | Role | SHA-256 | Size |
|---|------|------|---------|------|
"""
    for i, row in enumerate(manifest_rows, 1):
        manifest_md += f"| {i} | `{row['path']}` | {row['role']} | `{row['sha256'][:16]}...` | {row['size_bytes']} |\n"

    manifest_path = REPORT_DIR / "PACK_MANIFEST.md"
    manifest_path.write_text(manifest_md, encoding="utf-8")

    # Add manifest to pack list
    all_files.append(manifest_path)
    manifest_rows.append({
        "path": str(manifest_path.relative_to(REPO)),
        "role": "manifest",
        "sha256": sha256_file(manifest_path),
        "size_bytes": manifest_path.stat().st_size,
    })

    # Write RUN_ID file
    run_id_path = REPORT_DIR / "R1_RUN_ID.txt"
    run_id_path.write_text(run_id, encoding="utf-8")

    # Create ZIP
    zip_path = REPO / "evidence_packs" / pack_dir_name / zip_name
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in all_files:
            arcname = f.relative_to(REPO)
            zf.write(f, arcname)

    zip_sha = sha256_file(zip_path)
    zip_size = zip_path.stat().st_size

    print(f"Evidence pack built:")
    print(f"  ZIP: {zip_path}")
    print(f"  Size: {zip_size} bytes")
    print(f"  SHA-256: {zip_sha}")
    print(f"  Files: {len(all_files)}")
    print(f"  Run ID: {run_id}")

    # Write pack info
    pack_info = {
        "task_id": TASK_ID,
        "run_id": run_id,
        "zip_path": str(zip_path.relative_to(REPO)),
        "zip_sha256": zip_sha,
        "zip_size": zip_size,
        "file_count": len(all_files),
        "generated_at": now.isoformat(),
    }
    info_path = REPORT_DIR / "EVIDENCE_PACK_INFO.json"
    info_path.write_text(json.dumps(pack_info, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"  Pack info: {info_path}")

if __name__ == "__main__":
    main()
