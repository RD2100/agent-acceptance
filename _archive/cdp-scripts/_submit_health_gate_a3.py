"""Submit CONVERSATION-HEALTH-GATE-A3 R1 to GPT for review."""
import asyncio
import json
import sys
from pathlib import Path

from playwright.async_api import async_playwright

REPO = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO))
from _cdp_submit_helper import paste_and_send, run_pre_gpt_gate

CHAT_URL = "https://chatgpt.com/c/67e5a3c8-d280-8001-a4e7-a3e1d22f4319"
PROMPT_FILE = REPO / "_evidence" / "CONVERSATION-HEALTH-GATE-A3" / "gpt-review-prompt.md"


async def main():
    # Pre-gate check
    exit_code, decision, message = run_pre_gpt_gate(allow_init=True)
    if exit_code != 0:
        print(f"PRE-GPT GATE BLOCKED (exit {exit_code}): {message}")
        return

    print("Pre-GPT gate: OK — proceeding with CDP submission")

    prompt_text = PROMPT_FILE.read_text(encoding="utf-8")
    print(f"Prompt: {len(prompt_text)} chars")

    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp(
            "http://127.0.0.1:9222",
            timeout=30000
        )
        context = browser.contexts[0] if browser.contexts else await browser.new_context()
        page = context.pages[0] if context.pages else await context.new_page()

        # Navigate to chat
        await page.goto(CHAT_URL, wait_until="domcontentloaded", timeout=30000)
        await asyncio.sleep(5)

        # Check page loaded
        title = await page.title()
        print(f"Page title: {title}")

        # Submit
        await paste_and_send(page, prompt_text)

        # Wait for response to start
        print("Message sent. Waiting for GPT response...")
        await asyncio.sleep(15)

        # Save page state for capture script
        content = await page.content()
        (REPO / "_evidence" / "a3_r1_page_after_send.html").write_text(
            content[:50000], encoding="utf-8"
        )
        print("Page state saved. Use capture script to get GPT response.")

        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
