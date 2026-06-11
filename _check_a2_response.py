"""Check GPT response after waiting."""
import asyncio
import sys
from pathlib import Path
from playwright.async_api import async_playwright

sys.stdout.reconfigure(encoding='utf-8')


async def check():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://localhost:9222")
        ctx = browser.contexts[0]
        page = None
        for pg in ctx.pages:
            if "6a2a8cb1" in pg.url:
                page = pg
                break
        if not page:
            page = ctx.pages[0]

        await page.wait_for_timeout(5000)

        ams = page.locator('div[data-message-author-role="assistant"]')
        cnt = await ams.count()
        print(f"Assistant messages: {cnt}")

        if cnt > 0:
            last = await ams.last.inner_text()
            print(f"Last msg length: {len(last)} chars")
            print(last[:8000])
            if len(last) > 8000:
                print(f"\n... ({len(last) - 8000} more)")

            op = Path(r"D:\agent-acceptance\_evidence\conversation_health_gate_a2_verdict.txt")
            op.write_text(last, encoding="utf-8")
            print(f"\nSaved: {op}")

            upper = last.upper()
            for kw in ["ACCEPTED", "REJECTED", "NEEDS_REVISION"]:
                if kw in upper:
                    print(f"\n*** VERDICT: {kw} ***")
                    break


asyncio.run(check())
