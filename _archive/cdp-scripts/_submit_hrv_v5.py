"""Submit V5 evidence pack to GPT."""
import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

CONVO_URL = "https://chatgpt.com/c/6a2a8cb1-b228-83aa-addb-79bda9aba043"
ZIP_PATH = r"D:\agent-acceptance\_evidence\EVIDENCE_PACK_HOOK_FAILURE_RUNTIME_VALIDATION_V5.zip"

MSG = """V5 Evidence Pack — EVIDENCE-CAPTURE-HOOK-FAILURE-RUNTIME-VALIDATION-A1

请审核附件的V5证据包。本次修复了V4裁决中的blockers：

新 Blocker (validator/schema consistency):
1. Schema output_file type改为 ["string", "null"]（hook实际输出null给manifest-regen）
2. Validator增加了output_file类型校验（string or null，其他类型报错）
3. 所有fixture与schema完全一致，validator的"PASS"现在可信

Minor evidence gap:
4. 新增test 9: missing_ai_guard_rejected（与missing_sadp_audit成对，证明两个blocking stage的absence fail-closed）
5. 9个负路径场景 + combined（10个文件在extra/目录）

Doc cleanup:
6. 删除evidence-capture-workflow.md中重复的advisory bullet

测试结果: 1072 passed, 0 failed
负路径证据: 9/9 ALL PASS
Commit链: 6c47d327 → 7b8d9477 → f95b95c4 → 5755681d → d7b294d → 804ae3b
Base: 20a4aa27
ZIP: 36 files, 70.8 KB
SHA-256: 1c55067d9ec863fcf2758449b857421aacbea161f917569dafd387e1de768651
modified_tracked: 0"""


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

        await page.evaluate("document.querySelector('#upload-files').style.display = 'block'")
        await page.set_input_files("#upload-files", str(zip_path))
        await asyncio.sleep(3)
        print("File uploaded")

        textarea = page.locator("#prompt-textarea")
        await textarea.click()
        await asyncio.sleep(0.5)
        await page.keyboard.type(MSG, delay=2)
        await asyncio.sleep(1)

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
