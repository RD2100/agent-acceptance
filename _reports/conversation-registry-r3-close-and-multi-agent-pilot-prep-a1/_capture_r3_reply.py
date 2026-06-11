#!/usr/bin/env python3
"""Capture the LATEST GPT response via CDP — waits for new content."""
import asyncio, sys
from pathlib import Path

try:
    from playwright.async_api import async_playwright
except ImportError:
    sys.exit("playwright not installed")

TASK_DIR = Path(r"D:\agent-acceptance\_reports\conversation-registry-r3-close-and-multi-agent-pilot-prep-a1")

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://localhost:9222")
        context = browser.contexts[0]
        page = context.pages[0]

        print(f"Page: {await page.title()}")

        # First, check if GPT is still generating
        stop_btn = page.locator('button[aria-label="Stop generating"]')
        if await stop_btn.count() > 0:
            print("GPT still generating, waiting up to 180s...")
            for i in range(36):
                await asyncio.sleep(5)
                if await stop_btn.count() == 0:
                    print(f"GPT finished at {(i+1)*5}s")
                    break

        # Count all assistant messages
        msgs = page.locator('[data-message-author-role="assistant"]')
        count = await msgs.count()
        print(f"Total assistant messages: {count}")

        if count > 0:
            # Get the LAST message
            last = msgs.nth(count - 1)
            text = await last.inner_text()
            print(f"Last message: {len(text)} chars")
            print(f"\n--- FULL RESPONSE ---\n{text}\n--- END ---")

            # Save
            result_file = TASK_DIR / "GPT_REVIEW_RESULT.txt"
            result_file.write_text(text, encoding="utf-8")
            print(f"\nSaved to {result_file}")

            has_judgment = "overall_judgment" in text.lower() or "judgment" in text.lower()
            has_accepted = "accepted" in text.lower()
            has_blocked = "blocked" in text.lower()
            has_human = "human_required" in text.lower()
            print(f"judgment={has_judgment}, accepted={has_accepted}, blocked={has_blocked}, human={has_human}")

        await browser.close()

asyncio.run(main())
