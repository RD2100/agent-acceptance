#!/usr/bin/env python3
"""Capture GPT R2 response via CDP."""
import asyncio
import json
import sys
from pathlib import Path

try:
    from playwright.async_api import async_playwright
except ImportError:
    print("ERROR: playwright not installed")
    sys.exit(1)

TASK_DIR = Path(r"D:\agent-acceptance\_reports\universal-agent-workflow-standard-conversation-registry-a1")
CHAT_URL_FILE = TASK_DIR / "GPT_REVIEW_CHAT_URL.txt"

async def main():
    chat_url = CHAT_URL_FILE.read_text(encoding="utf-8").strip()
    
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://localhost:9222")
        context = browser.contexts[0] if browser.contexts else await browser.new_context()
        page = context.pages[0] if context.pages else await context.new_page()
        
        current_url = page.url
        if "chatgpt.com" not in current_url or "6a26cc03" not in current_url:
            await page.goto(chat_url, wait_until="domcontentloaded", timeout=30000)
            await asyncio.sleep(3)
        
        # Check if GPT is still generating (stop button visible)
        stop_btn = page.locator('button[aria-label="Stop generating"]')
        is_generating = await stop_btn.count() > 0
        if is_generating:
            print("GPT is still generating, waiting...")
            await asyncio.sleep(30)
        
        # Get the last assistant message
        messages = page.locator('[data-message-author-role="assistant"]')
        count = await messages.count()
        print(f"Found {count} assistant messages")
        
        if count == 0:
            print("ERROR: No assistant messages found")
            await browser.close()
            sys.exit(1)
        
        last_msg = messages.nth(count - 1)
        text = await last_msg.inner_text()
        
        print(f"Captured {len(text)} chars from last assistant message")
        
        # Save the captured response
        result_file = TASK_DIR / "GPT_REVIEW_RESULT_R2.txt"
        result_file.write_text(text, encoding="utf-8")
        print(f"Saved to {result_file}")
        
        # Check if response contains overall_judgment or verdict
        has_verdict = "overall_judgment" in text.lower() or "verdict" in text.lower()
        has_end_marker = "AWSP_END_MARKER" in text
        
        status = {
            "captured": True,
            "message_count": count,
            "text_length": len(text),
            "has_verdict_keyword": has_verdict,
            "has_end_marker": has_end_marker,
            "round": "R2"
        }
        print(f"Status: {json.dumps(status, indent=2)}")
        
        await browser.close()

asyncio.run(main())
