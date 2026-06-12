"""Submit R18 Workspace Closure SLIM ZIP to ChatGPT via CDP."""
import asyncio
from playwright.async_api import async_playwright

ZIP_PATH = r"D:\agent-acceptance\_evidence\EVIDENCE_PACK_R18_WORKSPACE_CLOSURE_SLIM.zip"
TARGET_URL = "https://chatgpt.com/c/6a297f76-3e7c-83a5-a0e5-b4413d923c7e"
CDP_URL = "http://localhost:9222"

SUBMISSION_MSG = """R18 Workspace Closure — SLIM Evidence Pack (addresses all 3 blockers)

EVIDENCE_PACK_R18_WORKSPACE_CLOSURE_SLIM.zip (24 files, 23 KB)
SHA256: 7622fa21ed695580e7a4ecebadcfc2e395b771df2e0316f3a512856f2d6602a6

This supersedes all previous evidence packs. All evidence regenerated from scratch in a single script pass to guarantee internal consistency.

=== BLOCKER RESOLUTION ===

BLOCKING-01 (register mismatch): FIXED
- git-status-after.txt: modified_tracked=0, untracked=28
- deferred-files-register.yaml: 17 NEG-009 + 3 secret-scan + 8 session artifacts = 28
- safety-report.json: matches exactly
- review.yaml: matches exactly  
- final-report.md: matches exactly
- All 5 files report identical numbers

BLOCKING-02 (6022c187 not evidenced): FIXED
- git-show-6022c187.txt: included
- diff-stat-6022c187.txt: included

BLOCKING-03 (modified tracked files): FIXED
- .agent/PROJECT_REGISTRY.json was reverted via git checkout (external process had modified it from 11 to 3 projects)
- Currently 0 modified tracked files confirmed
- Register documents the external modification pattern

=== COMMITS IN SCOPE ===
104ac8b1: registry reconciliation, session scripts, NUL removal
f06ce965: closure evidence, deferred register
6022c187: updated evidence with raw audit files
caa85c28: FINAL rebuilt evidence pack

=== POST-COMMIT STATE ===
- Modified tracked: 0
- Untracked: 28 (17 NEG-009 + 3 secret-scan + 8 session artifacts)
- Tests: 1038 passed, 0 failed
- All untracked files accounted for in register"""

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
            print("ERROR: Target page not found. Opening...")
            page = ctx.pages[0] if ctx.pages else await ctx.new_page()
            await page.goto(TARGET_URL, wait_until="networkidle", timeout=30000)
            target_page = page

        print(f"Page: {target_page.url}")
        await target_page.wait_for_timeout(3000)

        user_msgs_before = await target_page.locator('div[data-message-author-role="user"]').count()
        print(f"User messages before: {user_msgs_before}")

        # Upload ZIP
        print("Uploading ZIP...")
        file_input = target_page.locator('#upload-files')
        await file_input.set_input_files(ZIP_PATH)
        await target_page.wait_for_timeout(3000)
        print("File uploaded.")

        # Dismiss any duplicate file modal
        modal = target_page.locator('#modal-duplicate-file')
        if await modal.count() > 0 and await modal.is_visible():
            print("Duplicate file modal detected, confirming...")
            btn = modal.locator('button.btn-primary')
            if await btn.count() > 0:
                await btn.first.click(force=True)
            else:
                buttons = modal.locator('button')
                cnt = await buttons.count()
                if cnt > 0:
                    await buttons.last.click(force=True)
            await target_page.wait_for_timeout(2000)

        # Type message
        print("Typing message...")
        editor = target_page.locator('#prompt-textarea')
        if await editor.count() == 0:
            editor = target_page.locator('div[contenteditable="true"]').last
        await editor.click()
        await target_page.wait_for_timeout(500)

        # Use clipboard paste
        await target_page.evaluate(f"""
            async () => {{
                const text = {repr(SUBMISSION_MSG)};
                await navigator.clipboard.writeText(text);
            }}
        """)
        await target_page.wait_for_timeout(500)
        await editor.press("Control+v")
        await target_page.wait_for_timeout(2000)

        # Send
        print("Sending...")
        send_btn = target_page.locator('button[data-testid="send-button"]')
        if await send_btn.count() > 0:
            disabled = await send_btn.first.get_attribute("disabled")
            print(f"Send button disabled: {disabled}")
            if disabled is None:
                await send_btn.first.click()
                print("Clicked send.")
            else:
                # Try focusing editor and pressing Enter
                await editor.press("Enter")
                print("Pressed Enter.")
                await target_page.wait_for_timeout(2000)
                # If still not sent, force click
                disabled2 = await send_btn.first.get_attribute("disabled")
                if disabled2 is not None:
                    await send_btn.first.click(force=True)
                    print("Force clicked send.")
        else:
            await editor.press("Enter")
            print("Pressed Enter (no send button found).")

        await target_page.wait_for_timeout(5000)

        user_msgs_after = await target_page.locator('div[data-message-author-role="user"]').count()
        print(f"User messages after: {user_msgs_after}")

        if user_msgs_after > user_msgs_before:
            print(f"SUCCESS: Message sent ({user_msgs_before} -> {user_msgs_after})")
        else:
            print("WARNING: Message count unchanged. Submission may have failed.")
            return

        # Wait for GPT response
        print("Waiting for GPT response (up to 180s)...")
        await target_page.wait_for_timeout(180000)

        # Capture reply
        assistant_msgs = target_page.locator('div[data-message-author-role="assistant"]')
        count = await assistant_msgs.count()
        if count > 0:
            last_reply = await assistant_msgs.last.inner_text()
            print(f"\n=== GPT REPLY ({len(last_reply)} chars) ===")
            print(last_reply[:8000])

            out_path = r"D:\agent-acceptance\_evidence\R18-WORKSPACE-CLOSURE\gpt_reply_closure.txt"
            os.makedirs(os.path.dirname(out_path), exist_ok=True)
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(last_reply)
            print(f"\nSaved to {out_path}")
        else:
            print("No assistant messages found.")

import os
asyncio.run(main())
