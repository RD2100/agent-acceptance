"""Wait and capture A2 verdict - retry with longer wait."""
import asyncio
import json
import sys
from pathlib import Path
from playwright.async_api import async_playwright

sys.stdout.reconfigure(encoding='utf-8')

CHAT_URL = "https://chatgpt.com/c/6a2a8cb1-b228-83aa-addb-79bda9aba043"
OUTPUT = Path(r"D:\agent-acceptance\_evidence\conversation_health_gate_a2_verdict.txt")


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://localhost:9222")
        ctx = browser.contexts[0]

        target_page = None
        for page in ctx.pages:
            if "6a2a8cb1-b228-83aa-addb-79bda9aba043" in page.url:
                target_page = page
                break
        if not target_page:
            target_page = ctx.pages[0]

        print(f"Page: {target_page.url}")
        await target_page.wait_for_timeout(5000)

        # Wait for GPT to finish (check stop button)
        stop_btn = target_page.locator('button[aria-label="Stop generating"]')
        for i in range(90):  # 450 seconds max
            await asyncio.sleep(5)
            if await stop_btn.count() > 0 and await stop_btn.first.is_visible():
                print(f"  Still generating... {(i+1)*5}s")
                continue
            else:
                print(f"  Done generating at {(i+1)*5}s")
                break

        # Capture all assistant messages
        ams = target_page.locator('div[data-message-author-role="assistant"]')
        cnt = await ams.count()
        print(f"\nTotal assistant messages: {cnt}")

        # Get the last message
        if cnt > 0:
            last = await ams.last.inner_text()
            print(f"Last msg: {len(last)} chars")

            if len(last) < 500:
                print("\n--- Last message content ---")
                print(last)
                print("--- End ---")

                # If still too short, wait more
                print("\nWaiting additional 30s...")
                await target_page.wait_for_timeout(30000)
                ams = target_page.locator('div[data-message-author-role="assistant"]')
                cnt2 = await ams.count()
                if cnt2 > cnt:
                    last = await ams.last.inner_text()
                    print(f"New message appeared: {len(last)} chars")
                else:
                    last = await ams.last.inner_text()

            OUTPUT.write_text(last, encoding="utf-8")
            print(f"\nSaved {len(last)} chars to {OUTPUT}")
            print("\n--- First 5000 chars ---")
            print(last[:5000])
            if len(last) > 5000:
                print(f"\n... ({len(last) - 5000} more)")

            # Detect verdict
            upper = last.upper()
            for kw in ["ACCEPTED", "REJECTED", "NEEDS_REVISION"]:
                if kw in upper:
                    print(f"\n*** VERDICT: {kw} ***")
                    break


asyncio.run(main())
