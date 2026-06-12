"""Capture GPT response for CONVERSATION-HEALTH-GATE-A3 R1."""
import asyncio
import sys
from pathlib import Path

from playwright.async_api import async_playwright

REPO = Path(__file__).resolve().parent
CHAT_URL = "https://chatgpt.com/c/67e5a3c8-d280-8001-a4e7-a3e1d22f4319"
VERDICT_FILE = REPO / "_evidence" / "conversation_health_gate_a3_verdict.txt"


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp(
            "http://127.0.0.1:9222",
            timeout=30000
        )
        context = browser.contexts[0] if browser.contexts else await browser.new_context()
        page = context.pages[0] if context.pages else await context.new_page()

        await page.goto(CHAT_URL, wait_until="domcontentloaded", timeout=30000)
        await asyncio.sleep(5)

        # Extract all message content
        messages = await page.query_selector_all('[data-message-author-role="assistant"]')
        print(f"Found {len(messages)} assistant messages")

        if messages:
            # Get the last assistant message (most recent response)
            last_msg = messages[-1]
            text = await last_msg.inner_text()
            print(f"Last response: {len(text)} chars")
            print("---")
            print(text[:3000])
            print("---")

            # Save verdict
            VERDICT_FILE.write_text(text, encoding="utf-8")
            print(f"Verdict saved to {VERDICT_FILE}")

            # Check for verdict keywords
            if "ACCEPTED" in text:
                print("\n>>> VERDICT: ACCEPTED <<<")
            elif "NEEDS_REVISION" in text:
                print("\n>>> VERDICT: NEEDS_REVISION <<<")
            else:
                print("\n>>> VERDICT: UNCLEAR (check manually) <<<")
        else:
            print("No assistant messages found — GPT may still be responding")
            # Try waiting longer
            await asyncio.sleep(30)
            messages = await page.query_selector_all('[data-message-author-role="assistant"]')
            if messages:
                last_msg = messages[-1]
                text = await last_msg.inner_text()
                VERDICT_FILE.write_text(text, encoding="utf-8")
                print(f"Response captured after wait: {len(text)} chars")
                print(text[:2000])
            else:
                print("Still no response. Try running capture again later.")

        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
