#!/usr/bin/env python3
"""Build evidence pack ZIP for MULTI-AGENT-MULTI-GPT-PILOT-A1."""
import json
import os
import shutil
import zipfile
from pathlib import Path

REPO = Path(r"D:\agent-acceptance")
TASK_DIR = REPO / "_reports" / "multi-agent-multi-gpt-pilot-a1"
PACK_DIR = TASK_DIR / "evidence_pack"
ZIP_PATH = TASK_DIR / "EVIDENCE_PACK.zip"

# Clean previous
if PACK_DIR.exists():
    shutil.rmtree(PACK_DIR)

actual_dir = PACK_DIR / "actual_deliverables"
reports_dir = PACK_DIR / "reports"
actual_dir.mkdir(parents=True)
reports_dir.mkdir(parents=True)

# Actual deliverables
deliverables = {
    ".agent/CONVERSATION_BINDING.json": "CONVERSATION_BINDING.json",
    ".agent/CONVERSATION_REGISTRY.schema.json": "CONVERSATION_REGISTRY.schema.json",
    "scripts/pilot_activation_record.py": "pilot_activation_record.py",
    "scripts/multi_agent_gate0_preflight.py": "multi_agent_gate0_preflight.py",
    "scripts/multi_agent_dispatch_plan.py": "multi_agent_dispatch_plan.py",
    "scripts/validate_conversation_registry.py": "validate_conversation_registry.py",
    "scripts/validate_multi_agent_dispatch_plan.py": "validate_multi_agent_dispatch_plan.py",
    "tests/test_pilot_activation.py": "test_pilot_activation.py",
    "tests/test_conversation_registry.py": "test_conversation_registry.py",
    "tests/test_multi_agent_gate0_preflight.py": "test_multi_agent_gate0_preflight.py",
    "tests/test_multi_agent_dispatch_plan.py": "test_multi_agent_dispatch_plan.py",
    "tests/test_validate_multi_agent_dispatch_plan.py": "test_validate_multi_agent_dispatch_plan.py",
    "schemas/agent-runtime/multi-agent-dispatch-plan.schema.json": "multi-agent-dispatch-plan.schema.json",
    "schemas/agent-runtime/multi-agent-gate0-preflight.schema.json": "multi-agent-gate0-preflight.schema.json",
    "schemas/agent-runtime/task-spec.schema.json": "task-spec.schema.json",
    "docs/MULTI_AGENT_MULTI_GPT_PILOT_PLAN.md": "MULTI_AGENT_MULTI_GPT_PILOT_PLAN.md",
}

for src_rel, dst_name in deliverables.items():
    src = REPO / src_rel
    if src.exists():
        shutil.copy2(src, actual_dir / dst_name)

# Reports
reports = {
    "EXECUTION_REPORT.md": "EXECUTION_REPORT.md",
    "SAFETY_ATTESTATION.md": "SAFETY_ATTESTATION.md",
    "ACTIVATION_RECORD.json": "ACTIVATION_RECORD.json",
    "GATE0_PREFLIGHT_R3.json": "GATE0_PREFLIGHT_R3.json",
    "GATE0_PREFLIGHT_R4.json": "GATE0_PREFLIGHT_R4.json",
    "DISPATCH_PLAN_R2.json": "DISPATCH_PLAN_R2.json",
    "DISPATCH_PLAN_R3.json": "DISPATCH_PLAN_R3.json",
    "BETA_CONVERSATION.json": "BETA_CONVERSATION.json",
    "TARGET_TEST_OUTPUT.txt": "TARGET_TEST_OUTPUT.txt",
    "FULL_SUITE_OUTPUT.txt": "FULL_SUITE_OUTPUT.txt",
    "FULL_SUITE_R2.txt": "FULL_SUITE_R2.txt",
    "run_id.txt": "run_id.txt",
}

for src_name, dst_name in reports.items():
    src = TASK_DIR / src_name
    if src.exists():
        shutil.copy2(src, reports_dir / dst_name)

# Manifest
manifest_lines = ["# Evidence Pack Manifest", "",
    f"| Field | Value |", "|-------|-------|",
    f"| task_id | MULTI-AGENT-MULTI-GPT-PILOT-A1 |",
    f"| run_id | MULTI_AGENT_MULTI_GPT_PILOT_A1_20260610T102443_RD |",
    f"| generated | 2026-06-10 |", "", "## actual_deliverables/", ""]

for f in sorted(actual_dir.iterdir()):
    manifest_lines.append(f"- {f.name} ({f.stat().st_size:,} bytes)")

manifest_lines.append("\n## reports/\n")
for f in sorted(reports_dir.iterdir()):
    manifest_lines.append(f"- {f.name} ({f.stat().st_size:,} bytes)")

manifest_text = "\n".join(manifest_lines)
(PACK_DIR / "PACK_MANIFEST.md").write_text(manifest_text, encoding="utf-8")

# Build ZIP
with zipfile.ZipFile(ZIP_PATH, "w", zipfile.ZIP_DEFLATED) as zf:
    for root, dirs, files in os.walk(PACK_DIR):
        root_path = Path(root)
        for name in sorted(files):
            full = root_path / name
            arcname = full.relative_to(PACK_DIR)
            zf.write(full, arcname)

print(f"Evidence pack: {ZIP_PATH}")
print(f"  ZIP size: {ZIP_PATH.stat().st_size:,} bytes")
print(f"  Files: {sum(1 for _ in zipfile.ZipFile(ZIP_PATH).namelist())}")
for name in zipfile.ZipFile(ZIP_PATH).namelist():
    print(f"    {name}")
