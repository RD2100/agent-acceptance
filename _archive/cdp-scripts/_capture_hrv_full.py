"""Capture full GPT reply from correct conversation."""
import asyncio
from playwright.async_api import async_playwright

TARGET_URL = "https://chatgpt.com/c/6a297f76-3e7c-83a5-a0e5-b4413d923c7e"

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://localhost:9222")
        context = browser.contexts[0]
        page = None
        for pg in context.pages:
            if "chatgpt.com" in pg.url:
                page = pg
                break
        if not page:
            print("No page found")
            return

        if TARGET_URL not in page.url:
            await page.goto(TARGET_URL, wait_until="domcontentloaded", timeout=30000)
            await asyncio.sleep(3)

        # Scroll to bottom
        scroll_js = """() => {
            const el = document.querySelector('main');
            if (el) el.scrollTop = el.scrollHeight;
        }"""
        await page.evaluate(scroll_js)
        await asyncio.sleep(1)

        msgs = await page.query_selector_all('[data-message-author-role="assistant"]')
        print(f"Total assistant messages: {len(msgs)}")

        if msgs:
            last = msgs[-1]
            text = await last.inner_text()
            with open("_evidence/hrv_verdict_full.txt", "w", encoding="utf-8") as f:
                f.write(text)
            print(f"Total chars: {len(text)}")
            print(text)

asyncio.run(main())
