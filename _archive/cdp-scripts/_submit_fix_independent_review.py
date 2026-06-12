"""Submit LIVE-DISPATCH-READINESS-FIX-A1 to GPT for independent reviewer verdict."""
import asyncio, os, json, sys
from pathlib import Path
from playwright.async_api import async_playwright

CONV_ID = "6a26cc03-235c-83a2-a0fc-cd29be615959"
TARGET_URL = f"https://chatgpt.com/c/{CONV_ID}"
CDP_URL = "http://localhost:9222"

SUBMISSION = Path(r"D:\agent-acceptance\_evidence\LIVE-DISPATCH-READINESS-FIX-A1\gpt-review-submission.md").read_text(encoding="utf-8")

PROMPT = f"""{SUBMISSION}

---

Please evaluate this as an INDEPENDENT REVIEWER. Your verdict will be recorded as the formal independent review for FIX-A1, repairing the reviewer independence violation from the original task execution."""

OUT_DIR = Path(r"D:\agent-acceptance\_evidence\LIVE-DISPATCH-READINESS-FIX-A1")


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp(CDP_URL)
        ctx = browser.contexts[0]

        # Find target page
        target_page = None
        for page in ctx.pages:
            if CONV_ID in page.url:
                target_page = page
                break
        if not target_page:
            target_page = ctx.pages[0]
            await target_page.goto(TARGET_URL, wait_until="networkidle", timeout=30000)
            await asyncio.sleep(5)

        print(f"Page: {target_page.url}")
        await target_page.wait_for_timeout(3000)

        # Count user messages before
        ub = await target_page.locator('div[data-message-author-role="user"]').count()
        print(f"User msgs before: {ub}")

        # Paste prompt
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

        # Send
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

        # Wait for response
        print("Waiting for GPT response (240s)...")
        await target_page.wait_for_timeout(240000)

        # Check if still generating
        stop_btn = target_page.locator('button[data-testid="stop-button"]')
        if await stop_btn.count() > 0 and await stop_btn.first.is_visible():
            print("GPT still generating, waiting more (60s)...")
            await target_page.wait_for_timeout(60000)

        # Capture response
        ams = target_page.locator('div[data-message-author-role="assistant"]')
        cnt = await ams.count()
        if cnt > 0:
            reply = await ams.last.inner_text()
            print(f"\n=== GPT INDEPENDENT VERDICT ({len(reply)} chars) ===")
            print(reply[:20000])
            op = OUT_DIR / "gpt-review-raw.md"
            with open(op, "w", encoding="utf-8") as f:
                f.write(reply)
            print(f"\nSaved: {op}")
        else:
            print("No assistant messages found")


asyncio.run(main())
