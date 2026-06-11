"""R18 Evidence Submission via CDP — Catch-up Commit Batch Review."""
import asyncio, pyperclip, os, time
from playwright.async_api import async_playwright

os.chdir("D:/agent-acceptance")

CONVERSATION_ID = "6a297f76-3e7c-83a5-a0e5-b4413d923c7e"
CONVERSATION_FRAGMENT = "6a297f76"
CDP_URL = "http://localhost:9222"
EVIDENCE_PATH = "_evidence/R18-catchup-commits/submission_text.txt"
REPLY_PATH = "_evidence/R18-catchup-commits/gpt_reply.txt"
WAIT_SECONDS = 120

async def main():
    # Load submission text
    with open(EVIDENCE_PATH, encoding="utf-8") as f:
        msg = f.read().strip()
    print(f"[R18] Loaded submission text: {len(msg)} chars")

    # Copy to clipboard
    pyperclip.copy(msg)
    print("[R18] Copied to clipboard")

    # Connect to Chrome via CDP
    async with async_playwright() as pw:
        print(f"[R18] Connecting to {CDP_URL}...")
        browser = await pw.chromium.connect_over_cdp(CDP_URL)
        print(f"[R18] Connected. Contexts: {len(browser.contexts)}")

        # Find target page
        page = None
        for ctx in browser.contexts:
            for pg in ctx.pages:
                if CONVERSATION_FRAGMENT in pg.url:
                    page = pg
                    break
            if page:
                break

        if not page:
            print(f"[R18] ERROR: No page found with '{CONVERSATION_FRAGMENT}' in URL.")
            print("[R18] Available pages:")
            for ctx in browser.contexts:
                for pg in ctx.pages:
                    print(f"  - {pg.url}")
            return

        print(f"[R18] Found target page: {page.url}")

        # Ensure the page is focused
        await page.bring_to_front()
        await asyncio.sleep(1)

        # Dismiss any modals
        await page.keyboard.press("Escape")
        await asyncio.sleep(0.5)
        await page.keyboard.press("Escape")
        await asyncio.sleep(0.5)

        # Find the editor
        editor = page.locator('div[contenteditable="true"].ProseMirror')
        editor_count = await editor.count()
        if editor_count == 0:
            print("[R18] ERROR: No ProseMirror editor found. Trying alternative...")
            editor = page.locator('#prompt-textarea')
            editor_count = await editor.count()
            if editor_count == 0:
                print("[R18] ERROR: No editor found on page.")
                return

        print(f"[R18] Found editor (count={editor_count})")
        await editor.first.click()
        await asyncio.sleep(0.5)

        # Paste content
        print("[R18] Pasting content...")
        await page.keyboard.press("Control+v")
        await asyncio.sleep(3)

        # Submit
        print("[R18] Submitting message...")
        await page.keyboard.press("Control+Enter")
        print(f"[R18] Message submitted. Waiting {WAIT_SECONDS}s for GPT reply...")

        # Wait for reply
        await asyncio.sleep(WAIT_SECONDS)

        # Capture reply
        try:
            reply_elements = page.locator('div[data-message-author-role="assistant"]')
            count = await reply_elements.count()
            if count > 0:
                reply = await reply_elements.nth(count - 1).inner_text()
                print(f"[R18] Captured GPT reply: {len(reply)} chars")
                print(f"[R18] Reply preview: {reply[:300]}...")

                # Save reply
                os.makedirs(os.path.dirname(REPLY_PATH), exist_ok=True)
                with open(REPLY_PATH, "w", encoding="utf-8") as f:
                    f.write(reply)
                print(f"[R18] Reply saved to {REPLY_PATH}")

                # Extract verdict
                verdict = "unknown"
                for line in reply.split("\n"):
                    low = line.lower()
                    if "accepted" in low and "limitation" in low:
                        verdict = "ACCEPTED_WITH_LIMITATION"
                    elif "accepted" in low:
                        verdict = "ACCEPTED"
                    elif "blocked" in low:
                        verdict = "BLOCKED"
                    elif "pass" in low:
                        verdict = "PASS"
                print(f"[R18] Verdict: {verdict}")
            else:
                print("[R18] WARNING: No assistant reply found yet.")
        except Exception as e:
            print(f"[R18] Error capturing reply: {e}")

    print("[R18] Done.")

asyncio.run(main())
