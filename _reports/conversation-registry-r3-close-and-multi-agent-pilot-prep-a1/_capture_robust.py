#!/usr/bin/env python3
"""Robust capture of GPT R3 response via CDP."""
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
        context = browser.contexts[0]
        page = context.pages[0]
        
        print(f"URL: {page.url}")
        
        # Check if still generating
        stop_btn = page.locator('button[aria-label="Stop generating"]')
        generating = await stop_btn.count() > 0
        if generating:
            print("GPT still generating, waiting 120s...")
            await asyncio.sleep(120)
        
        # Try multiple selectors for assistant messages
        for selector in [
            '[data-message-author-role="assistant"]',
            '.markdown',
            '[class*="markdown"]',
            'main [class*="prose"]',
        ]:
            msgs = page.locator(selector)
            count = await msgs.count()
            if count > 0:
                last = msgs.nth(count - 1)
                text = await last.inner_text()
                if len(text) > 50:
                    print(f"Captured {len(text)} chars via '{selector}'")
                    
                    result_file = TASK_DIR / "GPT_REVIEW_RESULT.txt"
                    result_file.write_text(text, encoding="utf-8")
                    print(f"Saved to {result_file}")
                    
                    has_judgment = "overall_judgment" in text.lower() or "judgment" in text.lower()
                    has_accepted = "accepted" in text.lower()
                    print(f"has_judgment={has_judgment}, has_accepted={has_accepted}")
                    print(f"First 300 chars: {text[:300]}")
                    await browser.close()
                    return
        
        # Fallback: get main content
        print("Trying fallback - main content...")
        try:
            main_text = await page.locator('main').inner_text()
            print(f"Main content: {len(main_text)} chars")
            result_file = TASK_DIR / "GPT_REVIEW_RESULT.txt"
            result_file.write_text(main_text, encoding="utf-8")
            print(f"First 500 chars: {main_text[:500]}")
        except Exception as e:
            print(f"Fallback failed: {e}")
        
        await browser.close()

asyncio.run(main())
