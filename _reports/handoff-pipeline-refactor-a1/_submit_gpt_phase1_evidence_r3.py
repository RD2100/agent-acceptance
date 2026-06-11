import asyncio
import hashlib
import json
import time
from pathlib import Path

import pyperclip
from playwright.async_api import async_playwright

ROOT = Path("D:/agent-acceptance")
URL_ID = "6a23dd8c-4550-83a8-bdee-76ca5a982edb"
OUT = ROOT / "evidence_packs/handoff-pipeline-refactor-a1/GPT_REVIEW_RESULT_R3.txt"
REPORT_OUT = ROOT / "_reports/handoff-pipeline-refactor-a1/GPT_REVIEW_RESULT_R3.txt"
STATUS_OUT = ROOT / "_reports/handoff-pipeline-refactor-a1/GPT_SUBMISSION_STATUS_R3.json"
PACK = ROOT / "evidence_packs/handoff-pipeline-refactor-a1/closure-pack.zip"

FILES = [
    "HANDOFF_SOURCE_OF_TRUTH.md",
    "LEGACY_HANDOFF_INVENTORY.md",
    "_reports/handoff-pipeline-refactor-a1/HANDOFF_DRAFT_FOR_GPT.md",
    "_reports/handoff-pipeline-refactor-a1/HANDOFF_EVIDENCE_MAP.json",
    "_reports/handoff-pipeline-refactor-a1/HANDOFF_STALE_CHECK.md",
    "_reports/handoff-pipeline-refactor-a1/HANDOFF_SAFETY_SCAN.md",
    "_reports/handoff-pipeline-refactor-a1/TARGETED_TEST_OUTPUT.txt",
    "_reports/handoff-pipeline-refactor-a1/SAFETY_ATTESTATION.md",
    "_reports/handoff-pipeline-refactor-a1/PRE_GPT_GATE_OUTPUT.txt",
    "_reports/minimax-m3-observation/MINIMAX_M3_OBSERVATION_LOG.md",
    "evidence_packs/handoff-pipeline-refactor-a1/PACK_MANIFEST.md",
    "evidence_packs/handoff-pipeline-refactor-a1/CLOSURE_REPORT.md",
]

PROMPT = """GPT REVIEW REQUEST R3: HANDOFF-PIPELINE-REFACTOR-A1 PHASE 1 CLOSURE EVIDENCE

The previous R2 reply was review_unverified because you said Phase 1 evidence was unavailable. I am pasting the Phase 1 evidence mirror below directly in this message. Do not rely on old Phase 0 material.

Please review the pasted Phase 1 evidence and return ONLY the YAML block at the end.

Key facts to verify from pasted evidence:
- HANDOFF_SOURCE_OF_TRUTH.md defines P0/P1/P2/P3 hierarchy.
- LEGACY_HANDOFF_INVENTORY.md inventories legacy files without modifying them.
- Handoff draft says approval_status: draft_only and does not claim approved.
- Safety scan says pass: True / issues none.
- Targeted tests say 13 passed.
- Stale check intentionally flags stale risks including 232/247 conflicts and 296 PASS as unverified conversational claim.
- Minimax M3 observation log records objective evidence without final capability conclusion.
- Evidence pack linter and pre-GPT gate both passed.
- closure-pack.zip exists locally with SHA256 2e701b1e22e105fbf6adad73dd47a44d2478516e8cd4c39e3ad15c0b4055f793.

"""

TAIL = """

Return ONLY this YAML-like block. Use one of: accepted, accepted_with_limitation, blocked, review_unverified.

task_id: HANDOFF-PIPELINE-REFACTOR-A1
overall_judgment: accepted | accepted_with_limitation | blocked | review_unverified
safety_verdict: pass | fail | review_unverified
source_of_truth_verdict: pass | fail | review_unverified
stale_check_verdict: pass | fail | review_unverified
legacy_handoff_verdict: pass | fail | review_unverified
minimax_m3_observation_verdict: pass | fail | review_unverified
evidence_pack_reviewed: true | false
blocking_issues:
  - <issue or none>
required_fixes:
  - <fix or none>
limitations:
  - <limitation or none>
next_allowed_action: <specific next action>
END_OF_GPT_RESPONSE
"""


def build_message():
    parts = [PROMPT]
    for rel in FILES:
        path = ROOT / rel
        text = path.read_text(encoding="utf-8", errors="replace")
        max_len = 7000 if rel.endswith("PACK_MANIFEST.md") else 9000
        if len(text) > max_len:
            text = text[:max_len] + "\n...[TRUNCATED; enough excerpt included for review]...\n"
        parts.append(f"\n\n## FILE: {rel}\n```\n{text}\n```")
    parts.append(TAIL)
    return "".join(parts)


async def main():
    message = build_message()
    status = {"pack": str(PACK), "pack_exists": PACK.exists(), "message_chars": len(message), "uploaded": False, "sent": False, "captured": False}
    async with async_playwright() as pw:
        browser = await pw.chromium.connect_over_cdp("http://localhost:9222")
        page = None
        for ctx in browser.contexts:
            for pg in ctx.pages:
                if URL_ID in pg.url:
                    page = pg
                    break
            if page:
                break
        if page is None:
            raise RuntimeError("target page not found")
        await page.bring_to_front()
        await page.keyboard.press("Escape")
        await asyncio.sleep(1)
        try:
            inputs = page.locator('input[type="file"]')
            if await inputs.count() > 0:
                await inputs.first.set_input_files(str(PACK))
                status["uploaded"] = True
                await asyncio.sleep(6)
        except Exception as exc:
            status["upload_error"] = repr(exc)
        pyperclip.copy(message)
        editor = page.locator('div[contenteditable="true"].ProseMirror')
        if await editor.count() == 0:
            editor = page.locator('textarea, div[contenteditable="true"]').last
        await editor.click(timeout=15000)
        await page.keyboard.press("Control+v")
        await asyncio.sleep(2)
        await page.keyboard.press("Control+Enter")
        status["sent"] = True
        status["sent_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
        STATUS_OUT.write_text(json.dumps(status, ensure_ascii=False, indent=2), encoding="utf-8")
        last = ""
        stable = 0
        for _ in range(96):
            await asyncio.sleep(5)
            msgs = page.locator('[data-message-author-role="assistant"]')
            if await msgs.count() == 0:
                continue
            reply = await msgs.last.inner_text(timeout=10000)
            if reply == last:
                stable += 1
            else:
                stable = 0
                last = reply
            if "END_OF_GPT_RESPONSE" in reply:
                break
            if stable >= 10 and len(reply) > 300:
                break
        reply = last
        OUT.write_text(reply, encoding="utf-8")
        REPORT_OUT.write_text(reply, encoding="utf-8")
        status.update({"captured": bool(reply), "reply_chars": len(reply), "reply_sha256": hashlib.sha256(reply.encode("utf-8")).hexdigest() if reply else None, "valid_end_marker": "END_OF_GPT_RESPONSE" in reply, "result_path": str(OUT), "report_result_path": str(REPORT_OUT)})
        STATUS_OUT.write_text(json.dumps(status, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(status, ensure_ascii=False, indent=2))

asyncio.run(main())
