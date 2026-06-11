#!/usr/bin/env python3
"""Build and submit R3 closure evidence pack to GPT."""
import zipfile
import shutil
import json
from pathlib import Path

PROJECT = Path(r"D:\agent-acceptance")
TASK_DIR = PROJECT / "_reports" / "conversation-registry-r3-close-and-multi-agent-pilot-prep-a1"
ZIP_PATH = TASK_DIR / "EVIDENCE_PACK.zip"

# Deliverables (relative to project root)
DELIVERABLES = [
    "scripts/awsp_scaffold.py",
    "scripts/validate_conversation_registry.py",
    "tests/test_conversation_registry.py",
    "tests/test_cross_project_scaffold.py",
    "docs/AGENT_WORKFLOW_STANDARD.md",
    "docs/MULTI_AGENT_MULTI_GPT_PILOT_PLAN.md",
    "docs/agent-runtime/capability-inventory.md",
    "docs/agent-runtime/tool-policy.md",
    "docs/agent-runtime/sub-agent-dispatch-protocol.md",
    "docs/governance/PROGRESS_LOG.md",
    "docs/governance/DECISION_LOG.md",
    "docs/governance/RISK_REGISTER.md",
    "docs/governance/TECH_DEBT.md",
    "docs/governance/VERIFY_MATRIX.md",
    "docs/governance/HANDOFF.md",
    ".agent/CONVERSATION_BINDING.json",
    ".agent/CONVERSATION_REGISTRY.schema.json",
]

# Reports (relative to task dir)
REPORTS = [
    "STARTUP_READ_PROOF.json",
    "STARTUP_READ_SUMMARY.md",
    "EXECUTION_REPORT.md",
    "CLOSURE_REPORT.md",
    "SAFETY_ATTESTATION.md",
    "GPT_REVIEW_PROMPT.md",
    "TARGET_TEST_OUTPUT.txt",
    "TARGETED_TEST_OUTPUT.txt",
    "RELATED_TEST_OUTPUT.txt",
    "TEST_OUTPUT.txt",
    "FULL_SUITE_OUTPUT.txt",
    "TESTS_SUITE_OUTPUT.txt",
    "REAL_PATH_PROBE.txt",
    "ROOT_BINDING_VALIDATION.txt",
    "RUN_ID_CONSISTENCY.txt",
    "PRE_GPT_REVIEW_GATE.txt",
    "ZIP_CHECK.txt",
    "CHANGED_FILES_EVIDENCE.txt",
    "run_id.txt",
    "R1_RUN_ID.txt",
    "PACK_MANIFEST.md",
]

if ZIP_PATH.exists():
    ZIP_PATH.unlink()

built = 0
missing = []
with zipfile.ZipFile(str(ZIP_PATH), 'w', zipfile.ZIP_DEFLATED) as zf:
    # Deliverables
    for rel in DELIVERABLES:
        src = PROJECT / rel
        if src.exists():
            zf.write(str(src), f"actual_deliverables/{Path(rel).name}")
            built += 1
        else:
            missing.append(rel)
    
    # Reports
    for rel in REPORTS:
        src = TASK_DIR / rel
        if src.exists():
            zf.write(str(src), f"reports/{rel}")
            built += 1
        else:
            missing.append(rel)

size = ZIP_PATH.stat().st_size
print(f"Built: {ZIP_PATH}")
print(f"Files: {built} included, {len(missing)} missing")
print(f"Size: {size:,} bytes")
if missing:
    print(f"Missing: {missing}")
