"""Capture latest GPT reply from correct conversation."""
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
            print(f"Navigating to {TARGET_URL}")
            await page.goto(TARGET_URL, wait_until="domcontentloaded", timeout=30000)
            await asyncio.sleep(3)

        # Scroll to bottom to ensure latest message is loaded
        await page.evaluate("""() => {
            const container = document.querySelector('[class*="conversation"]') || document.querySelector('main');
            if (container) container.scrollTop = container.scrollHeight;
        }""")
        await asyncio.sleep(2)

        msgs = await page.query_selector_all('[data-message-author-role="assistant"]')
        print(f"Total assistant messages: {len(msgs)}")

        if msgs:
            last = msgs[-1]
            text = await last.inner_text()
            print(f"\nLatest message ({len(text)} chars):\n")
            print(text[:5000])
            with open("_evidence/hrv_verdict.txt", "w", encoding="utf-8") as f:
                f.write(text)
            print(f"\n--- Saved to _evidence/hrv_verdict.txt ---")

asyncio.run(main())
