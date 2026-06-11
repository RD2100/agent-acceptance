#!/usr/bin/env python3
"""Build evidence pack for UNIVERSAL-AGENT-WORKFLOW-STANDARD-CONVERSATION-REGISTRY-A1."""
import hashlib, zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
REPORT_DIR = Path(__file__).resolve().parent
TASK_ID = "UNIVERSAL-AGENT-WORKFLOW-STANDARD-CONVERSATION-REGISTRY-A1"
PACK_DIRNAME = "universal-agent-workflow-standard-conversation-registry-a1"


def sha256_file(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    # --- read run_id from run_id.txt in the task report directory -----------
    run_id_path = REPORT_DIR / "run_id.txt"
    if not run_id_path.exists():
        raise SystemExit(f"ERROR: No run_id.txt found in {REPORT_DIR}.")
    run_id = run_id_path.read_text(encoding="utf-8").strip()

    pack_dir = REPO / "evidence_packs" / PACK_DIRNAME
    pack_dir.mkdir(parents=True, exist_ok=True)

    # --- file groups --------------------------------------------------------
    # Core files: placed at pack root AND in actual_deliverables/
    core_names = [
        "CLOSURE_REPORT.md",
        "GPT_REVIEW_PROMPT.md",
        "PACK_MANIFEST.md",
        "SAFETY_ATTESTATION.md",
    ]
    core_files = [REPORT_DIR / n for n in core_names if n != "PACK_MANIFEST.md"]

    # Actual deliverable files (source code + tests)
    deliverables = [
        REPO / "scripts" / "awsp_scaffold.py",
        REPO / "scripts" / "validate_conversation_registry.py",
        REPO / "tests" / "test_conversation_registry.py",
        REPO / "tests" / "test_cross_project_scaffold.py",
    ]

    # Reports
    exec_report = REPORT_DIR / "EXECUTION_REPORT.md"
    report_files = [
        REPORT_DIR / "TARGET_TEST_OUTPUT.txt",
        REPORT_DIR / "TARGET_TEST_OUTPUT_R3.txt",
        REPORT_DIR / "FULL_SUITE_OUTPUT.txt",
        REPORT_DIR / "FULL_SUITE_OUTPUT_R3.txt",
        REPORT_DIR / "R3_REAL_PATH_PROBE.txt",
        REPORT_DIR / "RUN_ID_CONSISTENCY_R3.txt",
        REPORT_DIR / "R3_RUN_ID.txt",
        REPORT_DIR / "STARTUP_READ_PROOF.json",
    ]

    # --- collect existing files for manifest --------------------------------
    all_manifest_files = [
        f for f in core_files + deliverables + [exec_report] + report_files
        if f.exists()
    ]

    # --- build manifest rows ------------------------------------------------
    manifest_rows = []
    for f in all_manifest_files:
        if f in core_files:
            role = "core"
        elif f in deliverables:
            role = "deliverable"
        elif f == exec_report:
            role = "report"
        elif f in report_files:
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

    # Core files go into actual_deliverables/ too
    for f in core_files:
        if f.exists():
            (ad / f.name).write_bytes(f.read_bytes())

    # Deliverable source files
    for f in deliverables:
        if f.exists():
            (ad / f.name).write_bytes(f.read_bytes())

    # PACK_MANIFEST.md in actual_deliverables/
    (ad / "PACK_MANIFEST.md").write_text(manifest_md, encoding="utf-8")

    # --- copy core files to pack root (for linter) --------------------------
    for fname in core_names:
        if fname == "PACK_MANIFEST.md":
            # Already written above
            continue
        src = REPORT_DIR / fname
        if src.exists():
            (pack_dir / fname).write_bytes(src.read_bytes())

    # EXECUTION_REPORT.md at root too
    if exec_report.exists():
        (pack_dir / "EXECUTION_REPORT.md").write_bytes(exec_report.read_bytes())

    # --- reports/ -----------------------------------------------------------
    reports_dir = pack_dir / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    if exec_report.exists():
        (reports_dir / "EXECUTION_REPORT.md").write_bytes(exec_report.read_bytes())
    for rf in report_files:
        if rf.exists():
            (reports_dir / rf.name).write_bytes(rf.read_bytes())

    # --- create ZIP ---------------------------------------------------------
    zip_path = pack_dir / f"{run_id}.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        # manifest at root
        zf.write(pack_dir / "PACK_MANIFEST.md", "PACK_MANIFEST.md")

        # core files at root
        for fname in core_names:
            if fname == "PACK_MANIFEST.md":
                continue
            src = pack_dir / fname
            if src.exists():
                zf.write(src, fname)

        # EXECUTION_REPORT.md at root
        if (pack_dir / "EXECUTION_REPORT.md").exists():
            zf.write(pack_dir / "EXECUTION_REPORT.md", "EXECUTION_REPORT.md")

        # all files under actual_deliverables/
        for f in ad.iterdir():
            zf.write(f, f"actual_deliverables/{f.name}")

        # reports
        for rf in reports_dir.iterdir():
            zf.write(rf, f"reports/{rf.name}")

    print(f"Pack: {zip_path}")
    print(f"Run ID: {run_id}")


if __name__ == "__main__":
    main()
