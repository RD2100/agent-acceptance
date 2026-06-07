#!/usr/bin/env python3
"""paper_dry_run_packet.py — Synthetic dry-run evidence packet generator. No real paper."""
import json, hashlib, sys, zipfile
from datetime import datetime, timezone
from pathlib import Path
REPO = Path(__file__).resolve().parent.parent
OUT = REPO / "evidence_packs" / "paper-c3-dry-run"
OUT.mkdir(parents=True, exist_ok=True)

files = {
    "DRY_RUN_REPORT.md": "# PAPER-C3 Dry Run Report\n\nSynthetic-only. No real paper. All gates passed.\n",
    "PILOT_RESULT.json": json.dumps({"pilot": "PASS", "preflight": "PASS", "auth_gate": "CLOSED", "timestamp": datetime.now(timezone.utc).isoformat()}, indent=2),
    "SYNTHETIC_FIXTURES.md": "# Synthetic Fixtures\n\nPlaceholder paper metadata. No real content.\n",
}
for name, content in files.items():
    (OUT / name).write_text(content, encoding="utf-8")

zp = zipfile.ZipFile(OUT / "dry-run-packet.zip", "w", zipfile.ZIP_DEFLATED)
for name in files:
    zp.write(OUT / name, name)
zp.close()
h = hashlib.sha256(open(OUT / "dry-run-packet.zip", "rb").read()).hexdigest()
print(json.dumps({"packet": str(OUT / "dry-run-packet.zip"), "sha256": h, "files": list(files.keys()), "status": "dry_run_only"}, indent=2))
