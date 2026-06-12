"""Submit CONVERSATION-HEALTH-GATE-A1 evidence pack to GPT for review.
Uses clipboard paste (not keyboard.type) per user's explicit feedback.
"""
import asyncio
import json
import sys
from pathlib import Path
from playwright.async_api import async_playwright

REPO = Path(r"D:\agent-acceptance")
ZIP_PATH = REPO / "_evidence" / "EVIDENCE_PACK_CONVERSATION_HEALTH_GATE_A1.zip"
CHAT_URL = "https://chatgpt.com/c/6a2a8cb1-b228-83aa-addb-79bda9aba043"

MSG = r"""请审核 CONVERSATION-HEALTH-GATE-A1 证据包。

## 任务概要
实现主动式对话健康强制执行机制——四层防御模型：
- **C层**: Pre-Task Hard Gate（FORCE_HANDOFF 阻断任务启动）
- **B'层**: Pre-GPT Gate（A2范围，本次未实现）
- **Evidence Pack**: 必须包含 conversation-health/latest.json
- **A层**: Pre-Commit Advisory（A3范围，本次未实现）

## A1 交付物 (commit 892d445)
1. **数据层**: JSON Schema × 2 + Policy YAML + current.json.example
2. **决策引擎**: check_handoff_needed.py v2 — 完整 CLI (--input --write --fail-on-force --mode --composite --json)
3. **Pre-Task集成**: sadp_pre_task_enforcer.py 新增 step 7 (_check_conversation_health)
4. **Evidence Pack集成**: build_evidence_pack.py 新增 conversation_health section
5. **文档**: conversation-health-gate.md (242行)
6. **测试**: 21个单元测试 + 9个负面路径场景

## 阈值策略 (conversation-health-policy.yaml)
- **FORCE**: msg_count>=60, response_time>=60s, rounds>=3, reply_bytes<2000
- **SUGGEST**: msg_count>=45, response_time>=40s
- **Composite**: slow+short+rounds → FORCE
- **Nav**: access_denied→FORCE, auth_required→HUMAN_REQUIRED
- **metrics_source可信度**: cdp_dom_count > wrapper_counter > manual_estimate

## 测试结果
- 1093 tests passed (全量回归)
- 9/9 negative-path evidence ALL PASS
- 场景: missing_file(0), stale(0), msg_count_force(1), rounds_force(1), access_denied(1), auth_required(1), invalid_json(2), manual_estimate_no_force(0), composite_force(1)

## 证据包 (26 files, 65.7 KB)
SHA-256: 409c75379b1ad448bbf439bf58132f056c4525fe0132ebe380b4664ada586cfb
包含: diff.patch, git-show, test-output, secret-scan, 10个负面路径文件, review.yaml

请审核并给出判定：ACCEPTED / REJECTED / NEEDS_REVISION"""


async def main():
    print(f"=== CDP Submit: CONVERSATION-HEALTH-GATE-A1 ===")
    print(f"ZIP: {ZIP_PATH.name}")
    print(f"URL: {CHAT_URL}")
    print(f"MSG length: {len(MSG)} chars")
    print()

    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://localhost:9222")
        context = browser.contexts[0]
        page = context.pages[0]

        # Navigate to the conversation
        print("[1] Navigating to ChatGPT conversation...")
        await page.goto(CHAT_URL, wait_until="networkidle", timeout=30000)
        await asyncio.sleep(3)
        print(f"    Current URL: {page.url}")

        # Upload the evidence pack ZIP
        print("[2] Uploading evidence pack ZIP...")
        file_input = page.locator("#upload-files")
        if await file_input.count() > 0:
            await file_input.set_input_files(str(ZIP_PATH))
            print(f"    Uploaded: {ZIP_PATH.name}")
            await asyncio.sleep(3)
        else:
            # Try the paperclip/attach button approach
            print("    #upload-files not found, trying attach button...")
            attach_btn = page.locator('button[aria-label*="Attach"]').first
            if await attach_btn.is_visible():
                await attach_btn.click()
                await asyncio.sleep(1)
                file_input = page.locator('input[type="file"]')
                await file_input.set_input_files(str(ZIP_PATH))
                await asyncio.sleep(3)
            else:
                print("    WARNING: Could not find file upload mechanism")

        # Paste message using clipboard
        print("[3] Pasting message via clipboard...")
        textarea = page.locator("#prompt-textarea")
        await textarea.click()
        await asyncio.sleep(0.5)

        # Write to clipboard and paste
        await page.evaluate(f"navigator.clipboard.writeText({json.dumps(MSG)})")
        await asyncio.sleep(0.3)
        await page.keyboard.press("Control+v")
        await asyncio.sleep(1)
        print(f"    Message pasted ({len(MSG)} chars)")

        # Send via button
        print("[4] Sending message...")
        send_btn = page.locator('button[data-testid="send-button"]')
        if await send_btn.is_visible():
            await send_btn.click()
            print("    Sent via send button!")
        else:
            # Try alternative selectors
            send_btn2 = page.locator('button[aria-label="Send message"]')
            if await send_btn2.is_visible():
                await send_btn2.click()
                print("    Sent via aria-label button!")
            else:
                await page.keyboard.press("Enter")
                print("    Sent via Enter key!")

        await asyncio.sleep(5)
        print("[5] Message submitted. Waiting for GPT response...")

        # Wait for response to start appearing
        await asyncio.sleep(10)
        print(f"    Final URL: {page.url}")
        print("=== Submit complete ===")


if __name__ == "__main__":
    asyncio.run(main())
