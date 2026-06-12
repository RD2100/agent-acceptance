"""Ask GPT about the actual next task after A4 + UAWS-A1 both completed."""
import asyncio, os, json, sys
from pathlib import Path
from playwright.async_api import async_playwright

TARGET_URL = "https://chatgpt.com/c/6a2a8cb1-b228-83aa-addb-79bda9aba043"
CDP_URL = "http://localhost:9222"

MSG = """CONVERSATION-HEALTH-GATE-A4 已 ACCEPTED_WITH_LIMITATION（R1 verdict 已记录）。

当前 Conversation Health Gate 四层体系完整闭环：
- A1: ACCEPTED — Pre-Task Hard Gate + Data Layer + Evidence Pack
- A2: ACCEPTED — Pre-GPT Gate + CDP Metrics Refresh
- A3: ACCEPTED_WITH_LIMITATION — Pre-Commit Advisory + Registry Reconciliation
- A4: ACCEPTED_WITH_LIMITATION — Startup Read Gate Item 1.9

你在 A4 verdict 中推荐的下一任务是 UNIVERSAL-AGENT-WORKFLOW-STANDARD-A1。

但是 UAWS-A1 实际上已在之前的 session 中完成：
- commit: 9d699fb0 (feat: Universal Agent Workflow Standard A1)
- 判定: ACCEPTED_WITH_LIMITATION
- 9 个 governance docs + operations manual cross-reference
- Limitations: 仅文档/治理标准，无 runtime enforcement；live dispatch 未授权
- 当时推荐的后续: EVIDENCE-CAPTURE-STANDARD-A1

当前 TaskSpec 状态已更新为 accepted_with_limitation。

请确认：
1. 下一步应该做什么？EVIDENCE-CAPTURE-STANDARD-A1？还是其他任务？
2. 如果有其他更高优先级的任务，请说明。
3. 请给出具体的任务描述和验收标准。"""


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

        ub = await target_page.locator('div[data-message-author-role="user"]').count()
        print(f"User msgs before: {ub}")

        editor = target_page.locator('#prompt-textarea')
        if await editor.count() == 0:
            editor = target_page.locator('div[contenteditable="true"]').last
        await editor.click()
        await target_page.wait_for_timeout(500)

        await target_page.evaluate(f"""
            async () => {{
                await navigator.clipboard.writeText({json.dumps(MSG, ensure_ascii=False)});
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

        print("Waiting for GPT response (120s)...")
        await target_page.wait_for_timeout(120000)

        stop_btn = target_page.locator('button[data-testid="stop-button"]')
        if await stop_btn.count() > 0 and await stop_btn.first.is_visible():
            print("GPT still generating, waiting more (60s)...")
            await target_page.wait_for_timeout(60000)

        ams = target_page.locator('div[data-message-author-role="assistant"]')
        cnt = await ams.count()
        if cnt > 0:
            reply = await ams.last.inner_text()
            print(f"\n=== GPT REPLY ({len(reply)} chars) ===")
            print(reply[:15000])
            op = r"D:\agent-acceptance\_evidence\next_task_reply_after_a4.txt"
            os.makedirs(os.path.dirname(op), exist_ok=True)
            with open(op, "w", encoding="utf-8") as f:
                f.write(reply)
            print(f"\nSaved: {op}")
        else:
            print("No assistant messages found")


asyncio.run(main())
