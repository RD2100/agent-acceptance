# GPT 审查浏览器提交操作指引

> 用途：下一个智能体卡在浏览器提交环节时，直接按此文档执行，不需要重新摸索。

## 前置依赖

- Chrome 安装在 `C:\Program Files\Google\Chrome\Application\chrome.exe`
- Python 库：`playwright`（已安装），`pyperclip`
- 仓库：`D:/agent-acceptance`

## 第一步：启动 Chrome CDP

```python
from pathlib import Path
import subprocess, time, urllib.request

chrome = Path(r'C:/Program Files/Google/Chrome/Application/chrome.exe')
profile = Path('D:/agent-acceptance/.chrome-cdp-profile')
profile.mkdir(exist_ok=True)
port = 9222

proc = subprocess.Popen([
    str(chrome),
    f'--remote-debugging-port={port}',
    f'--user-data-dir={profile}',
    '--new-window',
    'https://chatgpt.com/'
], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

# 等待 CDP 就绪
for _ in range(10):
    time.sleep(1)
    try:
        urllib.request.urlopen(f'http://127.0.0.1:{port}/json/version', timeout=2)
        break
    except Exception:
        pass
```

如果端口 9222 已被占用，改用 9223、9224 等。如果已有 Chrome CDP 正在运行，直接连接即可，不要重复启动。

## 第二步：确定目标对话页面

**区分两种场景：**

### 场景 A：延续项目上下文的咨询/讨论
- 目标 URL 从项目文档读取：
  - 检查 `_reports/*/GPT_REVIEW_CHAT_URL.txt`
  - 检查 `HANDOFF_APPROVAL_RECORD.json` 的 `new_gpt_chat_url`
  - **当前项目上下文对话：`https://chatgpt.com/c/6a26cc03-235c-83a2-a0fc-cd29be615959`**
- 不得开空白新对话，否则 GPT 无上下文。
- 使用 `for pg in ctx.pages: if URL in pg.url: page = pg`

### 场景 B：独立 evidence pack 审查
- 开新 ChatGPT 页面：`page = await ctx.new_page(); await page.goto('https://chatgpt.com/')`
- 通过 UI 点击"新聊天"或直接打开首页。

## 第三步：Playwright 连接与操作模板

```python
import asyncio, json, time, hashlib
from playwright.async_api import async_playwright

async def main():
    # 1. 连接 CDP
    async with async_playwright() as pw:
        browser = await pw.chromium.connect_over_cdp('http://127.0.0.1:9222')
        ctx = browser.contexts[0]
        
        # 2. 打开目标页面（场景 A 复用已有页，场景 B 新开）
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

        # 3. 清空输入框
        editor = page.locator('div[contenteditable="true"]')
        await editor.first.click()
        await page.keyboard.press('Control+A')
        await page.keyboard.press('Backspace')

        # 4. 上传附件
        inputs = page.locator('input[type="file"]')
        for i in range(await inputs.count()):
            try:
                await inputs.nth(i).set_input_files(str(PACK_ZIP_PATH))
                await asyncio.sleep(8)
                body = await page.locator('body').inner_text(timeout=5000)
                if '你的附件关键词' in body.lower():
                    print('上传确认成功')
                    break
            except Exception:
                pass

        # 5. 粘贴 prompt（必须包含 run_id + task_id + END_OF_GPT_RESPONSE）
        import pyperclip
        pyperclip.copy(PROMPT_TEXT)
        await editor.first.click()
        await page.keyboard.press('Control+v')
        await asyncio.sleep(1)

        # 6. 点击提交按钮（禁止用 Control+Enter）
        send_btn = page.locator('button[data-testid="send-button"]')
        if await send_btn.is_visible() and await send_btn.is_enabled():
            await send_btn.click()
        else:
            # 备用选择器
            for sel in ['#composer-submit-button', 'button.composer-submit-button-color',
                        'button[aria-label*="Send"]', 'button:has-text("发送")']:
                btn = page.locator(sel)
                if await btn.is_visible(timeout=1000) and await btn.is_enabled(timeout=1000):
                    await btn.click()
                    break

        # 7. 确认消息发出（必须看到 user bubble）
        for _ in range(30):
            await asyncio.sleep(1)
            user_count = await page.locator('[data-message-author-role="user"]').count()
            if user_count > before_user_count:
                break

        # 8. 等待并捕获回复
        target = ''
        for _ in range(120):
            await asyncio.sleep(5)
            msgs = page.locator('[data-message-author-role="assistant"]')
            for i in range(await msgs.count()):
                txt = await msgs.nth(i).inner_text()
                if RUN_ID in txt and 'overall_judgment:' in txt and 'END_OF_GPT_RESPONSE' in txt:
                    target = txt
                    break
            if target:
                break

        # 9. 保存回复
        (REPORT_DIR / 'GPT_REVIEW_RESULT.txt').write_text(target, encoding='utf-8')

asyncio.run(main())
```

## 第四步：运行 verifier

```bash
cd "D:/agent-acceptance" && python scripts/verify_gpt_reply.py <GPT_REVIEW_RESULT.txt路径> <TASK_ID>
```

verifier 不通过（exit != 0）时，**不得**报告 verdict 为 accepted / accepted_with_limitation / closed。

## 第五步：记录审查证据

至少保存以下文件：
- `GPT_REVIEW_RESULT.txt`（GPT 原始回复，包含 run_id + overall_judgment + END_OF_GPT_RESPONSE）
- `VERIFY_GPT_REPLY_OUTPUT.txt`（verifier 输出）
- `GPT_REVIEW_SUBMISSION_STATUS.json`（提交状态，包含 sent、upload_confirmed、captured）
- `GPT_REVIEW_RECORD.json`（最终 verdict 记录，含 closure_ready）

## 已知踩坑点（不要重犯）

| 错误 | 正确做法 |
|------|----------|
| 用 `Control+Enter` 提交 | 必须点击可见提交按钮 |
| 只看 `sent=true` 就算成功 | 必须确认 user bubble 或 assistant response 出现 |
| 捕获旧 assistant message | 必须校验回复含本次 `run_id` |
| 用空白新对话做延续咨询 | 延续性咨询必须用项目文档记录的上下文对话 |
| verifier 不通过还报告 accepted | verifier 是硬门槛，不通过不能报告 verdict |
| 英文 prompt | GPT 页面交流必须中文，只保留机器字段名英文 |
| 开新 CDP 不关旧的 | 端口冲突；检查现有端口，不要重复启动 |