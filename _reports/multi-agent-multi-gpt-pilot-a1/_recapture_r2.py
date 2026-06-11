#!/usr/bin/env python3
"""Re-capture the full GPT review response."""
import asyncio
import sys
from pathlib import Path

try:
    from playwright.async_api import async_playwright
except ImportError:
    sys.exit("ERROR: playwright not installed")

TASK_DIR = Path(r"D:\agent-acceptance\_reports\multi-agent-multi-gpt-pilot-a1")
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

        # Capture all messages
        for i in range(count):
            msg = msgs.nth(i)
            text = await msg.inner_text()
            print(f"  Message {i+1}: {len(text)} chars")

        if count > 0:
            last = msgs.nth(count - 1)
            last_text = await last.inner_text()
            print(f"\nLast message ({len(last_text)} chars):")

            result_file = TASK_DIR / "GPT_REVIEW_RESULT_R2.txt"
            result_file.write_text(last_text, encoding="utf-8")
            print(f"Saved to {result_file}")

            # Check if we need the previous message (it might be the full review)
            if count >= 2:
                prev = msgs.nth(count - 2)
                prev_text = await prev.inner_text()
                print(f"\nPrevious message ({len(prev_text)} chars):")
                if len(prev_text) > len(last_text):
                    print("  Previous message is longer - likely the full review")
                    result_file.write_text(prev_text, encoding="utf-8")
                    print(f"  Saved previous message to {result_file}")


asyncio.run(main())
