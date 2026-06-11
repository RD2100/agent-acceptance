#!/usr/bin/env python3
"""Build R2 evidence pack for CONVERSATION-REGISTRY-A1."""
import zipfile
import shutil
from pathlib import Path

TASK_DIR = Path(r"D:\agent-acceptance\_reports\universal-agent-workflow-standard-conversation-registry-a1")
PROJECT = Path(r"D:\agent-acceptance")
PACK_DIR = TASK_DIR / "evidence_pack_r2"
ZIP_PATH = TASK_DIR / "EVIDENCE_PACK_R2.zip"

# Clean previous
if PACK_DIR.exists():
    shutil.rmtree(str(PACK_DIR))
PACK_DIR.mkdir(parents=True)
(PACK_DIR / "actual_deliverables").mkdir()
(PACK_DIR / "reports").mkdir()

# Copy report docs
for f in [
    "CLOSURE_REPORT_R2.md",
    "GPT_REVIEW_PROMPT_R2.md",
    "SAFETY_ATTESTATION_R2.md",
    "EXECUTION_REPORT_R2.md",
]:
    shutil.copy2(str(TASK_DIR / f), str(PACK_DIR / "reports" / f))

# Copy source files as actual deliverables
for f in [
    "scripts/awsp_scaffold.py",
    "scripts/validate_conversation_registry.py",
    "tests/test_conversation_registry.py",
    "tests/test_cross_project_scaffold.py",
]:
    shutil.copy2(str(PROJECT / f), str(PACK_DIR / "actual_deliverables" / Path(f).name))

# Copy test outputs
for f in ["TARGET_TEST_OUTPUT_R2.txt", "FULL_SUITE_OUTPUT_R2.txt"]:
    shutil.copy2(str(TASK_DIR / f), str(PACK_DIR / "reports" / f))

# Create PACK_MANIFEST.md
manifest = """# PACK MANIFEST — CONVERSATION-REGISTRY-A1 R2

| Field | Value |
|-------|-------|
| Task ID | UNIVERSAL-AGENT-WORKFLOW-STANDARD-CONVERSATION-REGISTRY-A1-R2 |
| Run ID | UNIVERSAL_AGENT_WORKFLOW_STANDARD_CONVERSATION_REGISTRY_A1_20260609T172643_RD |
| AWSP Version | 1.3.0 |
| Date | 2026-06-09 |
| Pack Version | R2 |

## Contents

### Root
- PACK_MANIFEST.md (this file)

### reports/
- CLOSURE_REPORT_R2.md
- GPT_REVIEW_PROMPT_R2.md
- SAFETY_ATTESTATION_R2.md
- EXECUTION_REPORT_R2.md
- TARGET_TEST_OUTPUT_R2.txt
- FULL_SUITE_OUTPUT_R2.txt

### actual_deliverables/
- awsp_scaffold.py
- validate_conversation_registry.py
- test_conversation_registry.py
- test_cross_project_scaffold.py
"""
(PACK_DIR / "PACK_MANIFEST.md").write_text(manifest, encoding="utf-8")

# Build ZIP
if ZIP_PATH.exists():
    ZIP_PATH.unlink()
with zipfile.ZipFile(str(ZIP_PATH), 'w', zipfile.ZIP_DEFLATED) as zf:
    for p in sorted(PACK_DIR.rglob("*")):
        if p.is_file():
            arcname = p.relative_to(PACK_DIR)
            zf.write(str(p), str(arcname))

print(f"Built: {ZIP_PATH}")
print(f"Size: {ZIP_PATH.stat().st_size:,} bytes")

# Cleanup temp dir
shutil.rmtree(str(PACK_DIR))
print("Cleaned up temp directory")
