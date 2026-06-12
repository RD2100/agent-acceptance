"""Wait for GPT R3 verdict and capture."""
import asyncio
import json
import sys
from pathlib import Path
from playwright.async_api import async_playwright

sys.stdout.reconfigure(encoding='utf-8')

CHAT_URL = "https://chatgpt.com/c/6a2a8cb1-b228-83aa-addb-79bda9aba043"
OUTPUT = Path(r"D:\agent-acceptance\_evidence\conversation_health_gate_a2_r3_verdict.txt")


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://localhost:9222")
        ctx = browser.contexts[0]

        target_page = None
        for pg in ctx.pages:
            if "6a2a8cb1" in pg.url:
                target_page = pg
                break
        if not target_page:
            target_page = ctx.pages[0]

        print(f"Page: {target_page.url}")

        # Wait for GPT to respond
        print("Waiting for GPT response (up to 300s)...")
        stop_btn = target_page.locator('button[aria-label="Stop generating"]')
        for i in range(60):
            await asyncio.sleep(5)
            if await stop_btn.count() > 0 and await stop_btn.first.is_visible():
                print(f"  Still generating... {(i+1)*5}s")
                continue
            else:
                await asyncio.sleep(5)
                if not (await stop_btn.count() > 0 and await stop_btn.first.is_visible()):
                    print(f"  Done at {(i+1)*5}s")
                    break

        # Capture
        ams = target_page.locator('div[data-message-author-role="assistant"]')
        cnt = await ams.count()
        print(f"\nAssistant messages: {cnt}")

        if cnt > 0:
            last = await ams.last.inner_text()
            print(f"Last msg: {len(last)} chars")

            if len(last) < 500:
                print(f"Short ({len(last)} chars): {last[:200]}")
                # Send follow-up
                follow = "请继续详细核验 R3 证据包，逐项检查 3 个 blocker 修复并给出最终判定 ACCEPTED / NEEDS_REVISION / REJECTED。"
                textarea = target_page.locator("#prompt-textarea")
                await textarea.click()
                await asyncio.sleep(0.5)
                await target_page.evaluate(f"navigator.clipboard.writeText({json.dumps(follow)})")
                await asyncio.sleep(0.3)
                await target_page.keyboard.press("Control+v")
                await asyncio.sleep(1)
                send_btn = target_page.locator('button[data-testid="send-button"]')
                if await send_btn.first.get_attribute("disabled") is None:
                    await send_btn.first.click()
                else:
                    await target_page.keyboard.press("Enter")
                print("Follow-up sent...")

                # Wait again
                for i in range(60):
                    await asyncio.sleep(5)
                    if await stop_btn.count() > 0 and await stop_btn.first.is_visible():
                        print(f"  Still generating... {(i+1)*5}s")
                        continue
                    else:
                        await asyncio.sleep(5)
                        if not (await stop_btn.count() > 0 and await stop_btn.first.is_visible()):
                            print(f"  Done at {(i+1)*5}s")
                            break

                ams = target_page.locator('div[data-message-author-role="assistant"]')
                last = await ams.last.inner_text()
                print(f"\nNew response: {len(last)} chars")

            print(last[:8000])
            if len(last) > 8000:
                print(f"\n... ({len(last) - 8000} more)")

            OUTPUT.write_text(last, encoding="utf-8")
            print(f"\nSaved: {OUTPUT}")

            upper = last.upper()
            for kw in ["ACCEPTED", "REJECTED", "NEEDS_REVISION"]:
                if kw in upper:
                    print(f"\n*** VERDICT: {kw} ***")
                    break


asyncio.run(main())
