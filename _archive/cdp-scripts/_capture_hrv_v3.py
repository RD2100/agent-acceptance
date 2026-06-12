"""Capture GPT verdict for V3 submission."""
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

        # Navigate to GPT conversation
        await page.goto(GPT_URL, wait_until="domcontentloaded")
        await asyncio.sleep(5)

        # Wait for response to complete (no "stop" button visible = response done)
        max_wait = 180  # 3 minutes
        start = time.time()
        while time.time() - start < max_wait:
            # Check if response is still generating (stop button visible)
            stop_btn = page.locator('button[data-testid="stop-button"]')
            if not await stop_btn.is_visible():
                # Response complete - wait a bit more for rendering
                await asyncio.sleep(3)
                break
            await asyncio.sleep(5)
            elapsed = int(time.time() - start)
            print(f"  Waiting for GPT response... ({elapsed}s)")

        # Extract last assistant message
        messages = await page.query_selector_all('[data-message-author-role="assistant"]')
        if messages:
            last_msg = messages[-1]
            text = await last_msg.inner_text()
            Path(OUT_PATH).write_text(text, encoding="utf-8")
            print(f"Verdict captured to: {OUT_PATH}")
            print(f"Length: {len(text)} chars")
            print("---")
            # Print first 2000 chars
            print(text[:2000])
            if len(text) > 2000:
                print(f"\n... ({len(text) - 2000} more chars)")
        else:
            print("No assistant messages found!")


asyncio.run(main())
