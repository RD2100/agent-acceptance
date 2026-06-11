#!/usr/bin/env python3
"""Send review request and capture GPT response."""
import asyncio
import sys
from pathlib import Path

try:
    from playwright.async_api import async_playwright
except ImportError:
    sys.exit("ERROR: playwright not installed")

TASK_DIR = Path(r"D:\agent-acceptance\_reports\multi-agent-multi-gpt-pilot-a1")

REVIEW_REQUEST = """请根据以上所有证据，对 MULTI-AGENT-MULTI-GPT-PILOT-A1 任务进行完整审查。

请按以下格式输出审查结果：

## 审查结论 (Overall Judgment)

给出以下三种之一：accepted / accepted_with_limitation / blocked

## 各检查项评估

1. 双 Agent 绑定是否真实有效？
2. Gate 0 Preflight PASS 是否可信？
3. Dispatch Plan READY 是否合理？
4. 测试覆盖是否充分（718 passed）？
5. CAP-029 升级是否有充分依据？
6. 安全边界是否完好？

## 发现的问题（如有）

## 最终判定

请给出明确的 accepted / accepted_with_limitation / blocked 判定。"""


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://localhost:9222")
        context = browser.contexts[0]
        page = context.pages[0]

        title = await page.title()
        url = page.url
        print(f"Connected to: {title} ({url})")

        # Count existing messages
        msgs = page.locator('[data-message-author-role="assistant"]')
        count = await msgs.count()
        print(f"Current assistant messages: {count}")

        # Send review request
        input_sel = "#prompt-textarea"
        try:
            await page.wait_for_selector(input_sel, timeout=8000)
        except Exception:
            input_sel = '[contenteditable="true"]'
            await page.wait_for_selector(input_sel, timeout=8000)

        await page.click(input_sel)
        await asyncio.sleep(0.3)
        await page.keyboard.press("Control+a")
        await asyncio.sleep(0.1)
        await page.keyboard.press("Backspace")
        await asyncio.sleep(0.2)

        await page.keyboard.insert_text(REVIEW_REQUEST)
        await asyncio.sleep(1)
        await page.keyboard.press("Enter")
        print("Review request submitted!")

        # Wait for response
        print("Waiting for GPT review response...")
        for i in range(36):  # 180 seconds max
            stop_btn = page.locator('button[aria-label="Stop generating"]')
            generating = await stop_btn.count() > 0
            if not generating and i > 3:
                msgs = page.locator('[data-message-author-role="assistant"]')
                new_count = await msgs.count()
                if new_count > count:
                    last = msgs.nth(new_count - 1)
                    text = await last.inner_text()
                    if len(text) > 100:
                        print(f"GPT finished. Response: {len(text)} chars")
                        result_file = TASK_DIR / "GPT_REVIEW_RESULT_R2.txt"
                        result_file.write_text(text, encoding="utf-8")
                        print(f"Response saved to {result_file}")
                        print(f"\nPreview:\n{text[:800]}")
                        return
            await asyncio.sleep(5)

        # Timeout fallback
        msgs = page.locator('[data-message-author-role="assistant"]')
        new_count = await msgs.count()
        if new_count > count:
            last = msgs.nth(new_count - 1)
            text = await last.inner_text()
            result_file = TASK_DIR / "GPT_REVIEW_RESULT_R2.txt"
            result_file.write_text(text, encoding="utf-8")
            print(f"Timeout but captured: {len(text)} chars")
            print(text[:800])
        else:
            print("ERROR: Could not capture response")


asyncio.run(main())
