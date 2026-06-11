import asyncio
import hashlib
import json
import time
from pathlib import Path

import pyperclip
from playwright.async_api import async_playwright

ROOT = Path("D:/agent-acceptance")
URL_ID = "6a23dd8c-4550-83a8-bdee-76ca5a982edb"
OUT = ROOT / "evidence_packs/handoff-pipeline-refactor-a1/GPT_REVIEW_RESULT_R2.txt"
REPORT_OUT = ROOT / "_reports/handoff-pipeline-refactor-a1/GPT_REVIEW_RESULT_R2.txt"
STATUS_OUT = ROOT / "_reports/handoff-pipeline-refactor-a1/GPT_SUBMISSION_STATUS_R2.json"

PROMPT = """Your previous reply was not machine-verifiable: it reviewed Phase 0 and did not include the required structured verdict for HANDOFF-PIPELINE-REFACTOR-A1 Phase 1 closure evidence.

Please now review the Phase 1 evidence already provided in the previous message (closure-pack.zip + pasted text mirror), especially:
- HANDOFF_SOURCE_OF_TRUTH.md
- LEGACY_HANDOFF_INVENTORY.md
- HANDOFF_DRAFT_FOR_GPT.md
- PASTE_BLOCK_DRAFT_FOR_NEW_GPT.txt
- HANDOFF_EVIDENCE_MAP.json
- HANDOFF_STALE_CHECK.md/json
- HANDOFF_SAFETY_SCAN.md
- TARGETED_TEST_OUTPUT.txt
- SAFETY_ATTESTATION.md
- MINIMAX_M3_OBSERVATION_LOG.md / EVIDENCE_TABLE.json
- PACK_MANIFEST.md and CLOSURE_REPORT.md

Return ONLY the following YAML-like block. Do not add prose before or after it. Use one of these overall_judgment values: accepted, accepted_with_limitation, blocked, review_unverified. If you think needs_fix is appropriate, encode it as overall_judgment: blocked and list exact required_fixes.

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

async def main():
    status = {"message_chars": len(PROMPT), "sent": False, "captured": False, "valid_end_marker": False}
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
            raise RuntimeError("target GPT conversation page not found")
        await page.bring_to_front()
        await page.keyboard.press("Escape")
        await asyncio.sleep(1)
        pyperclip.copy(PROMPT)
        editor = page.locator('div[contenteditable="true"].ProseMirror')
        if await editor.count() == 0:
            editor = page.locator('textarea, div[contenteditable="true"]').last
        await editor.click(timeout=15000)
        await page.keyboard.press("Control+v")
        await asyncio.sleep(1)
        await page.keyboard.press("Control+Enter")
        status["sent"] = True
        status["sent_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
        STATUS_OUT.write_text(json.dumps(status, ensure_ascii=False, indent=2), encoding="utf-8")

        last = ""
        stable = 0
        for _ in range(72):
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
            if stable >= 8 and len(reply) > 300:
                break
        reply = last
        OUT.write_text(reply, encoding="utf-8")
        REPORT_OUT.write_text(reply, encoding="utf-8")
        status.update({
            "captured": bool(reply),
            "reply_chars": len(reply),
            "reply_sha256": hashlib.sha256(reply.encode("utf-8")).hexdigest() if reply else None,
            "valid_end_marker": "END_OF_GPT_RESPONSE" in reply,
            "result_path": str(OUT),
            "report_result_path": str(REPORT_OUT),
        })
        STATUS_OUT.write_text(json.dumps(status, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(status, ensure_ascii=False, indent=2))

asyncio.run(main())
