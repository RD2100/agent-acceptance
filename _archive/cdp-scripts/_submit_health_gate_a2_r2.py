"""Submit A2-R2 evidence pack to GPT for review."""
import asyncio
import json
from pathlib import Path
from playwright.async_api import async_playwright

ZIP_PATH = Path(r"D:\agent-acceptance\_evidence\EVIDENCE_PACK_CONVERSATION_HEALTH_GATE_A2_R2.zip")
CHAT_URL = "https://chatgpt.com/c/6a2a8cb1-b228-83aa-addb-79bda9aba043"

MSG = r"""请审核 CONVERSATION-HEALTH-GATE-A2 R2 证据包。

## R2 修复 (你的 4 个 Blocker)

### Blocker 1: _cdp_submit_helper fail-open → fail-closed ✅
- run_pre_gpt_gate() 的 ImportError 处理:
  - 旧: return 0, {"decision": "UNKNOWN"}, "proceeding without gate check"
  - 新: return 3, {"decision": "UNKNOWN", "severity": "BLOCKING", ...}, "BLOCKED: pre_gpt_gate unavailable"
- 新增测试: test_legacy_helper_import_failure_blocks
- 新增 evidence: legacy_helper_import_failure_blocks.txt (source code verification)

### Blocker 2: Legacy script post-response metrics refresh ✅
- _ask_next_task_v2.py 添加完整闭环:
  - CDP 交互前: run_pre_gpt_gate()
  - CDP 响应后: capture reply bytes + count + response time
  - 调用 update_metrics() 写回 current.json
  - source=cdp_dom_count, freshness=fresh
- 新增测试: test_legacy_script_post_response_updates_current_json
- 新增 evidence: legacy_script_post_response_updates_current_json.txt

### Blocker 3: Evidence 汇总表 Expected 口径修正 ✅
- stale_metrics: Expected exit=0 (not exit!=0)
- latest_json_written: Expected latest=True, snapshot=True
- metrics_refresh: Expected assistant_message_count=20
- "Actual exit:" → "Actual value:" 对于非 exit code 场景

### Blocker 4: 新增 runtime evidence ✅
- legacy_helper_import_failure_blocks.txt (10/10 PASS)
- legacy_script_post_response_updates_current_json.txt (10/10 PASS)

## Commit chain
fbb08f0 → 593d78f → 9336d56
Tests: 1128 passed (1098 A1 + 30 A2)
modified_tracked: 0
40 files, 45.4 KB
SHA-256: 9f1b20371233ddb40017dc53c5fdac30a467a7dcf0ce02ccc00edb2b99ab89f3

请核验并给出判定: ACCEPTED / NEEDS_REVISION / REJECTED。"""


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://localhost:9222")
        ctx = browser.contexts[0]
        page = ctx.pages[0]

        await page.goto(CHAT_URL, wait_until="networkidle", timeout=30000)
        await asyncio.sleep(3)

        # Upload ZIP
        file_input = page.locator("#upload-files")
        await file_input.set_input_files(str(ZIP_PATH))
        await asyncio.sleep(3)
        print("ZIP uploaded")

        # Paste message
        textarea = page.locator("#prompt-textarea")
        await textarea.click()
        await asyncio.sleep(0.5)
        await page.evaluate(f"navigator.clipboard.writeText({json.dumps(MSG)})")
        await asyncio.sleep(0.3)
        await page.keyboard.press("Control+v")
        await asyncio.sleep(1)

        # Send
        send_btn = page.locator('button[data-testid="send-button"]')
        if await send_btn.is_visible():
            await send_btn.click()
        else:
            await page.keyboard.press("Enter")
        print("R2 submitted!")
        await asyncio.sleep(5)


asyncio.run(main())
