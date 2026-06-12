"""Capture V4 verdict from GPT."""
import asyncio
import time
from pathlib import Path
from playwright.async_api import async_playwright

CONVO_URL = "https://chatgpt.com/c/6a2a8cb1-b228-83aa-addb-79bda9aba043"
OUT_PATH = r"D:\agent-acceptance\_evidence\hrv_v4_verdict.txt"


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://localhost:9222")
        context = browser.contexts[0]
        page = context.pages[0] if context.pages else await context.new_page()

        await page.goto(CONVO_URL, wait_until="domcontentloaded")
        await asyncio.sleep(5)

        # Wait for response to complete (max 5 min)
        max_wait = 300
        start = time.time()
        while time.time() - start < max_wait:
            stop_btn = page.locator('button[data-testid="stop-button"]')
            is_gen = await stop_btn.is_visible()
            elapsed = int(time.time() - start)
            if elapsed % 15 == 0:
                print(f"  [{elapsed}s] generating={is_gen}")
            if not is_gen:
                await asyncio.sleep(5)
                break
            await asyncio.sleep(5)

        # Scroll to bottom
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await asyncio.sleep(2)

        # Get last assistant message
        text = ""
        for sel in [
            '[data-message-author-role="assistant"]',
            'div[class*="markdown"]',
        ]:
            msgs = await page.locator(sel).all()
            if msgs:
                last = msgs[-1]
                text = await last.inner_text()
                print(f"Selector '{sel}': {len(msgs)} elements, last={len(text)} chars")
                break

        if not text:
            text = await page.inner_text("body")
            print(f"Fallback: {len(text)} chars")

        Path(OUT_PATH).write_text(text, encoding="utf-8")
        print(f"Verdict saved: {OUT_PATH} ({len(text)} chars)")


asyncio.run(main())
