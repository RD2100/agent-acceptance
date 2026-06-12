"""Capture A2 verdict from GPT."""
import asyncio
import json
import sys
from pathlib import Path
from playwright.async_api import async_playwright

sys.stdout.reconfigure(encoding='utf-8')

CHAT_URL = "https://chatgpt.com/c/6a2a8cb1-b228-83aa-addb-79bda9aba043"
OUTPUT = Path(r"D:\agent-acceptance\_evidence\conversation_health_gate_a2_verdict.txt")


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://localhost:9222")
        ctx = browser.contexts[0]

        target_page = None
        for page in ctx.pages:
            if "6a2a8cb1-b228-83aa-addb-79bda9aba043" in page.url:
                target_page = page
                break
        if not target_page:
            target_page = ctx.pages[0]
            await target_page.goto(CHAT_URL, wait_until="networkidle", timeout=30000)

        await target_page.wait_for_timeout(3000)

        # Check current assistant messages
        ams = target_page.locator('div[data-message-author-role="assistant"]')
        cnt = await ams.count()
        print(f"Assistant messages: {cnt}")

        if cnt > 0:
            last = await ams.last.inner_text()
            print(f"Last msg length: {len(last)} chars")

            if len(last) < 300:
                print("Short response, sending follow-up...")
                textarea = target_page.locator("#prompt-textarea")
                await textarea.click()
                await asyncio.sleep(0.5)
                follow = "请继续详细核验 A2 证据包，逐项检查验收标准并给出最终判定 ACCEPTED / NEEDS_REVISION / REJECTED。"
                await target_page.evaluate(f"navigator.clipboard.writeText({json.dumps(follow)})")
                await asyncio.sleep(0.3)
                await target_page.keyboard.press("Control+v")
                await asyncio.sleep(1)
                await target_page.keyboard.press("Enter")
                print("Follow-up sent, waiting for detailed response...")

            # Wait for response to complete
            stop_btn = target_page.locator('button[aria-label="Stop generating"]')
            for i in range(60):
                await asyncio.sleep(5)
                if not await stop_btn.is_visible():
                    await asyncio.sleep(10)
                    if not await stop_btn.is_visible():
                        print(f"Done after ~{(i+1)*5}s")
                        break

            # Capture final response
            ams = target_page.locator('div[data-message-author-role="assistant"]')
            last = await ams.last.inner_text()
            print(f"\nFinal response: {len(last)} chars")
            print(last[:5000])
            if len(last) > 5000:
                print(f"\n... ({len(last) - 5000} more)")

            OUTPUT.write_text(last, encoding="utf-8")
            print(f"\nSaved: {OUTPUT}")

            # Detect verdict
            upper = last.upper()
            for kw in ["ACCEPTED", "REJECTED", "NEEDS_REVISION"]:
                if kw in upper:
                    print(f"\n*** VERDICT: {kw} ***")
                    break
        else:
            print("No assistant messages found")


asyncio.run(main())
