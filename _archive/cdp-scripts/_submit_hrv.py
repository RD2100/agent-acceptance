"""Submit EVIDENCE-CAPTURE-HOOK-FAILURE-RUNTIME-VALIDATION-A1 to correct GPT conversation."""
import asyncio
from playwright.async_api import async_playwright

ZIP_PATH = r"D:\agent-acceptance\_evidence\EVIDENCE_PACK_HOOK_FAILURE_RUNTIME_VALIDATION_A1.zip"
TARGET_URL = "https://chatgpt.com/c/6a297f76-3e7c-83a5-a0e5-b4413d923c7e"

MESSAGE = """EVIDENCE-CAPTURE-HOOK-FAILURE-RUNTIME-VALIDATION-A1 证据包提交。

任务目标：基于 EVIDENCE-CAPTURE-HOOK-FAILURE-SEMANTICS-A1 的 accepted_with_limitation 裁决，补强 runtime validation。

本次完成的工作：
1. Hook v2.2.0→v2.3.0：所有 required stage (sadp-audit, ai-guard, test-governance) 改为 BLOCKING
   - 移除了 PASS_WITH_WARNINGS，简化为 PASS 或 BLOCKED
   - ai_guard 失败 → overall_result=BLOCKED + exit 1
   - test_governance 失败 → overall_result=BLOCKED + exit 1
   - manifest-regen 保持 advisory
2. 新增 scripts/validate_hook_output.py — schema + 语义验证
   - 验证 latest.json 符合 evidence-capture.schema.json
   - 检查 blocking stage exit code 与 overall_result 一致性
3. 34 个测试覆盖完整 blocking 语义：
   - sadp_audit_exit_1_blocks, ai_guard_exit_1_blocks, test_governance_exit_1_blocks
   - all_exit_0_passes, manifest_regen_advisory
   - latest_json_schema_validation_passes_for_valid_output
   - invalid_latest_json_blocks, replay evidence labeling
4. 文档更新：hook-failure-semantics.md (v2.3.0), evidence-capture-workflow.md (section 8)
5. Schema 更新：overall_result enum 简化为 [PASS, BLOCKED]

变更文件（8个）：hook, schema, validator, tests, 2 docs, TaskSpec, current-task
证据包：16 文件, SHA-256: 547e628d9c43b490a61e7d11c9c500d4dbb9808ab420d77b67b10f8ca027a674
测试结果：1072 passed, 0 failed

请审核证据包并给出裁决。"""

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

        # Navigate to target URL
        if TARGET_URL not in page.url:
            print(f"Navigating to {TARGET_URL}")
            await page.goto(TARGET_URL, wait_until="domcontentloaded", timeout=30000)
            await asyncio.sleep(3)

        print(f"Using page: {page.url}")

        # Count messages before
        msgs_before = await page.evaluate("""() => {
            return document.querySelectorAll('[data-message-author-role]').length;
        }""")
        print(f"Messages before: {msgs_before}")

        # Upload ZIP
        print(f"Uploading {ZIP_PATH}")
        upload = await page.query_selector("#upload-files")
        if upload:
            await upload.set_input_files(ZIP_PATH)
            await asyncio.sleep(3)
            print("ZIP uploaded.")
        else:
            print("ERROR: #upload-files not found")
            return

        # Focus editor and type
        editor = await page.query_selector('[contenteditable="true"]')
        if editor:
            await editor.click()
            await asyncio.sleep(0.5)
            await page.evaluate("""(el) => { el.focus(); el.textContent = ''; }""", editor)
            await asyncio.sleep(0.3)
            print("Typing message...")
            await page.keyboard.type(MESSAGE, delay=3)
            await asyncio.sleep(2)

        # Check send button
        send_btn = await page.query_selector('button[data-testid="send-button"]')
        if send_btn:
            disabled = await send_btn.get_attribute("disabled")
            print(f"Send button disabled: {repr(disabled)}")
            if disabled is None:
                await send_btn.click()
                print("Clicked send button.")
            else:
                await page.keyboard.press("Enter")
                print("Sent via Enter.")
        else:
            await page.keyboard.press("Enter")

        # Wait
        await asyncio.sleep(5)
        msgs_after = await page.evaluate("""() => {
            return document.querySelectorAll('[data-message-author-role]').length;
        }""")
        print(f"Messages after: {msgs_after}")

        if msgs_after > msgs_before:
            print("SUCCESS: Message count increased!")
        else:
            print("WARNING: Message count unchanged.")

asyncio.run(main())
