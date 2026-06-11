#!/usr/bin/env python3
"""Capture all GPT messages from the B1 submission conversation."""
import asyncio, json, sys
from pathlib import Path

try:
    from playwright.async_api import async_playwright
except ImportError:
    sys.exit("ERROR: playwright not installed")

TASK_DIR = Path(r"D:\agent-acceptance\_reports\multi-agent-bounded-execution-b1")
SELECTOR = '[data-message-author-role="assistant"]'


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://localhost:9222")
        context = browser.contexts[0]
        page = context.pages[0]

        title = await page.title()
        url = page.url
        print(f"Page: {title} ({url})")

        msgs = page.locator(SELECTOR)
        count = await msgs.count()
        print(f"Total assistant messages: {count}")

        longest_text = ""
        longest_idx = 0

        for i in range(count):
            msg = msgs.nth(i)
            text = await msg.inner_text()
            print(f"  Message {i+1}: {len(text)} chars")
            if len(text) > len(longest_text):
                longest_text = text
                longest_idx = i

        # Save the longest (likely the full review)
        if longest_text:
            result_file = TASK_DIR / "GPT_REVIEW_RESULT.txt"
            result_file.write_text(longest_text, encoding="utf-8")
            print(f"\nSaved longest message ({len(longest_text)} chars, index={longest_idx})")
            print(f"Preview:\n{longest_text[:600]}")


asyncio.run(main())
