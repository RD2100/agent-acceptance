#!/usr/bin/env python3
"""Capture the correct GPT reply matching our run_id."""
import asyncio, hashlib, json
from pathlib import Path
from playwright.async_api import async_playwright

ROOT = Path('D:/agent-acceptance')
RUN_ID = 'HANDOFF_WORKFLOW_HARDENING_PLAN_A1_REVIEW_20260609_012328_RD'
TARGET_URL = 'https://chatgpt.com/c/6a26cc03-235c-83a2-a0fc-cd29be615959'
REPORT_RESULT = ROOT / '_reports/handoff-workflow-hardening-plan-a1/GPT_REVIEW_RESULT.txt'
PACK_RESULT = ROOT / 'evidence_packs/handoff-workflow-hardening-plan-a1/GPT_REVIEW_RESULT.txt'
STATUS = ROOT / '_reports/handoff-workflow-hardening-plan-a1/GPT_REVIEW_SUBMISSION_STATUS.json'

async def main():
    async with async_playwright() as pw:
        browser = await pw.chromium.connect_over_cdp('http://127.0.0.1:9222')
        ctx = browser.contexts[0]
        page = None
        for pg in ctx.pages:
            if TARGET_URL in pg.url:
                page = pg
                break
        if page is None:
            raise SystemExit('target page not found')
        await page.bring_to_front()
        await asyncio.sleep(1)

        msgs = page.locator('[data-message-author-role="assistant"]')
        target = None
        target_index = None
        for i in range(await msgs.count()):
            txt = await msgs.nth(i).inner_text(timeout=10000)
            if RUN_ID in txt and 'overall_judgment:' in txt and 'END_OF_GPT_RESPONSE' in txt:
                target = txt
                target_index = i

        if target is None:
            raise SystemExit('target reply not found')

        REPORT_RESULT.write_text(target, encoding='utf-8')
        PACK_RESULT.write_text(target, encoding='utf-8')

        status = json.loads(STATUS.read_text(encoding='utf-8')) if STATUS.exists() else {}
        status.update({
            'captured': True,
            'capture_corrected_from_page': True,
            'target_reply_index': target_index,
            'run_id_match': True,
            'has_end_marker': True,
            'has_overall_judgment': True,
            'reply_chars': len(target),
            'reply_sha256': hashlib.sha256(target.encode('utf-8')).hexdigest(),
            'chat_url_final': page.url,
            'result_path': str(PACK_RESULT),
            'report_result_path': str(REPORT_RESULT),
        })
        STATUS.write_text(json.dumps(status, ensure_ascii=False, indent=2), encoding='utf-8')
        print(json.dumps(status, ensure_ascii=False, indent=2))

asyncio.run(main())
