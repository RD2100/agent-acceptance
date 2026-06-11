#!/usr/bin/env python3
"""
paper_dry_run_packet.py — Synthetic dry-run evidence packet generator.

Usage: python scripts/paper_dry_run_packet.py [--output <dir>] [--task-id <id>]
Generates a synthetic evidence packet with DRY_RUN_REPORT, PILOT_RESULT, and fixtures.
No real paper content. Fail-closed.
"""
import argparse, json, hashlib, sys, zipfile
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent


def generate(output_dir=None, task_id="paper-c3-dry-run"):
    """Generate synthetic dry-run evidence packet."""
    out = Path(output_dir) if output_dir else (REPO / "evidence_packs" / task_id)
    out.mkdir(parents=True, exist_ok=True)

    ts = datetime.now(timezone.utc).isoformat()
    files = {
        "DRY_RUN_REPORT.md": f"# {task_id.upper()} Dry Run Report\n\nSynthetic-only. No real paper. All gates passed.\nGenerated: {ts}\n",
        "PILOT_RESULT.json": json.dumps({
            "task_id": task_id, "pilot": "PASS", "preflight": "PASS",
            "auth_gate": "CLOSED", "timestamp": ts,
        }, indent=2),
        "SYNTHETIC_FIXTURES.md": "# Synthetic Fixtures\n\nPlaceholder paper metadata. No real paper content.\n",
    }

    for name, content in files.items():
        (out / name).write_text(content, encoding="utf-8")

    zip_path = out / f"{task_id}-packet.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zp:
        for name in files:
            zp.write(out / name, name)

    sha = hashlib.sha256(zip_path.read_bytes()).hexdigest()
    return {
        "packet": str(zip_path), "sha256": sha,
        "files": list(files.keys()), "status": "dry_run_only",
        "output_dir": str(out),
    }


def main():
    parser = argparse.ArgumentParser(description="Generate synthetic dry-run evidence packet")
    parser.add_argument("--output", help="Output directory")
    parser.add_argument("--task-id", default="paper-c3-dry-run", help="Task ID for naming")
    args = parser.parse_args()

    result = generate(args.output, args.task_id)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    sys.exit(0)


if __name__ == "__main__":
    main()
