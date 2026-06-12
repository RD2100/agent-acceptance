"""Diagnose and retry submission."""
import asyncio
from playwright.async_api import async_playwright

TARGET_URL = "https://chatgpt.com/c/6a297f76-3e7c-83a5-a0e5-b4413d923c7e"
ZIP_PATH = r"D:\agent-acceptance\_evidence\EVIDENCE_PACK_HOOK_FAILURE_RUNTIME_VALIDATION_V2.zip"

MESSAGE = """BLOCKER-FIX V2: 5 个 blocker 全部修复。

BLOCKING-01: validator v2.3.0 语义 (ai_guard failure=BLOCKED, PASS_WITH_WARNINGS 禁止)
BLOCKING-02: diff.patch 仅含 f95b95c (8 files, 与 git-show 一致)
BLOCKING-03: modified_tracked=0 (已 stash)
BLOCKING-04: 6 个负路径 fixture 全部通过
BLOCKING-05: ai_guard 使用 Job.ChildJobs[0].ExitCode (null-safe)

SHA-256: 26b3b278afa2cff9be7c28d3320b241c7192ede67afcdc9cbbef65c37c028346
1072 tests passed, 0 failed

请审核。"""

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://localhost:9222")
        ctx = browser.contexts[0]
        page = None
        for pg in ctx.pages:
            if "chatgpt.com" in pg.url:
                page = pg
                break
        if not page:
            print("No page")
            return

        if TARGET_URL not in page.url:
            await page.goto(TARGET_URL, wait_until="domcontentloaded", timeout=30000)
            await asyncio.sleep(3)

        msgs_before = await page.evaluate("() => document.querySelectorAll('[data-message-author-role]').length")
        print(f"Messages before: {msgs_before}")

        # Dismiss any modals
        try:
            modal_btn = await page.query_selector('[role="dialog"] button')
            if modal_btn:
                await modal_btn.click()
                await asyncio.sleep(1)
                print("Dismissed modal")
        except:
            pass

        # Re-upload ZIP
        upload = await page.query_selector("#upload-files")
        if upload:
            await upload.set_input_files(ZIP_PATH)
            await asyncio.sleep(3)
            print("ZIP re-uploaded")

        # Type message
        editor = await page.query_selector('[contenteditable="true"]')
        if editor:
            await editor.click()
            await asyncio.sleep(0.3)
            await page.evaluate("(el) => { el.focus(); el.textContent = ''; }", editor)
            await asyncio.sleep(0.3)
            print("Typing...")
            await page.keyboard.type(MESSAGE, delay=2)
            await asyncio.sleep(2)

            editor_text = await page.evaluate("(el) => el.textContent", editor)
            print(f"Editor length: {len(editor_text)}")

        # Send
        send_btn = await page.query_selector('button[data-testid="send-button"]')
        if send_btn:
            disabled = await send_btn.get_attribute("disabled")
            print(f"Send disabled: {repr(disabled)}")
            if disabled is None:
                await send_btn.click()
                print("Clicked send")
            else:
                await page.keyboard.press("Enter")
                print("Enter key")
        else:
            await page.keyboard.press("Enter")
            print("No button, Enter")

        await asyncio.sleep(5)
        msgs_after = await page.evaluate("() => document.querySelectorAll('[data-message-author-role]').length")
        print(f"Messages after: {msgs_after}")
        if msgs_after > msgs_before:
            print("SUCCESS!")
        else:
            print("FAILED - message count unchanged")

asyncio.run(main())
