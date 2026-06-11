import asyncio
import json
from pathlib import Path
from playwright.async_api import async_playwright

ROOT = Path('D:/agent-acceptance')
RUN_ID = (ROOT / '_reports/global-project-evidence-binding-a1/GPT_REVIEW_RUN_ID.txt').read_text(encoding='utf-8').strip()
URL = (ROOT / '_reports/global-project-evidence-binding-a1/GPT_REVIEW_CHAT_URL.txt').read_text(encoding='utf-8').strip()
OUT = ROOT / '_reports/global-project-evidence-binding-a1/GPT_PAGE_OBSERVE.json'

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
        await asyncio.sleep(2)
        users = []
        assistants = []
        u = page.locator('[data-message-author-role="user"]')
        a = page.locator('[data-message-author-role="assistant"]')
        for i in range(await u.count()):
            txt = await u.nth(i).inner_text(timeout=5000)
            users.append({'index': i, 'chars': len(txt), 'has_run_id': RUN_ID in txt, 'excerpt': txt[:1200]})
        for i in range(await a.count()):
            txt = await a.nth(i).inner_text(timeout=5000)
            assistants.append({'index': i, 'chars': len(txt), 'has_run_id': RUN_ID in txt, 'has_end_marker': 'END_OF_GPT_RESPONSE' in txt, 'has_overall_judgment': 'overall_judgment:' in txt, 'excerpt': txt[:1200]})
        body = await page.locator('body').inner_text(timeout=10000)
        result = {'url': page.url, 'run_id': RUN_ID, 'user_count': len(users), 'assistant_count': len(assistants), 'target_run_id_in_body': RUN_ID in body, 'last_users': users[-3:], 'last_assistants': assistants[-3:]}
        OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
        print(json.dumps(result, ensure_ascii=False, indent=2))

asyncio.run(main())
