#!/usr/bin/env python3
"""Submit a question to GPT about solidifying the capture process."""
import asyncio, json, time
from pathlib import Path
import pyperclip
from playwright.async_api import async_playwright

ROOT = Path('D:/agent-acceptance')
TARGET_URL = 'https://chatgpt.com/c/6a26cc03-235c-83a2-a0fc-cd29be615959'
OUT = ROOT / '_reports/handoff-workflow-hardening-plan-a1/GPT_CAPTURE_ADVICE.txt'

QUESTION = """我在自动化提交 GPT 审查时遇到一个 capture 问题，请帮我分析并给出固化建议：

问题描述：
在延续性对话中（已有多轮 user/assistant 消息），我的 Playwright 脚本用 `msgs.last.inner_text()` 捕获最后一条 assistant 消息。但这次它捕获了 assistant[3]（一个 Qwen 提示词模板），而不是 assistant[4]（我们本次提交的真正 verdict）。

我的分析：
1. 提交后 user_count 确实增加了（send_confirm OK）
2. GPT 返回了 verdict 作为 assistant[4]
3. 但 capture 循环的 `msgs.last` 返回了 assistant[3]，可能是因为 assistant[4] 还在生成中
4. 后来我通过扫描所有 assistant 消息并匹配 run_id 才找到正确回复

请回答：
1. 在延续性对话中，capture 脚本应该如何确保取到的是本次提交对应的回复，而不是旧回复？
2. 是否建议在提交前记录 `before_assistant_count`，然后只看 `index >= before_assistant_count` 的消息？
3. 对于 run_id 匹配逻辑，你有什么建议来防止误取？
4. 这套提交流程应该如何固化到项目的 runbook 和脚本中？

请用中文回答，保留机器字段名英文。"""


async def find_editor(page):
    for sel in ['div[contenteditable="true"].ProseMirror', 'div[contenteditable="true"]', 'textarea']:
        loc = page.locator(sel)
        if await loc.count() > 0:
            return loc.last
    raise RuntimeError('editor not found')


async def click_visible_send_button(page):
    selectors = [
        'button[data-testid="send-button"]', '#composer-submit-button',
        'button.composer-submit-button-color', 'button[aria-label*="Send"]',
        'button:has-text("Send")', 'button:has-text("发送")',
    ]
    for sel in selectors:
        try:
            loc = page.locator(sel)
            for i in range(await loc.count()):
                btn = loc.nth(i)
                if await btn.is_visible(timeout=1000) and await btn.is_enabled(timeout=1000):
                    await btn.click(timeout=10000)
                    return {'ok': True, 'selector': sel}
        except Exception:
            pass
    return {'ok': False}


async def main():
    async with async_playwright() as pw:
        browser = await pw.chromium.connect_over_cdp('http://127.0.0.1:9222')
        ctx = browser.contexts[0]
        page = None
        for pg in ctx.pages:
            if TARGET_URL in pg.url:
                page = pg
                break
        if page is None:
            page = await ctx.new_page()
            await page.goto(TARGET_URL, wait_until='domcontentloaded', timeout=60000)
        await page.bring_to_front()
        await asyncio.sleep(5)

        # Clear composer
        editor = await find_editor(page)
        await editor.click(timeout=10000)
        await page.keyboard.press('Control+A')
        await page.keyboard.press('Backspace')
        await asyncio.sleep(0.5)

        # Paste question
        pyperclip.copy(QUESTION)
        await editor.click(timeout=10000)
        await page.keyboard.press('Control+v')
        await asyncio.sleep(2)

        # Record assistant count before send
        before_assistant_count = await page.locator('[data-message-author-role="assistant"]').count()

        # Click send
        send_result = await click_visible_send_button(page)
        if not send_result.get('ok'):
            print('Send button not found')
            return
        print(f'Sent. before_assistant_count={before_assistant_count}')

        # Wait for reply
        last = ''
        stable = 0
        for tick in range(90):
            await asyncio.sleep(5)
            msgs = page.locator('[data-message-author-role="assistant"]')
            count = await msgs.count()
            if count <= before_assistant_count:
                continue
            # Only look at NEW messages (index >= before_assistant_count)
            reply = await msgs.nth(count - 1).inner_text(timeout=10000)
            if reply == last:
                stable += 1
            else:
                stable = 0
                last = reply
            if stable >= 12 and len(reply) > 100:
                print(f'Reply stable at tick {tick}, chars={len(reply)}')
                break

        OUT.write_text(last, encoding='utf-8')
        print(f'Reply saved: {len(last)} chars')
        print(last[:500])


asyncio.run(main())
