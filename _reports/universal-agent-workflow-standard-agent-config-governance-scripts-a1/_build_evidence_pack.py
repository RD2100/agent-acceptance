#!/usr/bin/env python3
"""Build evidence pack for UNIVERSAL-AGENT-WORKFLOW-STANDARD-AGENT-CONFIG-GOVERNANCE-SCRIPTS-A1."""
import hashlib, zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
REPORT_DIR = Path(__file__).resolve().parent
TASK_ID = "UNIVERSAL-AGENT-WORKFLOW-STANDARD-AGENT-CONFIG-GOVERNANCE-SCRIPTS-A1"
PACK_DIRNAME = "universal-agent-workflow-standard-agent-config-governance-scripts-a1"


def sha256_file(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    # --- read run_id from run_id.txt in the task report directory -----------
    # For R2+, prefer R2_RUN_ID.txt; fall back to run_id.txt
    run_id_path = REPORT_DIR / "R2_RUN_ID.txt"
    if not run_id_path.exists():
        run_id_path = REPORT_DIR / "run_id.txt"
    if not run_id_path.exists():
        raise SystemExit(f"ERROR: No run_id file found in {REPORT_DIR}.")
    run_id = run_id_path.read_text(encoding="utf-8").strip()

    pack_dir = REPO / "evidence_packs" / PACK_DIRNAME
    pack_dir.mkdir(parents=True, exist_ok=True)

    # --- file groups --------------------------------------------------------
    core_names = [
        "CLOSURE_REPORT.md",
        "GPT_REVIEW_PROMPT.md",
        "SAFETY_ATTESTATION.md",
    ]
    core_files = [REPORT_DIR / n for n in core_names]

    exec_report = REPORT_DIR / "EXECUTION_REPORT.md"

    scripts = [
        REPO / "scripts" / "awsp_scaffold.py",
    ]
    tests = [
        REPO / "tests" / "test_cross_project_scaffold.py",
    ]
    reports = [
        REPORT_DIR / "TARGET_TEST_OUTPUT.txt",
        REPORT_DIR / "FULL_SUITE_OUTPUT.txt",
    ]

    # --- collect existing files ---------------------------------------------
    all_files = [f for f in core_files + [exec_report] + scripts + tests + reports if f.exists()]

    # --- build manifest rows ------------------------------------------------
    manifest_rows = []
    for f in all_files:
        if f in core_files or f == exec_report:
            role = "core"
        elif f in scripts:
            role = "deliverable"
        elif f in tests:
            role = "test"
        elif f in reports:
            role = "test_output"
        else:
            role = "reference"
        manifest_rows.append({
            "path": str(f.relative_to(REPO)),
            "role": role,
            "sha256": sha256_file(f),
            "size": f.stat().st_size,
        })

    # --- generate PACK_MANIFEST.md ------------------------------------------
    manifest_md = (
        f"# PACK_MANIFEST \u2014 {TASK_ID}\n\n"
        f"| Field | Value |\n|-------|-------|\n"
        f"| task_id | {TASK_ID} |\n"
        f"| run_id | {run_id} |\n\n"
        f"## Files\n\n"
        f"| # | Path | Role | SHA-256 | Size |\n"
        f"|---|------|------|---------|------|\n"
    )
    for i, row in enumerate(manifest_rows, 1):
        manifest_md += (
            f"| {i} | `{row['path']}` | {row['role']} "
            f"| `{row['sha256'][:16]}\u2026` | {row['size']} |\n"
        )
    manifest_md += f"| {len(manifest_rows)+1} | `PACK_MANIFEST.md` | core | self | - |\n"

    # --- write manifest to pack dir -----------------------------------------
    (pack_dir / "PACK_MANIFEST.md").write_text(manifest_md, encoding="utf-8")

    # --- actual_deliverables/ -----------------------------------------------
    ad = pack_dir / "actual_deliverables"
    ad.mkdir(parents=True, exist_ok=True)
    for f in all_files:
        (ad / f.name).write_bytes(f.read_bytes())
    (ad / "PACK_MANIFEST.md").write_text(manifest_md, encoding="utf-8")

    # --- copy core files to pack root (for linter) --------------------------
    for fname in core_names:
        src = REPORT_DIR / fname
        if src.exists():
            (pack_dir / fname).write_bytes(src.read_bytes())
    # PACK_MANIFEST.md already at root; EXECUTION_REPORT.md at root too
    if exec_report.exists():
        (pack_dir / "EXECUTION_REPORT.md").write_bytes(exec_report.read_bytes())

    # --- reports/ -----------------------------------------------------------
    reports_dir = pack_dir / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    if exec_report.exists():
        (reports_dir / "EXECUTION_REPORT.md").write_bytes(exec_report.read_bytes())
    target_out = REPORT_DIR / "TARGET_TEST_OUTPUT.txt"
    full_out = REPORT_DIR / "FULL_SUITE_OUTPUT.txt"
    if target_out.exists():
        (reports_dir / "TARGET_TEST_OUTPUT.txt").write_bytes(target_out.read_bytes())
    if full_out.exists():
        (reports_dir / "FULL_SUITE_OUTPUT.txt").write_bytes(full_out.read_bytes())

    # --- create ZIP ---------------------------------------------------------
    zip_path = pack_dir / f"{run_id}.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        # manifest at root
        zf.write(pack_dir / "PACK_MANIFEST.md", "PACK_MANIFEST.md")
        # core files at root
        for fname in core_names:
            src = pack_dir / fname
            if src.exists():
                zf.write(src, fname)
        if (pack_dir / "EXECUTION_REPORT.md").exists():
            zf.write(pack_dir / "EXECUTION_REPORT.md", "EXECUTION_REPORT.md")
        # all deliverables under actual_deliverables/
        for f in all_files:
            zf.write(f, f"actual_deliverables/{f.name}")
        zf.write(pack_dir / "PACK_MANIFEST.md", "actual_deliverables/PACK_MANIFEST.md")
        # reports
        for rf in reports_dir.iterdir():
            zf.write(rf, f"reports/{rf.name}")

    print(f"Pack: {zip_path}")
    print(f"Run ID: {run_id}")


if __name__ == "__main__":
    main()
