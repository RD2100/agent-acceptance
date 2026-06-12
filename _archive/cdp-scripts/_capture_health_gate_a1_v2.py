"""Capture GPT verdict for CONVERSATION-HEALTH-GATE-A1 — v2 with encoding fix."""
import asyncio
import sys
from pathlib import Path
from playwright.async_api import async_playwright

REPO = Path(r"D:\agent-acceptance")
CHAT_URL = "https://chatgpt.com/c/6a2a8cb1-b228-83aa-addb-79bda9aba043"
OUTPUT = REPO / "_evidence" / "conversation_health_gate_a1_verdict.txt"


async def main():
    # Force UTF-8 output
    sys.stdout.reconfigure(encoding='utf-8')

    print("=== Capture GPT Verdict v2: CONVERSATION-HEALTH-GATE-A1 ===")

    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://localhost:9222")
        context = browser.contexts[0]
        page = context.pages[0]

        print(f"[1] Current URL: {page.url}")
        if "6a2a8cb1" not in page.url:
            print("    Navigating to conversation...")
            await page.goto(CHAT_URL, wait_until="networkidle", timeout=30000)
            await asyncio.sleep(3)

        # Check if GPT is still generating
        stop_btn = page.locator('button[aria-label="Stop generating"]')
        is_generating = await stop_btn.is_visible()
        print(f"[2] GPT still generating: {is_generating}")

        if is_generating:
            print("    Waiting for generation to complete...")
            # Wait up to 90 seconds for generation to stop
            for i in range(18):
                await asyncio.sleep(5)
                is_gen = await stop_btn.is_visible()
                if not is_gen:
                    print(f"    Generation complete after {(i+1)*5}s")
                    break
                print(f"    Still generating... {(i+1)*5}s")
            await asyncio.sleep(3)

        # Scroll to bottom
        print("[3] Scrolling to bottom...")
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await asyncio.sleep(2)

        # Extract all messages
        responses = await page.locator('[data-message-author-role="assistant"]').all()
        print(f"[4] Found {len(responses)} assistant messages")

        if not responses:
            print("    ERROR: No assistant messages found!")
            # Try alternative selector
            responses = await page.locator('.markdown').all()
            print(f"    Alternative: found {len(responses)} .markdown elements")

        last_response = responses[-1]

        # Get text content — use text_content() which handles encoding properly
        text = await last_response.text_content()
        if not text:
            text = await last_response.inner_text()

        print(f"    Text length: {len(text)} chars")

        # Save verdict with UTF-8 encoding
        verdict_text = f"""CONVERSATION-HEALTH-GATE-A1 VERDICT
Captured: {len(text)} chars
URL: {page.url}
---
{text}
"""
        OUTPUT.write_text(verdict_text, encoding="utf-8")
        print(f"\n[5] Verdict saved to: {OUTPUT}")

        # Print first 1000 chars for preview
        print(f"\n=== VERDICT PREVIEW (first 1000 chars) ===")
        print(text[:1000])
        if len(text) > 1000:
            print(f"\n... ({len(text) - 1000} more chars)")

        # Check for verdict keywords
        text_upper = text.upper()
        for kw in ["ACCEPTED", "REJECTED", "NEEDS_REVISION", "NEEDS REVISION"]:
            if kw in text_upper:
                print(f"\n*** VERDICT KEYWORD FOUND: {kw} ***")
                break


if __name__ == "__main__":
    asyncio.run(main())
