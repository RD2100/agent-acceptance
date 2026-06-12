"""Submit EVIDENCE-CAPTURE-HOOK-FAILURE-SEMANTICS-A1 evidence pack to ChatGPT via CDP."""
import asyncio
from playwright.async_api import async_playwright

ZIP_PATH = r"D:\agent-acceptance\_evidence\EVIDENCE_PACK_HOOK_FAILURE_SEMANTICS_A1.zip"
TARGET_URL = "https://chatgpt.com/c/6a297e5f-c9c8-83a8-b413-a8fc414e0e85"

MESSAGE = """EVIDENCE-CAPTURE-HOOK-FAILURE-SEMANTICS-A1 证据包提交。

任务目标：验证并收紧 hook 失败行为，不改变 SADP audit 语义。

本次完成的工作：
1. 修复 schema — maxItems 3→4，enum 添加 ai-guard（之前 latest.json 每次生成都违反 schema）
2. 修复 overall_result 逻辑 — ai-guard 失败使用 PASS_WITH_WARNINGS 而非 BLOCKED（消除三元矛盾）
3. 添加 ai_guard 30s 超时保护 — Start-Job + Wait-Job，防止挂起阻塞所有 commit
4. 控制台输出消息匹配 overall_result — PASS_WITH_WARNINGS 显示 "with warnings"
5. 新建 hook-failure-semantics.md — 正式定义 stage 分类表、结果映射公式、反模式清单
6. 32 个新测试覆盖 schema 一致性、hook 脚本断言、模拟结果逻辑

变更文件（5个）：
- hooks/pre-commit.governance.ps1 (v2.1.0→v2.2.0)
- schemas/agent-runtime/evidence-capture.schema.json
- docs/agent-runtime/hook-failure-semantics.md (new)
- tests/test_hook_failure_semantics.py (new, 32 tests)
- .ai/tasks/evidence-capture-hook-failure-semantics-a1.yaml (TaskSpec)

证据包：16 文件，SHA-256: e6c09ce840908ba7b3967fa4a0e9c176f70ab0ca23ee07906930b2ef3675f54f
测试结果：1070 passed, 0 failed

请审核证据包并给出裁决。"""

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://localhost:9222")
        context = browser.contexts[0]
        page = None
        for pg in context.pages:
            if "chatgpt.com/c/" in pg.url:
                page = pg
                break
        
        if not page:
            for pg in context.pages:
                if "chatgpt.com" in pg.url:
                    page = pg
                    break
        
        if not page:
            print("ERROR: No ChatGPT page found")
            return
        
        print(f"Using page: {page.url}")
        
        # Navigate to target URL if different
        if TARGET_URL not in page.url:
            print(f"Navigating to {TARGET_URL}")
            await page.goto(TARGET_URL, wait_until="domcontentloaded", timeout=30000)
            await asyncio.sleep(3)
        
        # Check for duplicate file modal and dismiss
        try:
            modal = await page.query_selector("#modal-duplicate-file")
            if modal:
                print("Dismissing duplicate file modal...")
                btn = await page.query_selector("#modal-duplicate-file .btn-primary")
                if btn:
                    await btn.click()
                await asyncio.sleep(1)
        except:
            pass
        
        # Upload ZIP
        print(f"Uploading {ZIP_PATH}")
        upload = await page.query_selector("#upload-files")
        if upload:
            await upload.set_input_files(ZIP_PATH)
            await asyncio.sleep(2)
            print("ZIP uploaded.")
        else:
            print("ERROR: #upload-files not found")
            return
        
        # Count messages before
        msgs_before = await page.evaluate("""() => {
            return document.querySelectorAll('[data-message-author-role]').length;
        }""")
        print(f"Messages before: {msgs_before}")
        
        # Type message using keyboard
        editor = await page.query_selector('[contenteditable="true"]')
        if editor:
            await page.evaluate("""(el) => el.focus()""", editor)
            await asyncio.sleep(0.5)
            await page.keyboard.type(MESSAGE, delay=2)
            await asyncio.sleep(1)
        
        # Check send button
        send_btn = await page.query_selector('button[data-testid="send-button"]')
        if send_btn:
            disabled = await send_btn.get_attribute("disabled")
            print(f"Send button disabled: {disabled}")
            if disabled is None:
                await send_btn.click()
                print("Message sent via button click.")
            else:
                # Try Enter key
                await page.keyboard.press("Enter")
                print("Message sent via Enter key.")
        else:
            await page.keyboard.press("Enter")
            print("Send button not found, pressed Enter.")
        
        # Wait for message count to increase
        await asyncio.sleep(3)
        msgs_after = await page.evaluate("""() => {
            return document.querySelectorAll('[data-message-author-role]').length;
        }""")
        print(f"Messages after: {msgs_after}")
        
        if msgs_after > msgs_before:
            print("SUCCESS: Message count increased.")
        else:
            print("WARNING: Message count did not increase. May need manual check.")

asyncio.run(main())
