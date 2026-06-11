#!/usr/bin/env python3
"""Submit CONVERSATION-REGISTRY-A1 R2 review to GPT via CDP."""
import asyncio
import json
import sys
from pathlib import Path

try:
    from playwright.async_api import async_playwright
except ImportError:
    print("ERROR: playwright not installed. Run: pip install playwright")
    sys.exit(1)

TASK_DIR = Path(r"D:\agent-acceptance\_reports\universal-agent-workflow-standard-conversation-registry-a1")
PROMPT_FILE = TASK_DIR / "GPT_REVIEW_PROMPT_R2.md"
CHAT_URL_FILE = TASK_DIR / "GPT_REVIEW_CHAT_URL.txt"

async def main():
    prompt = PROMPT_FILE.read_text(encoding="utf-8")
    
    # Get chat URL
    if CHAT_URL_FILE.exists():
        chat_url = CHAT_URL_FILE.read_text(encoding="utf-8").strip()
        print(f"Using existing chat URL: {chat_url}")
    else:
        print("ERROR: No chat URL file found. Cannot submit.")
        sys.exit(1)
    
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://localhost:9222")
        context = browser.contexts[0] if browser.contexts else await browser.new_context()
        page = context.pages[0] if context.pages else await context.new_page()
        
        # Navigate to the chat
        await page.goto(chat_url, wait_until="domcontentloaded", timeout=30000)
        await asyncio.sleep(3)
        
        # Find the input area and type the prompt
        print("Typing R2 review prompt...")
        
        # Use the contenteditable div or textarea
        input_sel = '#prompt-textarea'
        try:
            await page.wait_for_selector(input_sel, timeout=10000)
        except:
            input_sel = 'textarea'
            await page.wait_for_selector(input_sel, timeout=10000)
        
        # Clear and type
        await page.click(input_sel)
        await asyncio.sleep(0.5)
        
        # Select all and delete
        await page.keyboard.press("Control+a")
        await asyncio.sleep(0.2)
        await page.keyboard.press("Backspace")
        await asyncio.sleep(0.3)
        
        # Type the prompt in chunks to avoid input buffer issues
        chunk_size = 500
        for i in range(0, len(prompt), chunk_size):
            chunk = prompt[i:i+chunk_size]
            await page.keyboard.type(chunk, delay=5)
            await asyncio.sleep(0.1)
        
        print(f"Prompt typed ({len(prompt)} chars)")
        await asyncio.sleep(1)
        
        # Press Enter to submit
        print("Submitting...")
        await page.keyboard.press("Enter")
        
        # Wait for response to start generating
        await asyncio.sleep(5)
        print("R2 review prompt submitted to GPT!")
        
        # Save submission status
        status = {
            "submitted": True,
            "chat_url": chat_url,
            "prompt_length": len(prompt),
            "method": "playwright_cdp",
            "round": "R2"
        }
        status_file = TASK_DIR / "GPT_REVIEW_SUBMISSION_STATUS_R2.json"
        status_file.write_text(json.dumps(status, indent=2), encoding="utf-8")
        print(f"Status saved to {status_file}")
        
        await browser.close()

asyncio.run(main())
