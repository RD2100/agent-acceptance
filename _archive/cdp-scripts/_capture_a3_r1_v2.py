"""Capture GPT response for A3 R1 — use after submit."""
import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

REPO = Path(__file__).resolve().parent
TARGET_URL = "https://chatgpt.com/c/6a2a8cb1-b228-83aa-addb-79bda9aba043"
VERDICT_FILE = REPO / "_evidence" / "conversation_health_gate_a3_verdict.txt"


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://localhost:9222")
        ctx = browser.contexts[0]

        target = None
        for pg in ctx.pages:
            if "6a2a8cb1" in pg.url:
                target = pg
                break
        if not target:
            target = ctx.pages[0]
            await target.goto(TARGET_URL, wait_until="networkidle", timeout=30000)
            await target.wait_for_timeout(5000)

        # Check if still generating
        stop_btn = target.locator('button[data-testid="stop-button"]')
        if await stop_btn.count() > 0 and await stop_btn.first.is_visible():
            print("GPT still generating, waiting (60s)...")
            await target.wait_for_timeout(60000)

        # Get all assistant messages
        ams = target.locator('div[data-message-author-role="assistant"]')
        cnt = await ams.count()
        print(f"Assistant messages: {cnt}")

        if cnt > 0:
            # Get the last message
            reply = await ams.last.inner_text()
            print(f"Last reply: {len(reply)} chars")
            print("---")
            # Write to file with utf-8 encoding
            VERDICT_FILE.write_text(reply, encoding="utf-8")
            print(f"Saved to {VERDICT_FILE}")
            print("---FULL TEXT---")
            print(reply)
        else:
            print("No assistant messages found")


asyncio.run(main())
