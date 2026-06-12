"""Capture GPT verdict for CONVERSATION-HEALTH-GATE-A1."""
import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

REPO = Path(r"D:\agent-acceptance")
CHAT_URL = "https://chatgpt.com/c/6a2a8cb1-b228-83aa-addb-79bda9aba043"
OUTPUT = REPO / "_evidence" / "conversation_health_gate_a1_verdict.txt"


async def main():
    print("=== Capture GPT Verdict: CONVERSATION-HEALTH-GATE-A1 ===")

    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://localhost:9222")
        context = browser.contexts[0]
        page = context.pages[0]

        print(f"[1] Current URL: {page.url}")
        if CHAT_URL not in page.url:
            print("    Navigating to conversation...")
            await page.goto(CHAT_URL, wait_until="networkidle", timeout=30000)
            await asyncio.sleep(3)

        # Scroll to bottom to see the latest response
        print("[2] Scrolling to bottom...")
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await asyncio.sleep(2)

        # Get the last assistant message (GPT's response)
        print("[3] Extracting GPT response...")
        responses = await page.locator('[data-message-author-role="assistant"]').all()
        if not responses:
            print("    ERROR: No assistant messages found!")
            return

        last_response = responses[-1]
        text = await last_response.inner_text()
        print(f"    Captured {len(text)} chars from last assistant message")

        # Also try to get the full content including any code blocks
        try:
            full_html = await last_response.inner_html()
            print(f"    HTML length: {len(full_html)} chars")
        except Exception:
            full_html = ""

        # Save the verdict
        verdict_text = f"""CONVERSATION-HEALTH-GATE-A1 VERDICT
Captured: {len(text)} chars
URL: {page.url}
---
{text}
"""
        OUTPUT.write_text(verdict_text, encoding="utf-8")
        print(f"\n[4] Verdict saved to: {OUTPUT}")
        print(f"    Preview (first 500 chars):")
        print(text[:500])
        print("...")

        # Check if response is still generating (look for stop button)
        stop_btn = page.locator('button[aria-label="Stop generating"]')
        if await stop_btn.is_visible():
            print("\n    WARNING: GPT is still generating response!")
            print("    Consider re-running capture after more wait time.")


if __name__ == "__main__":
    asyncio.run(main())
