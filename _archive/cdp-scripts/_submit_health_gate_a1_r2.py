"""Submit CONVERSATION-HEALTH-GATE-A1 R2 to GPT for review."""
import asyncio
import json
from pathlib import Path
from playwright.async_api import async_playwright

REPO = Path(r"D:\agent-acceptance")
ZIP_PATH = REPO / "_evidence" / "EVIDENCE_PACK_CONVERSATION_HEALTH_GATE_A1_R2.zip"
CHAT_URL = "https://chatgpt.com/c/6a2a8cb1-b228-83aa-addb-79bda9aba043"

MSG = r"""请审核 CONVERSATION-HEALTH-GATE-A1 R2 证据包。

## R2 修复清单 (逐项回应你的 5 个 Blocker)

### Blocker 1: Evidence Pack hard requirement ✅
- 已生成 `_evidence/conversation-health/latest.json` (schema_version, decision, metrics 全部填充)
- `build_evidence_pack.py` 缺失时标记 `verdict_eligibility: needs_more_evidence` + `hard_requirement: true`
- ZIP 中已包含 `conversation-health/latest.json`
- review.yaml 中 conversation_health.checked: true, verdict_eligibility: eligible

### Blocker 2: 阈值语义修正 ✅
- `response_time_seconds >= 60` 单独触发 → SUGGEST (不再 FORCE)
- `last_gpt_reply_bytes < 2000` 单独触发 → SUGGEST (不再 FORCE)
- 仅 Composite (slow + short + rounds) → FORCE
- 修改了: DEFAULT_POLICY, check_handoff_v2(), check_handoff(), policy YAML, docstring
- 新增测试: test_response_time_only_is_suggest, test_reply_bytes_only_is_suggest

### Blocker 3: decision schema enum ✅
- policy enum 扩展为: ["force", "suggest", "force_composite", "human", "suggest_capped", "warning"]
- 覆盖代码所有实际输出值
- 新增测试: test_policy_enum_covers_all_code_outputs

### Blocker 4: 负路径汇总表修正 ✅
- 汇总表从文件内容解析 Expected/Actual exit code (不再硬编码)
- 区分 9 scenario files + 1 combined file
- 表格新增 Actual 列

### Blocker 5: post-commit modified tracked ✅
- 已 revert 无关的 cleanup-a1.yaml 修改
- 当前 modified_tracked: 0

## 提交范围
Commits: 892d445 → 2b52579 → dcc31a7
Base: 8ccb446
Tests: 1096 passed (+3 新测试)

## 证据包
SHA-256: e5d6714b98e236b0dbaf0cceda1854e8596b6274f1fc4619ef5c0ae7a1353ca9
31 files, 74.1 KB, conversation-health/latest.json included

请审核并给出判定。"""


async def main():
    print(f"=== CDP Submit: CONVERSATION-HEALTH-GATE-A1 R2 ===")
    print(f"ZIP: {ZIP_PATH.name} ({ZIP_PATH.stat().st_size} bytes)")
    print(f"URL: {CHAT_URL}")
    print(f"MSG: {len(MSG)} chars")

    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://localhost:9222")
        context = browser.contexts[0]
        page = context.pages[0]

        print("[1] Navigating...")
        await page.goto(CHAT_URL, wait_until="networkidle", timeout=30000)
        await asyncio.sleep(3)
        print(f"    URL: {page.url}")

        print("[2] Uploading ZIP...")
        file_input = page.locator("#upload-files")
        await file_input.set_input_files(str(ZIP_PATH))
        await asyncio.sleep(3)
        print(f"    Uploaded: {ZIP_PATH.name}")

        print("[3] Pasting message via clipboard...")
        textarea = page.locator("#prompt-textarea")
        await textarea.click()
        await asyncio.sleep(0.5)
        await page.evaluate(f"navigator.clipboard.writeText({json.dumps(MSG)})")
        await asyncio.sleep(0.3)
        await page.keyboard.press("Control+v")
        await asyncio.sleep(1)
        print(f"    Pasted {len(MSG)} chars")

        print("[4] Sending...")
        send_btn = page.locator('button[data-testid="send-button"]')
        if await send_btn.is_visible():
            await send_btn.click()
            print("    Sent via button!")
        else:
            await page.keyboard.press("Enter")
            print("    Sent via Enter!")

        await asyncio.sleep(5)
        print("=== Submit complete ===")


if __name__ == "__main__":
    asyncio.run(main())
