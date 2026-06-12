"""Submit R18 Evidence Maintenance FINAL ZIP to ChatGPT via CDP."""
import asyncio, os
from playwright.async_api import async_playwright

ZIP_PATH = r"D:\agent-acceptance\_evidence\EVIDENCE_PACK_R18_EVIDENCE_MAINTENANCE_FINAL.zip"
TARGET_URL = "https://chatgpt.com/c/6a297f76-3e7c-83a5-a0e5-b4413d923c7e"
CDP_URL = "http://localhost:9222"

MSG = """R18 Evidence Maintenance FINAL — All session artifacts committed (efd5b96e)

EVIDENCE_PACK_R18_EVIDENCE_MAINTENANCE_FINAL.zip (24 files, 20 KB)
SHA256: a8f7cd7458a28f8da1b463813f73e0273af97d798d9505ca261edc37cce3fdb6

Follow-up to R18 Workspace Closure SLIM (ACCEPTED_WITH_LIMITATION).
This addresses the non-blocking follow-up: commit all 8 pending session artifacts.

=== WHAT CHANGED ===
Commit efd5b96e (60 files): all session scripts, evidence directories, GPT replies committed.
SADP hook: PASS — 60/60 files covered by TaskSpec write_sets.
Tests: 1038 passed, 0 failed, 21 warnings.

=== POST-COMMIT STATE ===
- Modified tracked: 0
- Untracked: 23 total
  - 17x NEG-009 fixtures (deny_paths — permanently deferred)
  - 5x secret-scan-output.txt (deny_list — permanently denied, contain mock patterns)
  - 1x _build_evidence_maintenance.py (current builder script, pending next commit)
- All entries registered in deferred-files-register.yaml
- Consistency: all 5 evidence files report identical numbers

=== COMMITS IN EVIDENCE ===
104ac8b1: registry reconciliation
f06ce965: closure evidence
6022c187: updated evidence
caa85c28: FINAL rebuilt evidence
efd5b96e: evidence maintenance — all artifacts committed

=== WORKSPACE STATUS ===
Zero committable files remain untracked (excluding the current builder script).
Only permanently deferred/denied files remain: 17 NEG-009 + 5 secret-scan = 22 permanently blocked.
This is the cleanest achievable state given SADP deny_paths and deny_list constraints."""

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
            print("ERROR: Page not found")
            return

        print(f"Page: {target_page.url}")
        await target_page.wait_for_timeout(3000)

        ub = await target_page.locator('div[data-message-author-role="user"]').count()
        print(f"User msgs before: {ub}")

        print("Uploading ZIP...")
        await target_page.locator('#upload-files').set_input_files(ZIP_PATH)
        await target_page.wait_for_timeout(3000)

        # Dismiss modal
        modal = target_page.locator('#modal-duplicate-file')
        if await modal.count() > 0 and await modal.is_visible():
            btns = modal.locator('button')
            cnt = await btns.count()
            pb = modal.locator('button.btn-primary')
            if await pb.count() > 0:
                await pb.first.click(force=True)
            elif cnt > 0:
                await btns.last.click(force=True)
            await target_page.wait_for_timeout(2000)

        # Type via clipboard
        editor = target_page.locator('#prompt-textarea')
        if await editor.count() == 0:
            editor = target_page.locator('div[contenteditable="true"]').last
        await editor.click()
        await target_page.wait_for_timeout(500)

        await target_page.evaluate(f"""
            async () => {{
                await navigator.clipboard.writeText({repr(MSG)});
            }}
        """)
        await target_page.wait_for_timeout(500)
        await editor.press("Control+v")
        await target_page.wait_for_timeout(2000)

        # Send
        send_btn = target_page.locator('button[data-testid="send-button"]')
        disabled = await send_btn.first.get_attribute("disabled")
        print(f"Send disabled: {disabled}")
        if disabled is None:
            await send_btn.first.click()
        else:
            await editor.press("Enter")
            await target_page.wait_for_timeout(2000)
            d2 = await send_btn.first.get_attribute("disabled")
            if d2 is not None:
                await send_btn.first.click(force=True)

        await target_page.wait_for_timeout(5000)
        ua = await target_page.locator('div[data-message-author-role="user"]').count()
        print(f"User msgs after: {ua}")
        if ua <= ub:
            print("WARNING: Message may not have been sent")
            return
        print(f"SUCCESS: {ub} -> {ua}")

        print("Waiting for GPT (180s)...")
        await target_page.wait_for_timeout(180000)

        ams = target_page.locator('div[data-message-author-role="assistant"]')
        cnt = await ams.count()
        if cnt > 0:
            reply = await ams.last.inner_text()
            print(f"\n=== GPT REPLY ({len(reply)} chars) ===")
            print(reply[:8000])
            op = r"D:\agent-acceptance\_evidence\R18-EVIDENCE-MAINTENANCE-FINAL\gpt_reply_maintenance.txt"
            os.makedirs(os.path.dirname(op), exist_ok=True)
            with open(op, "w", encoding="utf-8") as f:
                f.write(reply)
            print(f"\nSaved: {op}")

asyncio.run(main())
