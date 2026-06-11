"""Submit A2 evidence pack to GPT for review."""
import asyncio
import json
from pathlib import Path
from playwright.async_api import async_playwright

ZIP_PATH = Path(r"D:\agent-acceptance\_evidence\EVIDENCE_PACK_CONVERSATION_HEALTH_GATE_A2.zip")
CHAT_URL = "https://chatgpt.com/c/6a2a8cb1-b228-83aa-addb-79bda9aba043"

MSG = r"""请审核 CONVERSATION-HEALTH-GATE-A2 证据包。

## A2 交付内容

### 核心: scripts/pre_gpt_gate.py (新建)
- check_pre_gpt_gate(): Pre-Submit 门禁检查
  - 读取 current.json → check_handoff_v2(mode="pre-gpt") → 写 latest.json + snapshot.json
  - OK/SUGGEST → exit 0 (允许提交)
  - FORCE_HANDOFF → exit 1 (阻断)
  - HUMAN_REQUIRED → exit 2 (阻断, 需人工)
  - Missing current.json → exit 3 (阻断, 除非 allow_init)
- update_metrics(): 刷新 current.json 的 CDP metrics
- record_nav_result(): 记录导航失败并重新评估
- capture_cdp_metrics(): 异步 CDP DOM 抓取
- CLI: check, refresh, gate, nav-result 四个子命令

### Legacy 集成 (3个脚本)
- _cdp_submit_helper.py: 添加 run_pre_gpt_gate() 集成函数
- _submit_health_gate_a1_r4.py: 提交前调用 gate check
- _capture_r4_verdict.py: 捕获前调用 gate check
- _ask_next_task_v2.py: 询问前调用 gate check

### Evidence Pack 增强
- current-snapshot.json: 时间点快照
- pre-gpt-gate-evidence/: 8个负路径场景证据

### 测试 (28个新测试)
- OK/SUGGEST/FORCE/HUMAN_REQUIRED 场景
- Missing/Stale current.json
- Navigation result recording
- Metrics update schema compliance
- latest.json schema compliance
- A1 non-regression (5个测试)

### A1 语义保持
- response_time alone → SUGGEST ✅
- reply_bytes alone → SUGGEST ✅
- slow+short+rounds → FORCE ✅
- manual_estimate no force ✅
- auth_required → HUMAN_REQUIRED ✅

## Commit chain
fbb08f0 → 593d78f
Tests: 1126 passed (1098 A1 + 28 A2)
modified_tracked: 0
36 files, 68.0 KB
SHA-256: d1ee7e462f2ic593e8d6dc930dc9f7cb86ce2653ccf2a48997951803ded8652b

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
        print("A2 submitted!")
        await asyncio.sleep(5)


asyncio.run(main())
