import asyncio
import hashlib
import json
from pathlib import Path
from playwright.async_api import async_playwright

ROOT = Path('D:/agent-acceptance')
RUN_ID = (ROOT / '_reports/global-project-evidence-binding-a1/GPT_REVIEW_RUN_ID.txt').read_text(encoding='utf-8').strip()
URL = (ROOT / '_reports/global-project-evidence-binding-a1/GPT_REVIEW_CHAT_URL.txt').read_text(encoding='utf-8').strip()
REPORT_RESULT = ROOT / '_reports/global-project-evidence-binding-a1/GPT_REVIEW_RESULT.txt'
PACK_RESULT = ROOT / 'evidence_packs/global-project-evidence-binding-a1/GPT_REVIEW_RESULT.txt'
STATUS = ROOT / '_reports/global-project-evidence-binding-a1/GPT_REVIEW_SUBMISSION_STATUS.json'

async def main():
    async with async_playwright() as pw:
        browser = await pw.chromium.connect_over_cdp('http://localhost:9222')
        ctx = browser.contexts[0] if browser.contexts else await browser.new_context()
        page = None
        for pg in ctx.pages:
            if URL in pg.url:
                page = pg
                break
        if page is None:
            page = await ctx.new_page()
            await page.goto(URL, wait_until='domcontentloaded', timeout=60000)
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
