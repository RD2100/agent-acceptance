"""Submit A2-R3 evidence pack to GPT."""
import asyncio
import json
from pathlib import Path
from playwright.async_api import async_playwright

ZIP_PATH = Path(r"D:\agent-acceptance\_evidence\EVIDENCE_PACK_CONVERSATION_HEALTH_GATE_A2_R3.zip")
CHAT_URL = "https://chatgpt.com/c/6a2a8cb1-b228-83aa-addb-79bda9aba043"

MSG = r"""请审核 CONVERSATION-HEALTH-GATE-A2 R3 证据包。

## R3 修复 (你的 3 个 Blocker)

### Blocker 1: modified_tracked=2 → 0 ✅
- 提交后恢复 _evidence/conversation-health/latest.json + current-snapshot.json
- git-status-after 显示 modified_tracked: 0
- review.yaml / final-report / safety-report 全部一致

### Blocker 2: review.md / final-report.md summary 表修正 ✅
- build_evidence_pack.py 解析器升级:
  - 支持 "# Actual exit:" 和 "# Actual value:" 两种格式
  - Expected 列直接使用原始文本，不再硬编码 exit!=0
- 修正后的 10 个场景表:
  | force_handoff | exit_code=1 | exit=1 |
  | human_required | exit_code=2 | exit=2 |
  | latest_json_written | latest.json AND snapshot exists | latest=True, snapshot=True |
  | legacy_helper_import_failure | return 3, severity=BLOCKING | return_3=True, blocking=True |
  | legacy_post_response | msgs=15, bytes=3200, source=cdp | msgs=15, bytes=3200, source=cdp |
  | missing_current_json | exit_code=3 | exit=3 |
  | stale_metrics | exit_code=0 | exit=0 |
  | metrics_refresh | assistant_message_count=20 | 20 |

### Blocker 3: post-response import 路径修复 ✅
- _ask_next_task_v2.py: 使用 sys.path 注入 scripts/ 目录
  (与 _cdp_submit_helper.py 相同模式)
- ImportError 不再只 print warning:
  写入 _evidence/conversation-health/metrics_refresh_failed.json
  包含 decision=UNKNOWN, severity=WARNING, code=post_response_refresh_failed

## Commit chain
fbb08f0 → 593d78f → 9336d56 → be0491f
Tests: 1128 passed
modified_tracked: 0
40 files, 44.1 KB
SHA-256: ff561bc7c06739b9cd85de52513fbcd35de275a8677ba25140323f2ee207aafc

请核验并给出判定: ACCEPTED / NEEDS_REVISION / REJECTED。"""


async def main():
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
        print("R3 submitted!")
        await asyncio.sleep(5)


asyncio.run(main())
