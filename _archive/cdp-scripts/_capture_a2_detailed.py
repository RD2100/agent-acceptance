"""Send follow-up and capture detailed A2 verdict."""
import asyncio
import json
import sys
from pathlib import Path
from playwright.async_api import async_playwright

sys.stdout.reconfigure(encoding='utf-8')

CHAT_URL = "https://chatgpt.com/c/6a2a8cb1-b228-83aa-addb-79bda9aba043"
OUTPUT = Path(r"D:\agent-acceptance\_evidence\conversation_health_gate_a2_verdict.txt")

FOLLOW_UP = """请现在对 A2 证据包进行详细核验。

重点检查：
1. pre_gpt_gate.py 的 check_pre_gpt_gate() 是否正确阻断 FORCE_HANDOFF (exit 1) 和 HUMAN_REQUIRED (exit 2)
2. latest.json 和 current-snapshot.json 是否在 Pre-GPT 流程中被写入
3. 3 个 legacy 脚本是否正确集成
4. 8 个 runtime negative-path 证据是否与代码语义一致
5. A1 语义是否保持不变 (response_time alone → suggest, composite → force, etc.)
6. 1126 tests 是否全部通过
7. modified_tracked 是否为 0

请逐项给出通过/不通过，并最终判定 ACCEPTED / NEEDS_REVISION / REJECTED。"""


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

        print(f"Page: {target_page.url}")

        # Count messages before
        ub = await target_page.locator('div[data-message-author-role="user"]').count()
        print(f"User msgs before: {ub}")

        # Send follow-up
        textarea = target_page.locator("#prompt-textarea")
        await textarea.click()
        await asyncio.sleep(0.5)
        await target_page.evaluate(f"navigator.clipboard.writeText({json.dumps(FOLLOW_UP)})")
        await asyncio.sleep(0.3)
        await target_page.keyboard.press("Control+v")
        await asyncio.sleep(2)

        send_btn = target_page.locator('button[data-testid="send-button"]')
        disabled = await send_btn.first.get_attribute("disabled")
        if disabled is None:
            await send_btn.first.click()
        else:
            await target_page.keyboard.press("Enter")
        print("Follow-up sent!")

        await asyncio.sleep(5)
        ua = await target_page.locator('div[data-message-author-role="user"]').count()
        print(f"User msgs after: {ua}")

        # Wait for detailed response
        print("Waiting for GPT detailed response (up to 300s)...")
        stop_btn = target_page.locator('button[aria-label="Stop generating"]')
        for i in range(60):
            await asyncio.sleep(5)
            if await stop_btn.count() > 0 and await stop_btn.first.is_visible():
                print(f"  Still generating... {(i+1)*5}s")
                continue
            else:
                # Double-check it's really done
                await asyncio.sleep(5)
                if not await stop_btn.first.is_visible():
                    print(f"  Done at {(i+1)*5}s")
                    break

        # Capture response
        ams = target_page.locator('div[data-message-author-role="assistant"]')
        cnt = await ams.count()
        print(f"\nTotal assistant messages: {cnt}")

        if cnt > 0:
            last = await ams.last.inner_text()
            print(f"Last msg: {len(last)} chars")
            print(last[:8000])
            if len(last) > 8000:
                print(f"\n... ({len(last) - 8000} more)")

            OUTPUT.write_text(last, encoding="utf-8")
            print(f"\nSaved: {OUTPUT}")

            # Detect verdict
            upper = last.upper()
            for kw in ["ACCEPTED", "REJECTED", "NEEDS_REVISION"]:
                if kw in upper:
                    print(f"\n*** VERDICT: {kw} ***")
                    break


asyncio.run(main())
