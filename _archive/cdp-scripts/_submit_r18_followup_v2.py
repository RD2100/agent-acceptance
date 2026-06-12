"""Robust CDP submit for R18 follow-up — uses button click instead of Ctrl+Enter."""
import asyncio, pyperclip, os
from playwright.async_api import async_playwright

os.chdir("D:/agent-acceptance")

ZIP_PATH = os.path.abspath("_evidence/EVIDENCE_PACK_R18_FOLLOWUP.zip")
REPLY_PATH = "_evidence/R18-followup-cleanup/gpt_reply_followup.txt"

MSG = """## R18 Follow-Up Submission — SADP Closed Loop Complete

Commit: bc974d2f (238 files, SADP hook PASSED)

All 4 GPT R18 v3 follow-up items resolved:
1. Cleanup: 7 session artifacts committed, 15 NEG-009 remain deferred (deny_paths)
2. gate_0 repair: handoff-pipeline-refactor-a1.yaml now has valid inventory_evidence
3. NEG-009 denied: confirmed, 15 files still on deny_paths
4. Dedicated TaskSpec: R18-FOLLOWUP-CLEANUP-A1 created

Additional: project-beta removed (186 deletions), dev-frame-writing added (11th project), router stress test updated.

SADP evidence: 1038 tests passed, 0 scope violations, reviewer PASS, finalizer done.
ZIP attached with full evidence chain.

Please review. END_OF_GPT_RESPONSE"""

async def main():
    pyperclip.copy(MSG)
    print(f"[SUBMIT] Message ready ({len(MSG)} chars)")
    print(f"[SUBMIT] ZIP: {ZIP_PATH} ({os.path.getsize(ZIP_PATH):,} bytes)")

    async with async_playwright() as pw:
        browser = await pw.chromium.connect_over_cdp("http://localhost:9222")
        page = None
        for ctx in browser.contexts:
            for pg in ctx.pages:
                if "6a297f76" in pg.url:
                    page = pg; break
            if page: break

        if not page:
            print("[SUBMIT] ERROR: page not found"); return

        await page.bring_to_front()
        await asyncio.sleep(2)

        # Count current messages
        user_msgs = page.locator('div[data-message-author-role="user"]')
        pre_count = await user_msgs.count()
        print(f"[SUBMIT] Current user messages: {pre_count}")

        # Dismiss any overlays
        for _ in range(3):
            await page.keyboard.press("Escape")
            await asyncio.sleep(0.3)

        # Upload ZIP via file input
        print("[SUBMIT] Uploading ZIP...")
        file_inputs = page.locator('input[type="file"]')
        fi_count = await file_inputs.count()
        print(f"[SUBMIT] File inputs found: {fi_count}")
        if fi_count > 0:
            await file_inputs.first.set_input_files(ZIP_PATH)
            await asyncio.sleep(5)  # Wait for upload to complete
            print("[SUBMIT] ZIP uploaded")

        # Click on editor to focus
        editor = page.locator('div[contenteditable="true"].ProseMirror')
        ed_count = await editor.count()
        if ed_count == 0:
            editor = page.locator('#prompt-textarea')
            ed_count = await editor.count()

        print(f"[SUBMIT] Editor found: {ed_count}")
        if ed_count > 0:
            await editor.first.click()
            await asyncio.sleep(1)

            # Clear any existing content
            await page.keyboard.press("Control+a")
            await asyncio.sleep(0.3)
            await page.keyboard.press("Delete")
            await asyncio.sleep(0.3)

            # Paste
            await page.keyboard.press("Control+v")
            await asyncio.sleep(3)
            print("[SUBMIT] Message pasted")

            # Find and click send button
            send_btn = page.locator('button[data-testid="send-button"], button[aria-label="Send"], button[aria-label="Send message"]')
            btn_count = await send_btn.count()
            print(f"[SUBMIT] Send buttons found: {btn_count}")

            if btn_count > 0:
                await send_btn.first.click()
                print("[SUBMIT] Clicked send button")
            else:
                # Try Ctrl+Enter as fallback
                await page.keyboard.press("Control+Enter")
                print("[SUBMIT] Used Ctrl+Enter fallback")

            await asyncio.sleep(5)

            # Verify message was sent
            new_count = await user_msgs.count()
            if new_count > pre_count:
                print(f"[SUBMIT] Message sent! User messages: {pre_count} -> {new_count}")
            else:
                print(f"[SUBMIT] WARNING: Message may not have been sent. Count still: {new_count}")
                # Try Enter as last resort
                await editor.first.click()
                await asyncio.sleep(0.5)
                await page.keyboard.press("Enter")
                await asyncio.sleep(3)
                new_count2 = await user_msgs.count()
                print(f"[SUBMIT] After Enter: {new_count2} user messages")

        # Wait for GPT reply
        print("[SUBMIT] Waiting 150s for GPT reply...")
        await asyncio.sleep(150)

        # Capture reply
        replies = page.locator('div[data-message-author-role="assistant"]')
        count = await replies.count()
        if count > 0:
            reply = await replies.nth(count - 1).inner_text()
            print(f"[SUBMIT] Reply captured: {len(reply)} chars")
            print(f"[SUBMIT] Preview: {reply[:500]}")

            os.makedirs(os.path.dirname(REPLY_PATH), exist_ok=True)
            with open(REPLY_PATH, "w", encoding="utf-8") as f:
                f.write(reply)
            print(f"[SUBMIT] Saved to {REPLY_PATH}")
        else:
            print("[SUBMIT] No reply found")

    print("[SUBMIT] Done.")

asyncio.run(main())
