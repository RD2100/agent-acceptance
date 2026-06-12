"""Capture GPT verdict for V3 - robust approach."""
import asyncio
import time
from pathlib import Path
from playwright.async_api import async_playwright

GPT_URL = "https://chatgpt.com/c/6a297f76-3e7c-83a5-a0e5-b4413f923c7e"
OUT_PATH = r"D:\agent-acceptance\_evidence\hrv_v3_verdict.txt"


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://localhost:9222")
        context = browser.contexts[0]
        page = context.pages[0] if context.pages else await context.new_page()

        await page.goto(GPT_URL, wait_until="domcontentloaded")
        await asyncio.sleep(5)

        # Wait for response to complete
        max_wait = 180
        start = time.time()
        while time.time() - start < max_wait:
            stop_btn = page.locator('button[data-testid="stop-button"]')
            send_btn = page.locator('button[data-testid="send-button"]')
            is_generating = await stop_btn.is_visible()
            is_send_visible = await send_btn.is_visible()
            elapsed = int(time.time() - start)
            print(f"  [{elapsed}s] generating={is_generating}, send_visible={is_send_visible}")
            if not is_generating:
                await asyncio.sleep(5)
                break
            await asyncio.sleep(5)

        # Scroll to bottom to ensure latest message is rendered
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await asyncio.sleep(2)

        # Try multiple selectors for assistant messages
        text = ""
        for selector in [
            '[data-message-author-role="assistant"]',
            '.agent-turn',
            '[class*="assistant"]',
            'div[class*="markdown"]',
        ]:
            msgs = await page.query_selector_all(selector)
            if msgs:
                last = msgs[-1]
                text = await last.inner_text()
                print(f"Found {len(msgs)} elements with selector: {selector}")
                break

        if not text:
            # Fallback: get entire page text
            text = await page.inner_text("body")
            print("Used full page text fallback")

        Path(OUT_PATH).write_text(text, encoding="utf-8")
        print(f"Verdict captured to: {OUT_PATH}")
        print(f"Length: {len(text)} chars")
        print("---")
        print(text[:3000])
        if len(text) > 3000:
            print(f"\n... ({len(text) - 3000} more chars)")


asyncio.run(main())
