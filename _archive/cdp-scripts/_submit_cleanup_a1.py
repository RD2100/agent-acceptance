"""Submit CLEANUP-A1 evidence pack to GPT for review."""
import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

CONVO_URL = "https://chatgpt.com/c/6a2a8cb1-b228-83aa-addb-79bda9aba043"
ZIP_PATH = r"D:\agent-acceptance\_evidence\EVIDENCE_PACK_HOOK_FAILURE_RUNTIME_VALIDATION_CLEANUP_A1.zip"

MSG = """CLEANUP-A1 Evidence Pack — EVIDENCE-CAPTURE-HOOK-FAILURE-RUNTIME-VALIDATION-CLEANUP-A1

请审核附件的CLEANUP-A1证据包。此任务处理V5裁决中的3个minor limitations：

V5 Verdict: ACCEPTED_WITH_MINOR_LIMITATIONS (3 items)

修复内容：
1. 旧TaskSpec goal text更新 — 明确"validate PASS_WITH_WARNINGS is rejected in v2.3.0"
2. review.md和final-report.md增加Runtime Negative-Path Evidence汇总表（9 scenarios + Expected + Result列）
3. validate_hook_output.py docstring声明为bounded manual validator（明确不实现$ref/allOf等高级JSON Schema keywords）

Commit: 8ccb446 (on top of V5: 804ae3b)
Base: 804ae3b
测试结果: 1072 passed, 0 failed
负路径证据: 9/9 ALL PASS (extra/ 目录10个文件)
ZIP: 26 files, 21.9 KB
SHA-256: 25b0a887eda8def4e60180f1235fdcc1a65e4b925ff167968085124f715f8e1f

完整commit链:
6c47d327 feat: EVIDENCE-CAPTURE-HOOK-FAILURE-SEMANTICS-A1
7b8d9477 feat: EVIDENCE-CAPTURE-HOOK-FAILURE-RUNTIME-VALIDATION-A1
f95b95c4 fix: resolve 5 GPT blockers
5755681d fix: V3 blocker fixes — reliable Job exit code
d7b294dc fix: V4 — resolve 4 GPT blockers
804ae3b9 fix: V5 — validator/schema consistency
8ccb4460 chore: CLEANUP-A1 — fix 3 minor limitations from V5 GPT verdict

请裁决：ACCEPTED / ACCEPTED_WITH_MINOR_LIMITATIONS / REJECTED"""


async def main():
    zip_path = Path(ZIP_PATH)
    assert zip_path.exists(), f"ZIP not found: {zip_path}"

    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://localhost:9222")
        context = browser.contexts[0]
        page = context.pages[0] if context.pages else await context.new_page()

        await page.goto(CONVO_URL, wait_until="domcontentloaded")
        await asyncio.sleep(5)
        print(f"URL: {page.url}")

        # Upload ZIP
        await page.evaluate("document.querySelector('#upload-files').style.display = 'block'")
        await page.set_input_files("#upload-files", str(zip_path))
        await asyncio.sleep(3)
        print("File uploaded")

        # Type message
        textarea = page.locator("#prompt-textarea")
        await textarea.click()
        await asyncio.sleep(0.5)
        await page.keyboard.type(MSG, delay=2)
        await asyncio.sleep(1)

        # Send
        send_btn = page.locator('button[data-testid="send-button"]')
        if await send_btn.is_visible():
            await send_btn.click()
            print("Message sent!")
        else:
            await page.keyboard.press("Enter")
            print("Sent via Enter")

        await asyncio.sleep(3)
        print("Submission complete.")


asyncio.run(main())
