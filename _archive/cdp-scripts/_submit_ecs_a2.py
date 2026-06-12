"""Submit ECS-A2 evidence pack to GPT for review."""
import asyncio, os, json, sys
from pathlib import Path
from playwright.async_api import async_playwright

TARGET_URL = "https://chatgpt.com/c/6a2a8cb1-b228-83aa-addb-79bda9aba043"
CDP_URL = "http://localhost:9222"

PROMPT = Path(r"D:\agent-acceptance\_evidence\EVIDENCE-CAPTURE-STANDARD-A2\gpt_review_prompt_a2.md").read_text(encoding="utf-8")
ZIP_PATH = r"D:\agent-acceptance\_evidence\EVIDENCE_PACK_EVIDENCE_CAPTURE_STANDARD_A2.zip"


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp(CDP_URL)
        ctx = browser.contexts[0]

        target_page = None
        for page in ctx.pages:
            if "6a2a8cb1-b228-83aa-addb-79bda9aba043" in page.url:
                target_page = page
                break
        if not target_page:
            target_page = ctx.pages[0]
            await target_page.goto(TARGET_URL, wait_until="networkidle", timeout=30000)
            await asyncio.sleep(5)

        print(f"Page: {target_page.url}")
        await target_page.wait_for_timeout(3000)

        # Upload ZIP via file input
        print("Uploading ZIP attachment...")
        file_input = target_page.locator('#upload-files')
        if await file_input.count() > 0:
            await file_input.set_input_files(ZIP_PATH)
            await target_page.wait_for_timeout(3000)
            print("ZIP uploaded via file input")
        else:
            print("No file input found, trying button approach...")
            attach_btn = target_page.locator('button[aria-label*="Attach"], button[aria-label*="attach"], button[data-testid*="attach"]')
            if await attach_btn.count() > 0:
                await attach_btn.first.click()
                await target_page.wait_for_timeout(1000)
                fi2 = target_page.locator('#upload-files')
                if await fi2.count() > 0:
                    await fi2.set_input_files(ZIP_PATH)
                    await target_page.wait_for_timeout(3000)
                    print("ZIP uploaded via button+input")

        # Send prompt
        ub = await target_page.locator('div[data-message-author-role="user"]').count()
        print(f"User msgs before: {ub}")

        editor = target_page.locator('#prompt-textarea')
        if await editor.count() == 0:
            editor = target_page.locator('div[contenteditable="true"]').last
        await editor.click()
        await target_page.wait_for_timeout(500)

        await target_page.evaluate(f"""
            async () => {{
                await navigator.clipboard.writeText({json.dumps(PROMPT, ensure_ascii=False)});
            }}
        """)
        await target_page.wait_for_timeout(500)
        await editor.press("Control+v")
        await target_page.wait_for_timeout(2000)

        send_btn = target_page.locator('button[data-testid="send-button"]')
        disabled = await send_btn.first.get_attribute("disabled")
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

        print("Waiting for GPT response (240s)...")
        await target_page.wait_for_timeout(240000)

        stop_btn = target_page.locator('button[data-testid="stop-button"]')
        if await stop_btn.count() > 0 and await stop_btn.first.is_visible():
            print("GPT still generating, waiting more (60s)...")
            await target_page.wait_for_timeout(60000)

        ams = target_page.locator('div[data-message-author-role="assistant"]')
        cnt = await ams.count()
        if cnt > 0:
            reply = await ams.last.inner_text()
            print(f"\n=== GPT VERDICT ({len(reply)} chars) ===")
            print(reply[:20000])
            op = r"D:\agent-acceptance\_evidence\EVIDENCE-CAPTURE-STANDARD-A2\gpt_verdict_a2.txt"
            with open(op, "w", encoding="utf-8") as f:
                f.write(reply)
            print(f"\nSaved: {op}")
        else:
            print("No assistant messages found")


asyncio.run(main())
