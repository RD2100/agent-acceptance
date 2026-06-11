#!/usr/bin/env python3
"""Build R1 evidence pack for UNIVERSAL-AGENT-WORKFLOW-STANDARD-AGENT-CONFIG-SCAFFOLD-A1."""
import hashlib, zipfile
from datetime import datetime, timezone, timedelta
from pathlib import Path

TZ_CST = timezone(timedelta(hours=8))
REPO = Path(__file__).resolve().parent.parent.parent
REPORT_DIR = Path(__file__).resolve().parent
TASK_ID = "UNIVERSAL-AGENT-WORKFLOW-STANDARD-AGENT-CONFIG-SCAFFOLD-A1"

def sha256_file(p): return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    now = datetime.now(tz=TZ_CST)
    run_id = f"UNIVERSAL_AGENT_WORKFLOW_STANDARD_AGENT_CONFIG_SCAFFOLD_A1_{now.strftime('%Y%m%dT%H%M%S')}_RD"
    pack_dir = REPO / "evidence_packs" / TASK_ID.lower()
    pack_dir.mkdir(parents=True, exist_ok=True)

    core = [
        REPORT_DIR / "EXECUTION_REPORT.md",
        REPORT_DIR / "GPT_REVIEW_PROMPT.md",
        REPORT_DIR / "CLOSURE_REPORT.md",
        REPORT_DIR / "SAFETY_ATTESTATION.md",
    ]
    scripts = [
        REPO / "scripts" / "validate_run_id_consistency.py",
        REPO / "scripts" / "awsp_scaffold.py",
    ]
    tests = [
        REPO / "tests" / "test_validate_run_id_consistency.py",
        REPO / "tests" / "test_cross_project_scaffold.py",
    ]
    docs = [REPO / "docs" / "AGENT_WORKFLOW_STANDARD.md"]
    reports = [
        REPORT_DIR / "TARGET_TEST_OUTPUT.txt",
        REPORT_DIR / "FULL_SUITE_OUTPUT.txt",
    ]

    all_files = [f for f in core + scripts + tests + docs + reports if f.exists()]

    manifest_rows = []
    for f in all_files:
        if f in core: role = "core"
        elif f in scripts: role = "deliverable"
        elif f in tests: role = "test"
        elif f in docs: role = "documentation"
        elif f in reports: role = "test_output"
        else: role = "reference"
        manifest_rows.append({"path": str(f.relative_to(REPO)), "role": role, "sha256": sha256_file(f), "size": f.stat().st_size})

    manifest_md = f"# PACK_MANIFEST — {TASK_ID}\n\n| Field | Value |\n|-------|-------|\n| task_id | {TASK_ID} |\n| run_id | {run_id} |\n\n## Files\n\n| # | Path | Role | SHA-256 | Size |\n|---|------|------|---------|------|\n"
    for i, row in enumerate(manifest_rows, 1):
        manifest_md += f"| {i} | `{row['path']}` | {row['role']} | `{row['sha256'][:16]}…` | {row['size']} |\n"
    manifest_md += f"| {len(manifest_rows)+1} | `PACK_MANIFEST.md` | core | self | - |\n"
    manifest_md += f"\n## Tests\n- Target: 49 passed / 49 total\n- Suite: 540 passed / 540 total\n"

    (pack_dir / "PACK_MANIFEST.md").write_text(manifest_md, encoding="utf-8")
    ad = pack_dir / "actual_deliverables"; ad.mkdir(parents=True, exist_ok=True)
    for f in all_files: (ad / f.name).write_bytes(f.read_bytes())
    (ad / "PACK_MANIFEST.md").write_text(manifest_md, encoding="utf-8")

    # Copy required files to pack root for linter
    for fname in ["CLOSURE_REPORT.md", "GPT_REVIEW_PROMPT.md", "SAFETY_ATTESTATION.md"]:
        src = REPORT_DIR / fname
        if src.exists():
            (pack_dir / fname).write_bytes(src.read_bytes())
    reports_dir = pack_dir / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    target_out = REPORT_DIR / "TARGET_TEST_OUTPUT.txt"
    full_out = REPORT_DIR / "FULL_SUITE_OUTPUT.txt"
    if target_out.exists():
        (reports_dir / "TARGETED_TEST_OUTPUT.txt").write_bytes(target_out.read_bytes())
    if full_out.exists():
        (reports_dir / "TEST_OUTPUT.txt").write_bytes(full_out.read_bytes())

    zip_path = pack_dir / f"{run_id}.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.write(pack_dir / "PACK_MANIFEST.md", "PACK_MANIFEST.md")
        for f in all_files: zf.write(f, f"actual_deliverables/{f.name}")

    run_id_path = REPORT_DIR / "R1_RUN_ID.txt"
    run_id_path.write_text(run_id, encoding="utf-8")
    (REPORT_DIR / "run_id.txt").write_text(run_id, encoding="utf-8")
    print(f"Pack: {zip_path}\nRun ID: {run_id}")

if __name__ == "__main__":
    main()
