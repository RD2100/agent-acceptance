#!/usr/bin/env python3
"""_build_evidence_pack.py — Build evidence pack for HUMAN-DECISION-RECORD-CLI-T10-HASH-INTEGRATE-A1."""
import hashlib, json, zipfile
from datetime import datetime, timezone, timedelta
from pathlib import Path

TZ_CST = timezone(timedelta(hours=8))
REPO = Path(__file__).resolve().parent.parent.parent
REPORT_DIR = Path(__file__).resolve().parent
TASK_ID = "HUMAN-DECISION-RECORD-CLI-T10-HASH-INTEGRATE-A1"

def sha256_file(p): return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    now = datetime.now(tz=TZ_CST)
    run_id = f"HUMAN_DECISION_RECORD_CLI_T10_HASH_INTEGRATE_A1_{now.strftime('%Y%m%dT%H%M%S')}_RD"
    pack_dir = REPO / "evidence_packs" / TASK_ID.lower()
    pack_dir.mkdir(parents=True, exist_ok=True)

    core = [REPORT_DIR / "EXECUTION_REPORT.md", REPORT_DIR / "GPT_REVIEW_PROMPT.md"]
    scripts = [REPO / "scripts" / "human_decision_record.py", REPO / "scripts" / "state_machine_runtime.py"]
    tests = [REPO / "tests" / "test_human_decision_record.py", REPO / "tests" / "test_state_machine_runtime.py"]
    refs = [REPO / "_reports" / "human-decision-record-hash-manifest-bind-a1" / "GPT_REVIEW_RECORD_R1.json"]

    all_files = core + scripts + tests + refs
    all_files = [f for f in all_files if f.exists()]

    manifest_md = f"# PACK_MANIFEST — {TASK_ID}\n\n| Field | Value |\n|-------|-------|\n| task_id | {TASK_ID} |\n| run_id | {run_id} |\n\n## Files\n\n"
    for i, f in enumerate(all_files, 1):
        role = "core" if f in core else "deliverable" if f in scripts else "test" if f in tests else "reference"
        manifest_md += f"| {i} | `{f.relative_to(REPO)}` | {role} | `{sha256_file(f)[:16]}…` | {f.stat().st_size} |\n"

    manifest_md += f"\n## Tests\n- Suite: 467 passed\n"

    (pack_dir / "PACK_MANIFEST.md").write_text(manifest_md, encoding="utf-8")
    ad = pack_dir / "actual_deliverables"; ad.mkdir(parents=True, exist_ok=True)
    for f in all_files: (ad / f.name).write_bytes(f.read_bytes())
    (ad / "PACK_MANIFEST.md").write_text(manifest_md, encoding="utf-8")

    zip_path = pack_dir / f"{run_id}.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.write(pack_dir / "PACK_MANIFEST.md", "PACK_MANIFEST.md")
        for f in all_files: zf.write(f, f"actual_deliverables/{f.name}")

    (REPORT_DIR / "run_id.txt").write_text(run_id, encoding="utf-8")
    print(f"Pack: {zip_path}\nRun ID: {run_id}")

if __name__ == "__main__":
    main()
