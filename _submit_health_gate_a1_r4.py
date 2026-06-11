"""Submit R4 to GPT.

CONVERSATION-HEALTH-GATE-A2: Integrated with pre_gpt_gate.
Before any CDP interaction, the gate check runs to verify conversation health.
"""
import asyncio
import json
import sys
from pathlib import Path
from playwright.async_api import async_playwright

# A2 integration: import gate check
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _cdp_submit_helper import run_pre_gpt_gate  # noqa: E402

ZIP_PATH = Path(r"D:\agent-acceptance\_evidence\EVIDENCE_PACK_CONVERSATION_HEALTH_GATE_A1_R4.zip")
CHAT_URL = "https://chatgpt.com/c/6a2a8cb1-b228-83aa-addb-79bda9aba043"

MSG = r"""请审核 CONVERSATION-HEALTH-GATE-A1 R4 证据包。

## R4 修复 (你的 R3 两个 Blocker)

### Blocker 1: policy="info" → "warning" ✅
- check_handoff_v2() 的 no_metrics_source 分支: "info" → "warning"
- 新增测试: test_metrics_source_none_policy_is_warning
- 验证: 所有 policy 值都在 schema enum 中

### Blocker 2: CLI 字段映射 ✅
- check_handoff_v2() 内部添加字段归一化:
  last_response_time_seconds → response_time_seconds
- CLI flatten 逻辑同步添加 _field_map
- 新增测试: test_schema_compliant_last_response_time_triggers_composite
  (使用 schema 标准字段 last_response_time_seconds 触发 composite FORCE)

### 负路径证据 ✅
- run_conversation_health_evidence.py composite 场景使用 schema 标准字段
- 9/9 ALL PASS
- composite_force.txt: response_time→suggest, reply_bytes→suggest, composite→force_composite

## Commit chain
8ccb446 → 892d445 → 2b52579 → dcc31a7 → 40e4aba → fbb08f0
Tests: 1098 passed (+2 new)
modified_tracked: 0
35 files, 80.9 KB

请核验并给出最终判定。"""


async def main():
    # A2: Pre-GPT gate check before CDP interaction
    exit_code, decision, message = run_pre_gpt_gate()
    if exit_code != 0:
        print(f"GATE BLOCKED (exit {exit_code}): {message}")
        sys.exit(exit_code)
    print(f"GATE: {message}")

    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://localhost:9222")
        ctx = browser.contexts[0]
        page = ctx.pages[0]

        await page.goto(CHAT_URL, wait_until="networkidle", timeout=30000)
        await asyncio.sleep(3)

        file_input = page.locator("#upload-files")
        await file_input.set_input_files(str(ZIP_PATH))
        await asyncio.sleep(3)
        print("ZIP uploaded")

        textarea = page.locator("#prompt-textarea")
        await textarea.click()
        await asyncio.sleep(0.5)
        await page.evaluate(f"navigator.clipboard.writeText({json.dumps(MSG)})")
        await asyncio.sleep(0.3)
        await page.keyboard.press("Control+v")
        await asyncio.sleep(1)

        send_btn = page.locator('button[data-testid="send-button"]')
        if await send_btn.is_visible():
            await send_btn.click()
        else:
            await page.keyboard.press("Enter")
        print("R4 submitted!")
        await asyncio.sleep(5)

asyncio.run(main())
