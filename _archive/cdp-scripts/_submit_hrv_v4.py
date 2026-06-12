"""Submit V3 evidence pack to GPT for EVIDENCE-CAPTURE-HOOK-FAILURE-RUNTIME-VALIDATION-A1."""
import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

GPT_URL = "https://chatgpt.com/c/6a297f76-3e7c-83a5-a0e5-b4413f923c7e"
ZIP_PATH = r"D:\agent-acceptance\_evidence\EVIDENCE_PACK_HOOK_FAILURE_RUNTIME_VALIDATION_V3.zip"

MSG = """V3 Evidence Pack — EVIDENCE-CAPTURE-HOOK-FAILURE-RUNTIME-VALIDATION-A1

请审核附件的V3证据包。本次修复了V2裁决中的5个blockers：

1. **Governance Decision Record**: test-governance advisory mode的治理决策已记录在hook-failure-semantics.md中
2. **Validator Fail-Closed**: 缺失blocking stage (sadp-audit, ai-guard) 时validator报错（absence = BLOCKED）
3. **Negative-Path Evidence in ZIP**: 8个运行时负路径场景已包含在ZIP的extra/目录中
4. **Reliable Job Exit Code**: Start-Job通过return @(output, $LASTEXITCODE)跨进程传递exit code，null默认1
5. **Cross-Process Variable Fix**: 用hashtable返回值替代$script:变量（Start-Job在独立进程运行）

关键变更：
- hooks/pre-commit.governance.ps1 v2.3.0: Job返回@(output, LASTEXITCODE)确保exit code可靠传递
- scripts/validate_hook_output.py: fail-closed语义（缺失stage=null exit_code→BLOCKED）
- scripts/run_negative_path_evidence.py: 8个场景（blocks×2, advisory×1, rejected×4, forbidden×1）
- scripts/build_evidence_pack.py: --extra-dir参数支持负路径证据入ZIP
- docs/agent-runtime/hook-failure-semantics.md: 治理决策记录+v2.3.0语义

测试结果: 1072 passed, 0 failed
负路径证据: 8/8 ALL PASS
Commit链: 6c47d327 → 7b8d9477 → f95b95c4 → 5755681d
Base: 20a4aa27 (EVIDENCE-CAPTURE-STANDARD-A1)
ZIP: 32 files, 63.2 KB, SHA-256: c52288888cccf2c0c9a482a82ee3b061b0cb70044749a4eea8f75aed0b8fcdb9
modified_tracked: 0 (clean workspace)"""


async def main():
    zip_path = Path(ZIP_PATH)
    assert zip_path.exists(), f"ZIP not found: {zip_path}"

    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://localhost:9222")
        context = browser.contexts[0]
        page = context.pages[0] if context.pages else await context.new_page()

        # Navigate to GPT conversation
        await page.goto(GPT_URL, wait_until="domcontentloaded")
        await asyncio.sleep(3)

        # Upload ZIP — the #upload-files input may be hidden; force-set files via JS
        upload_sel = "#upload-files"
        await page.wait_for_selector(upload_sel, state="attached", timeout=10000)
        # Make it visible for file input
        await page.evaluate("document.querySelector('#upload-files').style.display = 'block'")
        await page.set_input_files(upload_sel, str(zip_path))
        await asyncio.sleep(2)

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
            # Try pressing Enter
            await page.keyboard.press("Enter")
            print("Sent via Enter key")

        await asyncio.sleep(3)
        print("Submission complete. Waiting for GPT response...")


asyncio.run(main())
