import asyncio
import hashlib
import json
import time
from pathlib import Path

import pyperclip
from playwright.async_api import async_playwright

ROOT = Path("D:/agent-acceptance")
URL_ID = "6a23dd8c-4550-83a8-bdee-76ca5a982edb"
TARGET_URL = "https://chatgpt.com/c/6a23dd8c-4550-83a8-bdee-76ca5a982edb"
PACK = ROOT / "evidence_packs/handoff-pipeline-refactor-a1/closure-pack.zip"
OUT = ROOT / "evidence_packs/handoff-pipeline-refactor-a1/GPT_REVIEW_RESULT.txt"
REPORT_OUT = ROOT / "_reports/handoff-pipeline-refactor-a1/GPT_REVIEW_RESULT.txt"
STATUS_OUT = ROOT / "_reports/handoff-pipeline-refactor-a1/GPT_SUBMISSION_STATUS.json"

FILES = [
    "HANDOFF_SOURCE_OF_TRUTH.md",
    "LEGACY_HANDOFF_INVENTORY.md",
    "_reports/handoff-pipeline-refactor-a1/HANDOFF_DRAFT_FOR_GPT.md",
    "_reports/handoff-pipeline-refactor-a1/PASTE_BLOCK_DRAFT_FOR_NEW_GPT.txt",
    "_reports/handoff-pipeline-refactor-a1/HANDOFF_EVIDENCE_MAP.json",
    "_reports/handoff-pipeline-refactor-a1/HANDOFF_STALE_CHECK.md",
    "_reports/handoff-pipeline-refactor-a1/HANDOFF_STALE_CHECK.json",
    "_reports/handoff-pipeline-refactor-a1/HANDOFF_SAFETY_SCAN.md",
    "_reports/handoff-pipeline-refactor-a1/TARGETED_TEST_OUTPUT.txt",
    "_reports/handoff-pipeline-refactor-a1/SAFETY_ATTESTATION.md",
    "_reports/minimax-m3-observation/MINIMAX_M3_OBSERVATION_LOG.md",
    "_reports/minimax-m3-observation/MINIMAX_M3_EVIDENCE_TABLE.json",
    "evidence_packs/handoff-pipeline-refactor-a1/PACK_MANIFEST.md",
    "evidence_packs/handoff-pipeline-refactor-a1/CLOSURE_REPORT.md",
]

PROMPT = """GPT REVIEW REQUEST: HANDOFF-PIPELINE-REFACTOR-A1

Please review the attached / provided evidence for HANDOFF-PIPELINE-REFACTOR-A1.

Task goal: Refactor the GPT and coding-agent handoff pipeline so that future GPT handoffs are source-of-truth bound, stale-checked, safety-scanned, and GPT-reviewed before being treated as approved.

Review scope:
1. HANDOFF_SOURCE_OF_TRUTH.md
2. LEGACY_HANDOFF_INVENTORY.md
3. HANDOFF_DRAFT_FOR_GPT.md
4. PASTE_BLOCK_DRAFT_FOR_NEW_GPT.txt
5. HANDOFF_EVIDENCE_MAP.json
6. HANDOFF_STALE_CHECK.md/json
7. HANDOFF_SAFETY_SCAN.md
8. TARGETED_TEST_OUTPUT.txt
9. SAFETY_ATTESTATION.md
10. MINIMAX_M3_OBSERVATION_LOG.md / EVIDENCE_TABLE.json

Please judge whether the implementation satisfies the intended constraints:
Core requirements:
- Establishes a clear source-of-truth hierarchy: P0 = captured GPT verdicts, evidence packs, TEST_OUTPUT, Project Index, issue ledger, manifests. P1 = GPT-approved BOOT_CONTEXT / HANDOFF / PASTE_BLOCK. P2 = claude-memory-compiler / memory/index recall layer. P3 = legacy PROJECT_HISTORY / old HANDOFF / old PASTE_BLOCK.
- Treats memory compiler as recall layer, not source of truth.
- Prevents coding agent from declaring final approved handoff without GPT review.
- Generates handoff draft and paste block without paper full text, original paragraphs, private notes, or advisor comments.
- Detects stale memory / stale Project Index risks.
- Preserves accepted_with_limitation and human_required without flattening.
- Does not delete, move, rename, or clean old handoff documents.
- Produces legacy inventory instead of destructive cleanup.
- Establishes Minimax M3 observation logging without making premature final capability claims.
- Includes targeted tests and safety attestation.

Please check for:
- Missing source-of-truth evidence.
- Stale status risks.
- Any unsafe inclusion of paper text.
- Any overclaim that draft handoff is already approved.
- Whether old handoff docs were improperly modified or deleted.
- Whether tests are meaningful or superficial.
- Whether Minimax M3 observation logging is objective enough for future model capability assessment.

Return a verdict for HANDOFF-PIPELINE-REFACTOR-A1:
overall_judgment: accepted | accepted_with_limitation | needs_fix | blocked | review_unverified
If not fully accepted, list exact blockers and required fixes.
Also include:
- safety_verdict
- source_of_truth_verdict
- stale_check_verdict
- legacy_handoff_verdict
- minimax_m3_observation_verdict
- next_allowed_action
Do not infer from agent summary alone. Base the verdict on the provided evidence.
END_OF_GPT_RESPONSE
"""


def build_message():
    parts = [PROMPT, "\n\n# PROVIDED EVIDENCE (text mirror of closure-pack.zip)\n"]
    for rel in FILES:
        path = ROOT / rel
        text = path.read_text(encoding="utf-8", errors="replace")
        if len(text) > 12000:
            text = text[:12000] + "\n...[TRUNCATED IN PASTE; full file included in closure-pack.zip if upload succeeded]...\n"
        parts.append(f"\n\n## FILE: {rel}\n```\n{text}\n```")
    return "".join(parts)


async def main():
    message = build_message()
    status = {
        "pack": str(PACK),
        "pack_exists": PACK.exists(),
        "message_chars": len(message),
        "uploaded": False,
        "sent": False,
        "captured": False,
        "valid_end_marker": False,
    }
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
            page = await browser.contexts[0].new_page()
            await page.goto(TARGET_URL, wait_until="domcontentloaded", timeout=60000)
        await page.bring_to_front()
        await page.keyboard.press("Escape")
        await asyncio.sleep(1)

        try:
            inputs = page.locator('input[type="file"]')
            if await inputs.count() > 0:
                await inputs.first.set_input_files(str(PACK))
                status["uploaded"] = True
                await asyncio.sleep(8)
        except Exception as exc:
            status["upload_error"] = repr(exc)

        pyperclip.copy(message)
        editor = page.locator('div[contenteditable="true"].ProseMirror')
        if await editor.count() == 0:
            editor = page.locator('textarea, div[contenteditable="true"]').last
        await editor.click(timeout=15000)
        await page.keyboard.press("Control+v")
        await asyncio.sleep(3)
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
            if stable >= 8 and len(reply) > 500:
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
