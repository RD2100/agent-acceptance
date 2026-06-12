"""Ask GPT for next-step direction discussion with completeness analysis."""
import asyncio, json
from pathlib import Path
from playwright.async_api import async_playwright

CONV_ID = "6a26cc03-235c-83a2-a0fc-cd29be615959"
TARGET_URL = f"https://chatgpt.com/c/{CONV_ID}"
CDP_URL = "http://localhost:9222"
OUT_DIR = Path(r"D:\agent-acceptance\_evidence")

PROMPT = """你刚才给了一个项目整体状态分析。现在 QoderWork agent 做了一个完整性审计，发现了以下缺口。请你结合你的分析和这些缺口，给出你认为最合理的下一步执行方案（优先级排序 + 具体步骤）。

## QoderWork 完整性审计发现的缺口

### 高优先级

1. **Evidence Pack 未构建**：REVIEW-A1 和 FIX-A1 两个任务有 evidence 目录，但没有按 ECS-A2 标准跑 build_evidence_pack.py 生成 evidence-manifest.json + ZIP 文件。ECS-A2 要求每个任务产出 ECS-A2 compliant evidence pack。

2. **Reviewer 独立性违规**：SADP 规定 executor 不能写 review.md/review.yaml，reviewer 必须在独立 session 中运行。但这次是 executor (QoderWork) 自己写了 review.md 和 review.yaml。这是一个 P0 违规。

3. **GPT R2 没有给出特定裁决**：你的上一个回复是项目整体状态分析，不是对 FIX-A1 的 accepted/blocked 裁决。FIX-A1 的 fix 实际上没有被你正式审查。

### 中优先级

4. **ExecutionReport 缺失**：SADP 要求每个 @go 任务产出 ExecutionReport（executor + reviewer + finalizer），我们只有 evidence 目录。

5. **你识别的待办项**：HOOK-FAILURE-SEMANTICS-FINALIZE-A1、NEG-009-MOCK-SECRET-FIXTURE-POLICY-A1、LIVE-DISPATCH-HUMAN-AUTHORIZATION-A1、workspace 193+ untracked 文件。

## 我的问题

1. 从你的角度看，上面 5 个缺口哪些是最紧迫的？哪些可以先放？
2. 你认为下一步最应该做什么？给出优先级排序。
3. 如果要补 evidence pack + 独立 reviewer review，你认为工作量如何？值得做吗？
4. 关于 GPT R2 裁决缺失 — 你愿意现在对 FIX-A1 给出一个正式裁决吗？（suspend dev-frame-writing, registry 11→10, fresh dry-run 2 dispatchable 0 collisions）
5. 项目整体的下一步路径是什么？

请给出你的方案建议，要具体到可以被 agent 直接执行的程度。"""


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp(CDP_URL)
        ctx = browser.contexts[0]

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

        print("Waiting for GPT response (300s)...")
        await target_page.wait_for_timeout(300000)

        stop_btn = target_page.locator('button[data-testid="stop-button"]')
        if await stop_btn.count() > 0 and await stop_btn.first.is_visible():
            print("GPT still generating, waiting more (60s)...")
            await target_page.wait_for_timeout(60000)

        ams = target_page.locator('div[data-message-author-role="assistant"]')
        cnt = await ams.count()
        if cnt > 0:
            reply = await ams.last.inner_text()
            print(f"\n=== GPT RESPONSE ({len(reply)} chars) ===")
            print(reply[:25000])
            op = OUT_DIR / "next_direction_discussion.txt"
            with open(op, "w", encoding="utf-8") as f:
                f.write(reply)
            print(f"\nSaved: {op}")
        else:
            print("No assistant messages found")


asyncio.run(main())
