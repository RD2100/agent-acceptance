#!/usr/bin/env python3
"""Capture GPT R3 closure response via CDP."""
import asyncio
import json
import sys
from pathlib import Path

try:
    from playwright.async_api import async_playwright
except ImportError:
    sys.exit(1)

TASK_DIR = Path(r"D:\agent-acceptance\_reports\conversation-registry-r3-close-and-multi-agent-pilot-prep-a1")

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://localhost:9222")
        context = browser.contexts[0] if browser.contexts else await browser.new_context()
        page = context.pages[0] if context.pages else await context.new_page()
        
        # Check if still generating
        try:
            stop_btn = page.locator('button[aria-label="Stop generating"]')
            if await stop_btn.count() > 0:
                print("GPT is still generating, waiting 60s more...")
                await asyncio.sleep(60)
        except:
            pass
        
        # Get the last assistant message
        messages = page.locator('[data-message-author-role="assistant"]')
        count = await messages.count()
        print(f"Found {count} assistant messages")
        
        if count == 0:
            print("No assistant messages found. Checking page URL and content...")
            print(f"Current URL: {page.url}")
            # Try to get any text content
            body = await page.locator('main').inner_text()
            print(f"Main content length: {len(body)} chars")
            print(f"First 500 chars: {body[:500]}")
            await browser.close()
            sys.exit(1)
        
        last_msg = messages.nth(count - 1)
        text = await last_msg.inner_text()
        
        print(f"Captured {len(text)} chars from last assistant message")
        
        # Save
        result_file = TASK_DIR / "GPT_REVIEW_RESULT.txt"
        result_file.write_text(text, encoding="utf-8")
        print(f"Saved to {result_file}")
        
        has_judgment = "overall_judgment" in text.lower() or "judgment" in text.lower()
        has_end = "END_OF_GPT_RESPONSE" in text
        
        status = {
            "captured": True,
            "message_count": count,
            "text_length": len(text),
            "has_judgment": has_judgment,
            "has_end_marker": has_end
        }
        print(f"Status: {json.dumps(status, indent=2)}")
        
        await browser.close()

asyncio.run(main())
