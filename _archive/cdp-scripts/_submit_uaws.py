"""Submit UAWS evidence via CDP — robust version with keyboard input."""
import asyncio, os
from playwright.async_api import async_playwright

ZIP_PATH = r"D:\agent-acceptance\_evidence\EVIDENCE_PACK_UNIVERSAL_AGENT_WORKFLOW_STANDARD_A1.zip"
TARGET_URL = "https://chatgpt.com/c/6a297f76-3e7c-83a5-a0e5-b4413d923c7e"
CDP_URL = "http://localhost:9222"

MSG = """UNIVERSAL-AGENT-WORKFLOW-STANDARD-A1 Evidence Pack

ZIP: EVIDENCE_PACK_UNIVERSAL_AGENT_WORKFLOW_STANDARD_A1.zip (16 files, 103 KB)
SHA256: c3dd8e58302fb428a76bd617d59eac92e39119498bfc04b1400b4853f33b1195

Commit: 9d699fb0 (13 files, SADP PASS). Type: docs and governance only.

9 standard documents created:
1. universal-agent-workflow-standard.md (707 lines)
2. startup-read-gate.md (178 lines)
3. pre-task-gate.md (207 lines)
4. pre-gpt-review-gate.md (351 lines)
5. evidence-pack-standard.md (163 lines)
6. status-state-machine.md (462 lines)
7. human-required-decision-record.md (347 lines)
8. workspace-closure-standard.md (153 lines)
9. evidence-generation-hygiene.md (195 lines)

operations-manual.md: added section 9 cross-reference (no rewrite).
Tests: 1038 passed, 0 failed. Post-commit: 0 modified, 29 untracked (all registered).
No runtime changes. No live dispatch. write_set narrow."""

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
            print("Page not found, navigating...")
            page = ctx.pages[0]
            await page.goto(TARGET_URL, wait_until="networkidle", timeout=30000)
            target_page = page

        print(f"Page: {target_page.url}")
        await target_page.wait_for_timeout(3000)

        ub = await target_page.locator('div[data-message-author-role="user"]').count()
        print(f"User msgs before: {ub}")

        # Upload ZIP
        print("Uploading ZIP...")
        await target_page.locator('#upload-files').set_input_files(ZIP_PATH)
        await target_page.wait_for_timeout(5000)

        # Dismiss any modal
        modal = target_page.locator('#modal-duplicate-file')
        if await modal.count() > 0 and await modal.is_visible():
            print("Dismissing duplicate modal...")
            pb = modal.locator('button.btn-primary')
            if await pb.count() > 0:
                await pb.first.click(force=True)
            else:
                btns = modal.locator('button')
                if await btns.count() > 0:
                    await btns.last.click(force=True)
            await target_page.wait_for_timeout(2000)

        # Focus the editor using JavaScript
        print("Focusing editor...")
        await target_page.evaluate("""
            () => {
                const editor = document.querySelector('#prompt-textarea');
                if (editor) { editor.focus(); }
            }
        """)
        await target_page.wait_for_timeout(500)

        # Use keyboard.type() for reliable text input
        print("Typing message via keyboard...")
        await target_page.keyboard.type(MSG, delay=2)
        await target_page.wait_for_timeout(2000)

        # Verify editor has content
        editor_text = await target_page.evaluate("""
            () => {
                const editor = document.querySelector('#prompt-textarea');
                return editor ? editor.textContent : 'not found';
            }
        """)
        print(f"Editor content length: {len(editor_text)}")

        # Check send button
        send_btn = target_page.locator('button[data-testid="send-button"]')
        disabled = await send_btn.first.get_attribute("disabled")
        print(f"Send button disabled attribute: {repr(disabled)}")

        if disabled is None:
            print("Button enabled, clicking...")
            await send_btn.first.click()
        else:
            # Try JS to enable the button
            print("Button disabled, trying to enable via input event...")
            await target_page.evaluate("""
                () => {
                    const editor = document.querySelector('#prompt-textarea');
                    if (editor) {
                        editor.dispatchEvent(new InputEvent('input', {
                            bubbles: true,
                            inputType: 'insertText'
                        }));
                    }
                }
            """)
            await target_page.wait_for_timeout(1000)
            disabled2 = await send_btn.first.get_attribute("disabled")
            print(f"After input event - disabled: {repr(disabled2)}")
            if disabled2 is None:
                await send_btn.first.click()
                print("Clicked after enabling.")
            else:
                print("Still disabled, force clicking...")
                await send_btn.first.click(force=True)

        await target_page.wait_for_timeout(8000)

        ua = await target_page.locator('div[data-message-author-role="user"]').count()
        print(f"User msgs after: {ua}")
        if ua <= ub:
            print("WARNING: Count unchanged. Trying Enter key...")
            await target_page.keyboard.press("Enter")
            await target_page.wait_for_timeout(5000)
            ua2 = await target_page.locator('div[data-message-author-role="user"]').count()
            print(f"After Enter: {ua2}")
            if ua2 > ub:
                print(f"SUCCESS after Enter: {ub} -> {ua2}")
            else:
                print("FAILED: Could not send message")
                return
        else:
            print(f"SUCCESS: {ub} -> {ua}")

        print("Waiting for GPT (180s)...")
        await target_page.wait_for_timeout(180000)

        ams = target_page.locator('div[data-message-author-role="assistant"]')
        cnt = await ams.count()
        if cnt > 0:
            reply = await ams.last.inner_text()
            print(f"\n=== GPT REPLY ({len(reply)} chars) ===")
            print(reply[:10000])
            op = r"D:\agent-acceptance\_evidence\UNIVERSAL-AGENT-WORKFLOW-STANDARD-A1\gpt_reply_uaws.txt"
            os.makedirs(os.path.dirname(op), exist_ok=True)
            with open(op, "w", encoding="utf-8") as f:
                f.write(reply)
            print(f"\nSaved: {op}")

asyncio.run(main())
