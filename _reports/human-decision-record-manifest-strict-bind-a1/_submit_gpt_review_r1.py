#!/usr/bin/env python3
"""_submit_gpt_review_r1.py — Submit GPT review R1 for HUMAN-DECISION-RECORD-MANIFEST-STRICT-BIND-A1."""
import subprocess, sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
REPORT_DIR = Path(__file__).resolve().parent
TASK_ID = "HUMAN-DECISION-RECORD-MANIFEST-STRICT-BIND-A1"
CHAT_URL = "https://chatgpt.com/c/6a26cc03-235c-83a2-a0fc-cd29be615959"
CDP_URL = "http://127.0.0.1:9222"

pack_dir = REPO / "evidence_packs" / TASK_ID.lower()
zips = sorted(pack_dir.glob("*.zip"))
if not zips: print("ERROR: No pack"); sys.exit(1)
PACK_PATH = zips[-1]

def main():
    cmd = [sys.executable, str(REPO / "scripts" / "gpt_new_chat_attachment_submit.py"),
        "--task-id", TASK_ID, "--pack-path", str(PACK_PATH),
        "--run-id-path", str(REPORT_DIR / "R1_RUN_ID.txt"),
        "--output-path", str(REPORT_DIR / "GPT_REVIEW_RESULT_R1.txt"),
        "--prompt-template", str(REPORT_DIR / "GPT_REVIEW_PROMPT.md"),
        "--chat-url", CHAT_URL, "--report-dir", str(REPORT_DIR),
        "--cdp-url", CDP_URL, "--timeout", "300"]
    result = subprocess.run(cmd, capture_output=False)
    sys.exit(result.returncode)

if __name__ == "__main__":
    main()
