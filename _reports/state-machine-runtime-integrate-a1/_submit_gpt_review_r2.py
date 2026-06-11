#!/usr/bin/env python3
"""_submit_gpt_review_r2.py — Submit GPT review R2 for STATE-MACHINE-RUNTIME-INTEGRATE-A1."""

import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
REPORT_DIR = Path(__file__).resolve().parent

TASK_ID = "STATE-MACHINE-RUNTIME-INTEGRATE-A1"
CHAT_URL = "https://chatgpt.com/c/6a26cc03-235c-83a2-a0fc-cd29be615959"
CDP_URL = "http://127.0.0.1:9222"

pack_dir = REPO / "evidence_packs" / "state-machine-runtime-integrate-a1"
zips = sorted(pack_dir.glob("*.zip"))
if not zips:
    print("ERROR: No evidence pack ZIP found")
    sys.exit(1)
PACK_PATH = zips[-1]

RUN_ID_PATH = REPORT_DIR / "R1_RUN_ID.txt"
OUTPUT_PATH = REPORT_DIR / "GPT_REVIEW_RESULT_R2.txt"
PROMPT_TEMPLATE = REPORT_DIR / "GPT_REVIEW_PROMPT.md"

def main():
    cmd = [
        sys.executable,
        str(REPO / "scripts" / "gpt_new_chat_attachment_submit.py"),
        "--task-id", TASK_ID,
        "--pack-path", str(PACK_PATH),
        "--run-id-path", str(RUN_ID_PATH),
        "--output-path", str(OUTPUT_PATH),
        "--prompt-template", str(PROMPT_TEMPLATE),
        "--chat-url", CHAT_URL,
        "--report-dir", str(REPORT_DIR),
        "--cdp-url", CDP_URL,
        "--timeout", "300",
    ]

    print(f"Task: {TASK_ID} (R2 — fix for blocked)")
    print(f"Pack: {PACK_PATH.name} ({PACK_PATH.stat().st_size} bytes)")
    print(f"Run ID: {RUN_ID_PATH.read_text().strip()}")
    print()

    result = subprocess.run(cmd, capture_output=False)
    sys.exit(result.returncode)

if __name__ == "__main__":
    main()
