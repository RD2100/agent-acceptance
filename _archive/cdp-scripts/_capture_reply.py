"""Capture GPT reply from ChatGPT conversation via CDP."""
import asyncio
from playwright.async_api import async_playwright

TARGET_URL = "https://chatgpt.com/c/6a297f76-3e7c-83a5-a0e5-b4413d923c7e"
CDP_URL = "http://localhost:9222"
OUT_PATH = r"D:\agent-acceptance\_evidence\R18-WORKSPACE-CLEANUP-FINAL\gpt_reply_final4.txt"

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp(CDP_URL)
        ctx = browser.contexts[0]

        target_page = None
        for page in ctx.pages:
            if "6a297f76-3e7c-83a5-a0e5-b4413d923c7e" in page.url:
                target_page = page
                break

        if not target_page:
            print("ERROR: Target page not found.")
            return

        print(f"Page: {target_page.url}")
        await target_page.wait_for_timeout(3000)

        # Scroll to bottom to ensure latest messages are loaded
        await target_page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await target_page.wait_for_timeout(2000)

        # Count messages
        user_msgs = await target_page.locator('div[data-message-author-role="user"]').count()
        assistant_msgs = await target_page.locator('div[data-message-author-role="assistant"]').count()
        print(f"User messages: {user_msgs}, Assistant messages: {assistant_msgs}")

        if assistant_msgs > 0:
            last_reply = await target_page.locator('div[data-message-author-role="assistant"]').last.inner_text()
            print(f"\n=== GPT REPLY ({len(last_reply)} chars) ===")
            print(last_reply[:8000])

            with open(OUT_PATH, "w", encoding="utf-8") as f:
                f.write(last_reply)
            print(f"\nSaved to {OUT_PATH}")
        else:
            print("No assistant messages found.")

asyncio.run(main())
