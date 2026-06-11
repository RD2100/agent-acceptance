"""R18 Evidence Pack ZIP Submission via CDP."""
import asyncio, pyperclip, os
from playwright.async_api import async_playwright

os.chdir("D:/agent-acceptance")

CONVERSATION_FRAGMENT = "6a297f76"
CDP_URL = "http://localhost:9222"
ZIP_PATH = os.path.abspath("_evidence/EVIDENCE_PACK_R18.zip")
REPLY_PATH = "_evidence/R18-catchup-commits/gpt_reply_r3.txt"
WAIT_SECONDS = 150

SUBMISSION_MSG = """## R18 Third Submission — v3 Evidence Pack (All 5 Remaining Blockers Fixed)

This submission addresses the 5 remaining blockers from the R18 second review (PARTIAL_ACCEPTANCE_WITH_REMAINING_BLOCKERS).

### Blocker Fixes:

**R18-BLOCKING-03 (FIXED)**: Per-commit SADP audit now includes actual write_set pattern count and file counts from git at each commit time.

**R18-BLOCKING-04 (FIXED)**: ai_guard replay now checks all 3,634 committed files against the write_set. Result: 3,634 files checked, 0 scope violations, 0 deny-path violations.

**R18-BLOCKING-06 (FIXED)**: Deferred files register fully reconciled with git-status-after. 26 untracked entries = 17 NEG-009 + 1 gate_0 + 7 session artifacts + 1 NUL. Secret scan covers ALL untracked paths.

**R18-BLOCKING-07 (FIXED)**: git-status-after.txt contains accurate porcelain output matching the deferred register exactly.

**R18-NEW-BLOCKING-08 (FIXED)**: governance-decision-record.yaml provides explicit human/governance authorization for bulk write_set expansion, protected file risk acceptance, and task_id mismatch acknowledgment.

### ZIP Contents (31 files, 79 KB):
See attached EVIDENCE_PACK_R18.zip v3.

Please review and update the verdict. END_OF_GPT_RESPONSE"""

async def main():
    print(f"[R18-ZIP] ZIP file: {ZIP_PATH}")
    print(f"[R18-ZIP] ZIP size: {os.path.getsize(ZIP_PATH):,} bytes")

    pyperclip.copy(SUBMISSION_MSG)
    print("[R18-ZIP] Submission message copied to clipboard")

    async with async_playwright() as pw:
        print(f"[R18-ZIP] Connecting to {CDP_URL}...")
        browser = await pw.chromium.connect_over_cdp(CDP_URL)
        print(f"[R18-ZIP] Connected. Contexts: {len(browser.contexts)}")

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
            print(f"[R18-ZIP] ERROR: No page with '{CONVERSATION_FRAGMENT}' found")
            for ctx in browser.contexts:
                for pg in ctx.pages:
                    print(f"  Available: {pg.url}")
            return

        print(f"[R18-ZIP] Target: {page.url}")
        await page.bring_to_front()
        await asyncio.sleep(1)

        # Dismiss modals
        await page.keyboard.press("Escape")
        await asyncio.sleep(0.5)
        await page.keyboard.press("Escape")
        await asyncio.sleep(0.5)

        # === Step 1: Upload ZIP file ===
        print("[R18-ZIP] Uploading ZIP file...")
        try:
            # Method 1: Find file input element (ChatGPT uses hidden input)
            file_input = page.locator('input[type="file"]')
            input_count = await file_input.count()
            if input_count > 0:
                print(f"[R18-ZIP] Found {input_count} file input(s)")
                await file_input.first.set_input_files(ZIP_PATH)
                print("[R18-ZIP] File set via input element")
                await asyncio.sleep(3)
            else:
                print("[R18-ZIP] No file input found, trying button approach...")
                # Try clicking the attachment/paperclip button
                attach_btn = page.locator('button[aria-label*="Attach"], button[aria-label*="attach"], button[aria-label*="file"], button[data-testid*="attach"]')
                btn_count = await attach_btn.count()
                if btn_count > 0:
                    await attach_btn.first.click()
                    await asyncio.sleep(1)
                    file_input = page.locator('input[type="file"]')
                    input_count = await file_input.count()
                    if input_count > 0:
                        await file_input.first.set_input_files(ZIP_PATH)
                        print("[R18-ZIP] File set after clicking attach button")
                        await asyncio.sleep(3)
                    else:
                        print("[R18-ZIP] WARNING: Could not find file input after clicking attach")
                else:
                    print("[R18-ZIP] WARNING: No attach button or file input found")
        except Exception as e:
            print(f"[R18-ZIP] File upload error: {e}")

        # === Step 2: Paste message ===
        print("[R18-ZIP] Pasting submission message...")
        editor = page.locator('div[contenteditable="true"].ProseMirror')
        editor_count = await editor.count()
        if editor_count == 0:
            editor = page.locator('#prompt-textarea')
            editor_count = await editor.count()

        if editor_count > 0:
            await editor.first.click()
            await asyncio.sleep(0.5)
            await page.keyboard.press("Control+v")
            await asyncio.sleep(2)
        else:
            print("[R18-ZIP] ERROR: No editor found")
            return

        # === Step 3: Submit ===
        print("[R18-ZIP] Submitting...")
        await page.keyboard.press("Control+Enter")
        print(f"[R18-ZIP] Submitted. Waiting {WAIT_SECONDS}s for reply...")

        # === Step 4: Wait and capture reply ===
        await asyncio.sleep(WAIT_SECONDS)

        try:
            reply_elements = page.locator('div[data-message-author-role="assistant"]')
            count = await reply_elements.count()
            if count > 0:
                reply = await reply_elements.nth(count - 1).inner_text()
                print(f"[R18-ZIP] Captured reply: {len(reply)} chars")
                print(f"[R18-ZIP] Preview: {reply[:500]}")

                os.makedirs(os.path.dirname(REPLY_PATH), exist_ok=True)
                with open(REPLY_PATH, "w", encoding="utf-8") as f:
                    f.write(reply)
                print(f"[R18-ZIP] Reply saved to {REPLY_PATH}")

                # Extract verdict
                verdict = "unknown"
                for line in reply.split("\n"):
                    low = line.lower()
                    if "accepted_with_limitation" in low or "accepted with limitation" in low:
                        verdict = "ACCEPTED_WITH_LIMITATION"; break
                    elif "accepted" in low and "limitation" not in low:
                        verdict = "ACCEPTED"
                    elif "needs_more_evidence" in low or "needs more evidence" in low:
                        verdict = "NEEDS_MORE_EVIDENCE"
                    elif "blocked" in low:
                        verdict = "BLOCKED"
                print(f"[R18-ZIP] Verdict: {verdict}")
            else:
                print("[R18-ZIP] No assistant reply found yet")
        except Exception as e:
            print(f"[R18-ZIP] Error capturing reply: {e}")

    print("[R18-ZIP] Done.")

asyncio.run(main())
