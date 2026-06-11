"""Ask GPT for next task after CONVERSATION-HEALTH-GATE-A1 ACCEPTED.

CONVERSATION-HEALTH-GATE-A2: Integrated with pre_gpt_gate.
"""
import asyncio, os, json, sys
from pathlib import Path
from playwright.async_api import async_playwright

# A2 integration: import gate check
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _cdp_submit_helper import run_pre_gpt_gate  # noqa: E402

TARGET_URL = "https://chatgpt.com/c/6a2a8cb1-b228-83aa-addb-79bda9aba043"
CDP_URL = "http://localhost:9222"

MSG = """CONVERSATION-HEALTH-GATE-A1 已 ACCEPTED (R4 verdict)。

当前项目状态：
- A1 完成：四层对话健康防御 (Pre-Task Hard Gate + Pre-GPT Gate 基础 + Evidence Pack + Pre-Commit Advisory 基础)
- 最新 commit: fbb08f0 (R4 schema/CLI/evidence gaps closed)
- 测试：1098 passed, 0 failed
- modified_tracked: 0
- 所有 A1 acceptance criteria 已闭合

你在 R4 verdict 中提到下一步可以进入 A2：Pre-GPT Gate + CDP metrics refresh + legacy submit script integration。

请确认：
1. 下一个任务是否就是 A2？还是有更优先的任务？
2. 请给出具体的任务描述、验收标准和范围边界。
3. 如果有其他待处理任务（如 OPERATIONS-MANUAL-AUDIT-PATTERN-BIND-A1 等），请说明优先级。"""


async def main():
    import time as _time
    _start_time = _time.monotonic()

    # A2: Pre-GPT gate check before CDP interaction
    exit_code, decision, message = run_pre_gpt_gate()
    if exit_code != 0:
        print(f"GATE BLOCKED (exit {exit_code}): {message}")
        sys.exit(exit_code)
    print(f"GATE: {message}")

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
            # Try navigating in first page
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
                await navigator.clipboard.writeText({json.dumps(MSG)});
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
            # Take screenshot for debug
            await target_page.screenshot(path=r"D:\agent-acceptance\_evidence\ask_next_task_debug.png")
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
            print(reply[:10000])
            op = r"D:\agent-acceptance\_evidence\next_task_reply.txt"
            os.makedirs(os.path.dirname(op), exist_ok=True)
            with open(op, "w", encoding="utf-8") as f:
                f.write(reply)
            print(f"\nSaved: {op}")

            # A2: Post-response metrics refresh — write back to current.json
            import time as _time
            _reply_bytes = len(reply.encode("utf-8"))
            _resp_time = _time.monotonic() - _start_time if '_start_time' in dir() else None
            try:
                from pre_gpt_gate import update_metrics as _um
                _new_metrics = {
                    "assistant_message_count": cnt,
                    "last_gpt_reply_bytes": _reply_bytes,
                }
                if _resp_time is not None:
                    _new_metrics["last_response_time_seconds"] = round(_resp_time, 1)
                _updated, _err = _um(new_metrics=_new_metrics, nav_result="ok",
                                      source="cdp_dom_count")
                if _err:
                    print(f"WARNING: Metrics refresh failed: {_err}")
                else:
                    print(f"A2: current.json refreshed — msgs={cnt}, bytes={_reply_bytes}")
            except ImportError:
                print("WARNING: pre_gpt_gate not available for post-response refresh")
        else:
            print("No assistant messages found")
            await target_page.screenshot(path=r"D:\agent-acceptance\_evidence\ask_next_task_debug.png")


asyncio.run(main())
