"""Submit CONVERSATION-HEALTH-GATE-A1 R3 to GPT."""
import asyncio
import json
from pathlib import Path
from playwright.async_api import async_playwright

REPO = Path(r"D:\agent-acceptance")
ZIP_PATH = REPO / "_evidence" / "EVIDENCE_PACK_CONVERSATION_HEALTH_GATE_A1_R3.zip"
CHAT_URL = "https://chatgpt.com/c/6a2a8cb1-b228-83aa-addb-79bda9aba043"

MSG = r"""请审核 CONVERSATION-HEALTH-GATE-A1 R3 证据包。

## R3 修复: 重新生成负路径证据 (你的最后一个 Blocker)

R2 中你指出的核心问题是：extra/ 中的负路径证据是旧语义生成的，与修复后的代码不一致。

R3 修复 (commit 40e4aba):
- 用修复后的代码重新运行 run_conversation_health_evidence.py
- composite_force.txt 现在显示:
  - response_time_elevated → policy: "suggest" (不再是 "force")
  - last_gpt_reply_bytes_low → policy: "suggest" (不再是 "force")
  - composite_degradation → policy: "force_composite" (组合才FORCE)
- 9/9 scenarios ALL PASS

## 完整 commit chain
8ccb446 → 892d445 (feat) → 2b52579 (fix R2) → dcc31a7 (fix parser) → 40e4aba (fix R3 evidence)
Tests: 1096 passed
modified_tracked: 0

## 证据包
33 files, 76.8 KB
SHA-256: 051601543992755a62b590a7c9a6f4d3a3e42cd722939014feb8c6f162ea8488
conversation-health/latest.json included

请逐项核验并给出最终判定。"""


async def main():
    print(f"=== Submit R3 ===")
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
        print("Message sent!")
        await asyncio.sleep(5)
        print("=== R3 Submit complete ===")


if __name__ == "__main__":
    asyncio.run(main())
