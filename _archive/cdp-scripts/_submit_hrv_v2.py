"""Submit blocker-fix evidence pack to GPT."""
import asyncio
from playwright.async_api import async_playwright

ZIP_PATH = r"D:\agent-acceptance\_evidence\EVIDENCE_PACK_HOOK_FAILURE_RUNTIME_VALIDATION_V2.zip"
TARGET_URL = "https://chatgpt.com/c/6a297f76-3e7c-83a5-a0e5-b4413d923c7e"

MESSAGE = """BLOCKER-FIX 证据包提交 (EVIDENCE-CAPTURE-HOOK-FAILURE-RUNTIME-VALIDATION-A1 V2)

修复了上一轮裁决中的 5 个 blocker:

BLOCKING-01 [FIXED]: validate_hook_output.py 更新为 v2.3.0 语义
  - ai_guard/test_governance 失败 → BLOCKED (移除 PASS_WITH_WARNINGS)
  - 语义不匹配 → validator exits 1 (fail-closed)

BLOCKING-02 [FIXED]: diff.patch 范围精确匹配
  - 仅含 f95b95c 单个 commit
  - diff.patch paths 与 git-show-f95b95c.txt 完全一致 (8 files)

BLOCKING-03 [FIXED]: modified_tracked = 0
  - 已 stash scripts/gpt_new_chat_attachment_submit.py

BLOCKING-04 [FIXED]: 负路径 runtime 证据
  - scripts/run_negative_path_evidence.py 生成 6 个 fixture:
    [1] sadp_audit failure → BLOCKED: validator exit=0 (正确语义)
    [2] ai_guard failure → BLOCKED: validator exit=0 (正确语义)
    [3] test_governance failure → PASS: validator exit=0 (advisory)
    [4] ai_guard failure + result=PASS → REJECTED: validator exit=1
    [5] PASS_WITH_WARNINGS → REJECTED: validator exit=1 (v2.3.0 禁止)
    [6] Invalid JSON → REJECTED: validator exit=1

BLOCKING-05 [FIXED]: ai_guard exit code 可靠捕获
  - 使用 $Job.ChildJobs[0].ExitCode (null-safe)
  - 移除了输出正则 heuristic

补充说明: test-governance 保持 advisory 模式 (以 -Mode advisory 调用),
因为修改 Test-Governance.ps1 不在本任务范围内。
sadp-audit + ai-guard 为 blocking gates。

证据包: 16 files, SHA-256: 26b3b278afa2cff9be7c28d3320b241c7192ede67afcdc9cbbef65c37c028346
测试: 1072 passed, 0 failed

请审核并给出裁决。"""

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://localhost:9222")
        context = browser.contexts[0]
        page = None
        for pg in context.pages:
            if "chatgpt.com" in pg.url:
                page = pg
                break
        if not page:
            print("ERROR: No ChatGPT page found")
            return

        if TARGET_URL not in page.url:
            print(f"Navigating to {TARGET_URL}")
            await page.goto(TARGET_URL, wait_until="domcontentloaded", timeout=30000)
            await asyncio.sleep(3)

        print(f"Using page: {page.url}")

        msgs_before = await page.evaluate("() => document.querySelectorAll('[data-message-author-role]').length")
        print(f"Messages before: {msgs_before}")

        upload = await page.query_selector("#upload-files")
        if upload:
            await upload.set_input_files(ZIP_PATH)
            await asyncio.sleep(3)
            print("ZIP uploaded.")

        editor = await page.query_selector('[contenteditable="true"]')
        if editor:
            await editor.click()
            await asyncio.sleep(0.5)
            await page.evaluate("(el) => { el.focus(); el.textContent = ''; }", editor)
            await asyncio.sleep(0.3)
            await page.keyboard.type(MESSAGE, delay=2)
            await asyncio.sleep(2)

        send_btn = await page.query_selector('button[data-testid="send-button"]')
        if send_btn:
            disabled = await send_btn.get_attribute("disabled")
            print(f"Send button disabled: {repr(disabled)}")
            if disabled is None:
                await send_btn.click()
                print("Clicked send.")
            else:
                await page.keyboard.press("Enter")
                print("Sent via Enter.")

        await asyncio.sleep(5)
        msgs_after = await page.evaluate("() => document.querySelectorAll('[data-message-author-role]').length")
        print(f"Messages after: {msgs_after}")
        if msgs_after > msgs_before:
            print("SUCCESS!")

asyncio.run(main())
