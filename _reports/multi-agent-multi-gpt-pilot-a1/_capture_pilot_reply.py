#!/usr/bin/env python3
"""Capture latest GPT response for pilot-a1 via CDP."""
import asyncio, sys
from pathlib import Path
from playwright.async_api import async_playwright

TASK_DIR = Path(r"D:\agent-acceptance\_reports\multi-agent-multi-gpt-pilot-a1")

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://localhost:9222")
        context = browser.contexts[0]
        page = context.pages[0]

        # Wait for generation to finish
        for i in range(36):
            stop_btn = page.locator('button[aria-label="Stop generating"]')
            if await stop_btn.count() > 0:
                print(f"  Still generating... {(i+1)*5}s")
                await asyncio.sleep(5)
            else:
                break

        msgs = page.locator('[data-message-author-role="assistant"]')
        count = await msgs.count()
        print(f"Total assistant messages: {count}")

        if count > 0:
            last = msgs.nth(count - 1)
            text = await last.inner_text()
            print(f"Last message: {len(text)} chars")
            print(f"\n--- FULL RESPONSE ---\n{text}\n--- END ---")

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
