"""Submit A3 R1 to GPT — v2 with debugging."""
import asyncio
import json
import sys
from pathlib import Path

from playwright.async_api import async_playwright

REPO = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO))
from _cdp_submit_helper import run_pre_gpt_gate

CHAT_URL = "https://chatgpt.com/c/67e5a3c8-d280-8001-a4e7-a3e1d22f4319"
PROMPT_FILE = REPO / "_evidence" / "CONVERSATION-HEALTH-GATE-A3" / "gpt-review-prompt.md"


async def main():
    exit_code, decision, message = run_pre_gpt_gate(allow_init=True)
    if exit_code != 0:
        print(f"BLOCKED (exit {exit_code}): {message}")
        return

    prompt = PROMPT_FILE.read_text(encoding="utf-8")
    print(f"Prompt length: {len(prompt)} chars")

    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9222", timeout=30000)
        context = browser.contexts[0]
        page = context.pages[0] if context.pages else await context.new_page()

        print(f"Navigating to {CHAT_URL}")
        await page.goto(CHAT_URL, wait_until="networkidle", timeout=30000)
        await asyncio.sleep(5)

        # Debug: check page state
        url = page.url
        title = await page.title()
        print(f"Current URL: {url}")
        print(f"Page title: {title}")

        # Check for textarea
        textarea = page.locator("#prompt-textarea")
        is_visible = await textarea.is_visible()
        print(f"Textarea visible: {is_visible}")

        if not is_visible:
            # Try waiting
            await textarea.wait_for(state="visible", timeout=10000)
            is_visible = await textarea.is_visible()
            print(f"Textarea visible after wait: {is_visible}")

        # Focus and paste
        await textarea.click()
        await asyncio.sleep(0.5)

        # Use JS to set clipboard and paste
        escaped = json.dumps(prompt)
        await page.evaluate(f"navigator.clipboard.writeText({escaped})")
        await asyncio.sleep(0.5)
        await page.keyboard.press("Control+v")
        await asyncio.sleep(2)

        # Check textarea content
        content = await textarea.input_value()
        print(f"Textarea content length: {len(content)}")
        if len(content) > 100:
            print(f"First 100 chars: {content[:100]}")

        # Click send button
        send_btn = page.locator('button[data-testid="send-button"]')
        btn_visible = await send_btn.is_visible()
        print(f"Send button visible: {btn_visible}")

        if btn_visible:
            await send_btn.click()
            print("Clicked send button")
        else:
            # Try Enter
            await page.keyboard.press("Enter")
            print("Pressed Enter")

        # Wait for response
        print("Waiting for GPT response (60s)...")
        await asyncio.sleep(60)

        # Check for response
        assistant_msgs = await page.query_selector_all('[data-message-author-role="assistant"]')
        print(f"Assistant messages found: {len(assistant_msgs)}")

        if assistant_msgs:
            last = assistant_msgs[-1]
            text = await last.inner_text()
            print(f"Last response: {len(text)} chars")
            verdict_path = REPO / "_evidence" / "conversation_health_gate_a3_verdict.txt"
            verdict_path.write_text(text, encoding="utf-8")
            print(f"Verdict saved to {verdict_path}")
            if "ACCEPTED" in text:
                print(">>> VERDICT: ACCEPTED <<<")
            elif "NEEDS_REVISION" in text:
                print(">>> VERDICT: NEEDS_REVISION <<<")
            print("---FIRST 2000 CHARS---")
            print(text[:2000])
        else:
            # Try alternative selector
            all_divs = await page.query_selector_all('[class*="markdown"]')
            print(f"Markdown divs found: {len(all_divs)}")
            
            # Save screenshot for debugging
            await page.screenshot(path=str(REPO / "_evidence" / "a3_r1_debug.png"))
            print("Debug screenshot saved")

        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
