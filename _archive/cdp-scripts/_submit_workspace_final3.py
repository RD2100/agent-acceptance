"""Submit R18 workspace cleanup FINAL ZIP to ChatGPT via CDP — v5 (handle duplicate modal)."""
import asyncio
from playwright.async_api import async_playwright

ZIP_PATH = r"D:\agent-acceptance\_evidence\EVIDENCE_PACK_R18_WORKSPACE_CLEANUP_FINAL.zip"
TARGET_URL = "https://chatgpt.com/c/6a297f76-3e7c-83a5-a0e5-b4413d923c7e"
CDP_URL = "http://localhost:9222"

SUBMISSION_MSG = """R18 Workspace Cleanup FINAL — Complete Rebuilt Evidence Pack (commit caa85c28)

EVIDENCE_PACK_R18_WORKSPACE_CLEANUP_FINAL.zip (22 files, 4907 KB)
SHA256: 0e5539d83bb526c79d9675b0daed25b0e979ea90505c891cca1594c2f87731c3

This submission supersedes all previous workspace cleanup submissions. All evidence files regenerated from scratch in single script pass for internal consistency.

Commits covered: 104ac8b1, f06ce965, 6022c187, caa85c28
Full R18 chain: 3fc33dac -> 4efcbac9 -> bc974d2f -> 104ac8b1 -> f06ce965 -> 6022c187 -> e1bbd516 -> 04b3d562 -> c4017e89 -> caa85c28

Evidence pack (22 files): diff-combined.patch, 3 individual diffs, 3 git-show files, git-status-after, git-log, chain-evidence.json, deferred-files-register.yaml, secret-scan, ai-guard, sadp-audit, staging-reconciliation, safety-report, test-output, review.md, review.yaml, final-report.md, 2 gpt replies.

Post-commit: 17x NEG-009 (deny_paths) + 3x secret-scan-output.txt (deny_list) = 20 untracked, all registered in deferred-files-register.yaml. Tests: 1038 passed, 0 failed."""

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
            print("Target page not found. Opening...")
            page = ctx.pages[0] if ctx.pages else await ctx.new_page()
            await page.goto(TARGET_URL, wait_until="networkidle", timeout=30000)
            target_page = page

        print(f"Page: {target_page.url}")
        await target_page.wait_for_timeout(3000)

        # Dismiss any modal that might be blocking
        print("Checking for modals...")
        modal = target_page.locator('#modal-duplicate-file')
        if await modal.count() > 0:
            print("Found duplicate-file modal, dismissing...")
            # Try clicking the primary/confirm button inside the modal
            modal_btn = modal.locator('button.btn-primary')
            if await modal_btn.count() > 0:
                await modal_btn.first.click(force=True)
                print("Clicked primary button in modal.")
            else:
                # Try any button
                modal_btns = modal.locator('button')
                btn_count = await modal_btns.count()
                print(f"Found {btn_count} buttons in modal")
                for i in range(btn_count):
                    btn_text = await modal_btns.nth(i).inner_text()
                    print(f"  Button {i}: '{btn_text}'")
                # Click the last button (usually the confirm/action button)
                if btn_count > 0:
                    await modal_btns.last.click(force=True)
                    print("Clicked last button in modal.")
            await target_page.wait_for_timeout(2000)

        # Also try Escape key
        await target_page.keyboard.press("Escape")
        await target_page.wait_for_timeout(1000)

        # Reload the page to get clean state
        print("Reloading page for clean state...")
        await target_page.reload(wait_until="networkidle", timeout=30000)
        await target_page.wait_for_timeout(5000)

        user_msgs_before = await target_page.locator('div[data-message-author-role="user"]').count()
        print(f"User messages before: {user_msgs_before}")

        # Upload ZIP
        print("Uploading ZIP...")
        file_input = target_page.locator('#upload-files')
        await file_input.set_input_files(ZIP_PATH)
        await target_page.wait_for_timeout(5000)
        print("File uploaded.")

        # Check for and dismiss duplicate modal if it appears again
        modal = target_page.locator('#modal-duplicate-file')
        if await modal.count() > 0 and await modal.is_visible():
            print("Duplicate modal appeared again, clicking confirm...")
            modal_btns = modal.locator('button')
            btn_count = await modal_btns.count()
            for i in range(btn_count):
                btn_text = await modal_btns.nth(i).inner_text()
                print(f"  Button {i}: '{btn_text}'")
            # Click the primary/confirm button
            modal_btn_primary = modal.locator('button.btn-primary')
            if await modal_btn_primary.count() > 0:
                await modal_btn_primary.first.click(force=True)
            elif btn_count > 0:
                await modal_btns.last.click(force=True)
            await target_page.wait_for_timeout(3000)

        # Type message
        print("Typing message...")
        editor = target_page.locator('#prompt-textarea')
        if await editor.count() == 0:
            editor = target_page.locator('div[contenteditable="true"]').last

        await editor.click(force=True)
        await target_page.wait_for_timeout(500)

        # Clear any existing content
        await target_page.keyboard.press("Control+a")
        await target_page.wait_for_timeout(200)
        await target_page.keyboard.press("Backspace")
        await target_page.wait_for_timeout(300)

        # Type message character by character (slow but reliable)
        await target_page.keyboard.type(SUBMISSION_MSG, delay=3)
        await target_page.wait_for_timeout(2000)

        # Check send button state
        send_btn = target_page.locator('button[data-testid="send-button"]')
        is_disabled = await send_btn.first.get_attribute("disabled")
        print(f"Send button disabled: {is_disabled}")

        if is_disabled is None:
            print("Send button enabled, clicking...")
            await send_btn.first.click(force=True)
        else:
            print("Send button still disabled, trying Enter key...")
            await target_page.keyboard.press("Enter")
            await target_page.wait_for_timeout(2000)
            is_disabled2 = await send_btn.first.get_attribute("disabled")
            print(f"After Enter - disabled: {is_disabled2}")
            # Force click regardless
            print("Force clicking send button...")
            await send_btn.first.click(force=True)

        await target_page.wait_for_timeout(8000)

        user_msgs_after = await target_page.locator('div[data-message-author-role="user"]').count()
        print(f"User messages after: {user_msgs_after}")

        if user_msgs_after > user_msgs_before:
            print(f"SUCCESS: Message sent ({user_msgs_before} -> {user_msgs_after})")
        else:
            print("WARNING: Message count unchanged, trying JS approach...")
            # Use JavaScript to set text and dispatch events
            await target_page.evaluate("""
                (msg) => {
                    const editor = document.querySelector('#prompt-textarea');
                    if (editor) {
                        editor.focus();
                        editor.textContent = msg;
                        editor.dispatchEvent(new InputEvent('input', { bubbles: true, inputType: 'insertText', data: msg }));
                        // Also try React-style event
                        const nativeInputValueSetter = Object.getOwnPropertyDescriptor(window.HTMLElement.prototype, 'textContent');
                        if (nativeInputValueSetter && nativeInputValueSetter.set) {
                            nativeInputValueSetter.set.call(editor, msg);
                        }
                        editor.dispatchEvent(new Event('input', { bubbles: true }));
                    }
                }
            """, SUBMISSION_MSG)
            await target_page.wait_for_timeout(3000)
            is_disabled3 = await send_btn.first.get_attribute("disabled")
            print(f"After JS - disabled: {is_disabled3}")
            if is_disabled3 is None:
                await send_btn.first.click()
                print("Clicked after JS.")
            else:
                await send_btn.first.click(force=True)
                print("Force clicked after JS.")
            await target_page.wait_for_timeout(5000)
            user_msgs_after2 = await target_page.locator('div[data-message-author-role="user"]').count()
            print(f"After retry - messages: {user_msgs_after2}")

        # Wait for GPT response
        print("Waiting for GPT response (180s)...")
        await target_page.wait_for_timeout(180000)

        assistant_msgs = target_page.locator('div[data-message-author-role="assistant"]')
        count = await assistant_msgs.count()
        if count > 0:
            last_reply = await assistant_msgs.last.inner_text()
            print(f"\n=== GPT REPLY ({len(last_reply)} chars) ===")
            print(last_reply[:5000])

            out_path = r"D:\agent-acceptance\_evidence\R18-WORKSPACE-CLEANUP-FINAL\gpt_reply_final4.txt"
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(last_reply)
            print(f"\nSaved to {out_path}")

asyncio.run(main())
