#!/usr/bin/env python3
"""Observe current GPT page state and find our run_id reply."""
import asyncio, json
from pathlib import Path
from playwright.async_api import async_playwright

ROOT = Path('D:/agent-acceptance')
RUN_ID = 'HANDOFF_WORKFLOW_HARDENING_PLAN_A1_REVIEW_20260609_012328_RD'
TARGET_URL = 'https://chatgpt.com/c/6a26cc03-235c-83a2-a0fc-cd29be615959'
OUT = ROOT / '_reports/handoff-workflow-hardening-plan-a1/GPT_PAGE_OBSERVE.json'

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
            print('Target page not found')
            return
        await page.bring_to_front()
        await asyncio.sleep(2)

        users = []
        assistants = []
        u = page.locator('[data-message-author-role="user"]')
        a = page.locator('[data-message-author-role="assistant"]')

        for i in range(await u.count()):
            txt = await u.nth(i).inner_text(timeout=5000)
            users.append({
                'index': i, 'chars': len(txt),
                'has_run_id': RUN_ID in txt,
                'excerpt': txt[:500],
            })

        for i in range(await a.count()):
            txt = await a.nth(i).inner_text(timeout=5000)
            assistants.append({
                'index': i, 'chars': len(txt),
                'has_run_id': RUN_ID in txt,
                'has_end_marker': 'END_OF_GPT_RESPONSE' in txt,
                'has_overall_judgment': 'overall_judgment:' in txt,
                'excerpt': txt[:500],
            })

        result = {
            'url': page.url,
            'run_id': RUN_ID,
            'user_count': len(users),
            'assistant_count': len(assistants),
            'users': users,
            'assistants': assistants,
        }
        OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
        print(json.dumps(result, ensure_ascii=False, indent=2))

asyncio.run(main())
