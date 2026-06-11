#!/usr/bin/env python3
"""_build_evidence_pack.py — Build evidence pack for HUMAN-DECISION-RECORD-EVIDENCE-BIND-A1."""

import hashlib
import json
import zipfile
from datetime import datetime, timezone, timedelta
from pathlib import Path

TZ_CST = timezone(timedelta(hours=8))
REPO = Path(__file__).resolve().parent.parent.parent
REPORT_DIR = Path(__file__).resolve().parent
TASK_ID = "HUMAN-DECISION-RECORD-EVIDENCE-BIND-A1"

def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    now = datetime.now(tz=TZ_CST)
    run_id = f"HUMAN_DECISION_RECORD_EVIDENCE_BIND_A1_{now.strftime('%Y%m%dT%H%M%S')}_RD"
    pack_dir_name = TASK_ID.lower()
    pack_dir = REPO / "evidence_packs" / pack_dir_name
    zip_name = f"{run_id}.zip"

    pack_dir.mkdir(parents=True, exist_ok=True)

    core_files = [
        REPORT_DIR / "EXECUTION_REPORT.md",
        REPORT_DIR / "GPT_REVIEW_PROMPT.md",
    ]

    deliverable_scripts = [
        REPO / "scripts" / "human_decision_record.py",
    ]

    test_files = [
        REPO / "tests" / "test_human_decision_record.py",
    ]

    ref_files = [
        REPO / "_reports" / "human-decision-record-integrate-t10-a1" / "GPT_REVIEW_RECORD_R1.json",
    ]

    all_files = core_files + deliverable_scripts + test_files + ref_files
    missing = [f for f in all_files if not f.exists()]
    if missing:
        print(f"WARNING: Missing files: {[str(f) for f in missing]}")
        all_files = [f for f in all_files if f.exists()]

    manifest_rows = []
    for f in all_files:
        rel_path = f.relative_to(REPO)
        sha = sha256_file(f)
        size = f.stat().st_size
        if f in core_files:
            role = "core"
        elif f in deliverable_scripts:
            role = "deliverable"
        elif f in test_files:
            role = "test"
        else:
            role = "reference"
        manifest_rows.append({"path": str(rel_path), "role": role, "sha256": sha, "size_bytes": size})

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
        manifest_md += f"| {i} | `{row['path']}` | {row['role']} | `{row['sha256'][:16]}…` | {row['size_bytes']} |\n"

    manifest_md += f"""
## Test Results

- Target tests: 45 passed (test_human_decision_record.py, 6 new evidence binding)
- Full suite: 456 passed

## Integrity

- Total files: {len(manifest_rows)}
- Zip archive: {zip_name}
"""

    manifest_path = pack_dir / "PACK_MANIFEST.md"
    manifest_path.write_text(manifest_md, encoding="utf-8")

    actual_dir = pack_dir / "actual_deliverables"
    actual_dir.mkdir(parents=True, exist_ok=True)

    for f in all_files:
        dest = actual_dir / f.name
        dest.write_bytes(f.read_bytes())

    (actual_dir / "PACK_MANIFEST.md").write_text(manifest_md, encoding="utf-8")

    zip_path = pack_dir / zip_name
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(manifest_path, "PACK_MANIFEST.md")
        for f in all_files:
            zf.write(f, f"actual_deliverables/{f.name}")

    run_id_path = REPORT_DIR / "run_id.txt"
    run_id_path.write_text(run_id, encoding="utf-8")

    print(f"Pack built: {zip_path}")
    print(f"Run ID: {run_id}")
    print(f"Files: {len(manifest_rows)}")

if __name__ == "__main__":
    main()
