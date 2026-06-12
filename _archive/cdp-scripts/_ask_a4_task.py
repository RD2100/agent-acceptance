"""Ask GPT about CONVERSATION-HEALTH-GATE-A4 scope.

A3 completed with accepted_with_limitation. GPT authorized A4 with ask_before_starting=true.
"""
import asyncio, os, json, sys
from pathlib import Path
from playwright.async_api import async_playwright

TARGET_URL = "https://chatgpt.com/c/6a2a8cb1-b228-83aa-addb-79bda9aba043"
CDP_URL = "http://localhost:9222"

MSG = """CONVERSATION-HEALTH-GATE-A3 R2 已完成，verdict: accepted_with_limitation。

A3 成果总结：
- Pre-Commit Advisory (Layer 4) 已实现：hook v2.4.0，5 阶段（含 conversation-health advisory）
- Registry Reconciliation 已实现：reconcile_conversation_registry.py（5 项检查）
- Schema 更新：evidence-capture.schema.json（maxItems=5, conversation-health enum）
- 测试：1172 passed（含 A3 新增 42 个测试 + 9 个 R2 新测试）
- Advisory stage 已验证为 never block（exit code 仅诊断，不影响 overall_result）
- Commit 链：c5adb08 (R1) → 77e6320 (R2 fix) → a3269e1 (verdict recorded)

A3 Limitation（GPT 备注，非 blocker）：
- Evidence pack 缺少 review.yaml / final-report.md / full regression log
- 无 conversation-health exit_code!=0 的 runtime artifact（仅 test simulation 覆盖）

你在 R2 verdict 中授权了 CONVERSATION-HEALTH-GATE-A4（ask_before_starting: 是）。

A3 TaskSpec 中延期的内容：
- startup-read-gate item 7（conversation-health awareness 集成到启动读取门）

请给出：
1. A4 的具体任务描述和验收标准
2. A4 的范围边界（哪些做，哪些不做）
3. 是否还有其他优先于 A4 的待处理任务"""


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp(CDP_URL)
        ctx = browser.contexts[0]

        # Find the target page
        target_page = None
        for page in ctx.pages:
            if "6a2a8cb1-b228-83aa-addb-79bda9aba043" in page.url:
                target_page = page
                break

        if not target_page:
            target_page = ctx.pages[0]
            print(f"Navigating from {target_page.url} to target...")
            await target_page.goto(TARGET_URL, wait_until="networkidle", timeout=30000)
            await asyncio.sleep(5)

        print(f"Page: {target_page.url}")
        await target_page.wait_for_timeout(3000)

        # Count user messages before sending
        ub = await target_page.locator('div[data-message-author-role="user"]').count()
        print(f"User msgs before: {ub}")

        # Focus editor
        editor = target_page.locator('#prompt-textarea')
        if await editor.count() == 0:
            editor = target_page.locator('div[contenteditable="true"]').last
        await editor.click()
        await target_page.wait_for_timeout(500)

        # Paste via clipboard
        await target_page.evaluate(f"""
            async () => {{
                await navigator.clipboard.writeText({json.dumps(MSG, ensure_ascii=False)});
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
            await target_page.screenshot(path=r"D:\agent-acceptance\_evidence\ask_a4_debug.png")
            return
        print(f"SUCCESS: {ub} -> {ua}")

        # Wait for GPT response
        print("Waiting for GPT response (120s)...")
        await target_page.wait_for_timeout(120000)

        # Check if still generating
        stop_btn = target_page.locator('button[data-testid="stop-button"]')
        if await stop_btn.count() > 0 and await stop_btn.first.is_visible():
            print("GPT still generating, waiting more (60s)...")
            await target_page.wait_for_timeout(60000)

        # Capture reply
        ams = target_page.locator('div[data-message-author-role="assistant"]')
        cnt = await ams.count()
        if cnt > 0:
            reply = await ams.last.inner_text()
            print(f"\n=== GPT REPLY ({len(reply)} chars) ===")
            print(reply[:15000])
            op = r"D:\agent-acceptance\_evidence\next_task_reply_a4.txt"
            os.makedirs(os.path.dirname(op), exist_ok=True)
            with open(op, "w", encoding="utf-8") as f:
                f.write(reply)
            print(f"\nSaved: {op}")
        else:
            print("No assistant messages found")
            await target_page.screenshot(path=r"D:\agent-acceptance\_evidence\ask_a4_debug.png")


asyncio.run(main())
