#!/usr/bin/env python3
"""Submit inline evidence to GPT via CDP."""
import asyncio
import json
import sys
from pathlib import Path

try:
    from playwright.async_api import async_playwright
except ImportError:
    sys.exit(1)

TASK_DIR = Path(r"D:\agent-acceptance\_reports\conversation-registry-r3-close-and-multi-agent-pilot-prep-a1")
EVIDENCE_FILE = TASK_DIR / "_inline_evidence.txt"

async def main():
    msg = EVIDENCE_FILE.read_text(encoding="utf-8")
    print(f"Evidence message: {len(msg)} chars")
    
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://localhost:9222")
        context = browser.contexts[0] if browser.contexts else await browser.new_context()
        page = context.pages[0] if context.pages else await context.new_page()
        
        # Make sure we're on the right chat page
        if "chatgpt.com" not in page.url:
            await page.goto("https://chatgpt.com/", wait_until="domcontentloaded", timeout=30000)
            await asyncio.sleep(3)
        
        # Find input area
        input_sel = '#prompt-textarea'
        try:
            await page.wait_for_selector(input_sel, timeout=10000)
        except:
            input_sel = 'textarea, [contenteditable="true"]'
            await page.wait_for_selector(input_sel, timeout=10000)
        
        await page.click(input_sel)
        await asyncio.sleep(0.5)
        await page.keyboard.press("Control+a")
        await asyncio.sleep(0.2)
        await page.keyboard.press("Backspace")
        await asyncio.sleep(0.3)
        
        # Type in chunks
        chunk_size = 400
        for i in range(0, len(msg), chunk_size):
            chunk = msg[i:i+chunk_size]
            await page.keyboard.type(chunk, delay=3)
            if i % 2000 == 0 and i > 0:
                await asyncio.sleep(0.5)
                print(f"  typed {i}/{len(msg)} chars...")
        
        print(f"Message typed ({len(msg)} chars)")
        await asyncio.sleep(2)
        
        # Submit
        print("Submitting...")
        await page.keyboard.press("Enter")
        await asyncio.sleep(5)
        print("Inline evidence submitted!")
        
        await browser.close()

asyncio.run(main())
