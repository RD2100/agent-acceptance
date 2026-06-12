"""Submit V4 evidence pack to GPT."""
import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

CONVO_URL = "https://chatgpt.com/c/6a2a8cb1-b228-83aa-addb-79bda9aba043"
ZIP_PATH = r"D:\agent-acceptance\_evidence\EVIDENCE_PACK_HOOK_FAILURE_RUNTIME_VALIDATION_V4.zip"

MSG = """V4 Evidence Pack — EVIDENCE-CAPTURE-HOOK-FAILURE-RUNTIME-VALIDATION-A1

请审核附件的V4证据包。本次修复了V3(1)裁决中的4个blockers：

Blocker 1 (Stale evidence): 清空了_evidence/runtime-negative-path-evidence/目录并重新生成。
ZIP extra/ 现在只有8个场景文件 + 1个combined，不再有 test_governance_failure_blocks.txt。

Blocker 2 (Expected text): 修复了run_negative_path_evidence.py的Expected文案逻辑：
- blocks场景: "0 (correct semantics — blocking stage failure → BLOCKED)"
- advisory场景: "0 (advisory semantics — failure logged but not blocking)"
- rejected场景: "nonzero (mismatch/invalid input rejected by validator)"

Blocker 3 (Doc conflicts):
- evidence-capture-workflow.md: "Blocking stages: sadp-audit, ai-guard" + "Advisory stages: manifest-regen, test-governance"
- test_hook_failure_semantics.py: docstring和class注释全部同步为v2.3.0语义
- hook-failure-semantics.md: 新增"Null Exit Code Semantics"章节

Blocker 4 (null/schema semantics):
- Schema exit_code type改为 ["integer", "null"]，描述null语义
- Validator: null在blocking stage = BLOCKED expected
- Hook: null默认1 (fail-closed)
- 文档: hook-failure-semantics.md记录了完整的null语义规则

测试结果: 1072 passed, 0 failed
负路径证据: 8/8 ALL PASS (无残留文件)
Commit链: 6c47d327 → 7b8d9477 → f95b95c4 → 5755681d → d7b294d
Base: 20a4aa27
ZIP: 33 files, 67.1 KB
SHA-256: ddbb798840d23e6d30963404b74560bcc2dc436f5b5851998c11d78620b5a61a
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
