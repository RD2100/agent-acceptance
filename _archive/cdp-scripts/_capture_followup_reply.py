"""Capture the NEW GPT reply for R18 follow-up submission."""
import asyncio, os
from playwright.async_api import async_playwright

os.chdir("D:/agent-acceptance")
REPLY_PATH = "_evidence/R18-followup-cleanup/gpt_reply_followup.txt"

async def main():
    async with async_playwright() as pw:
        browser = await pw.chromium.connect_over_cdp("http://localhost:9222")
        page = None
        for ctx in browser.contexts:
            for pg in ctx.pages:
                if "6a297f76" in pg.url:
                    page = pg; break
            if page: break

        if not page:
            print("ERROR: page not found"); return

        await page.bring_to_front()

        # Count current assistant messages
        replies = page.locator('div[data-message-author-role="assistant"]')
        current_count = await replies.count()
        print(f"Current assistant messages: {current_count}")

        # Check last message to see if our follow-up was received
        if current_count > 0:
            last = await replies.nth(current_count - 1).inner_text()
            print(f"Last reply preview: {last[:100]}...")

        # Wait for a NEW reply (count increases)
        print("Waiting for new reply (polling every 15s, max 180s)...")
        for attempt in range(12):
            await asyncio.sleep(15)
            new_count = await replies.count()
            if new_count > current_count:
                reply = await replies.nth(new_count - 1).inner_text()
                print(f"\nNew reply captured ({len(reply)} chars):")
                print(reply[:600])
                with open(REPLY_PATH, "w", encoding="utf-8") as f:
                    f.write(reply)
                print(f"\nSaved to {REPLY_PATH}")
                return
            # Check if GPT is still generating
            stop_btn = page.locator('button[aria-label="Stop generating"], button[aria-label="Stop"]')
            if await stop_btn.count() > 0:
                print(f"  Attempt {attempt+1}: GPT still generating...")
            else:
                print(f"  Attempt {attempt+1}: no new reply yet")

        print("Timeout: no new reply captured")

asyncio.run(main())
