#!/usr/bin/env python3
"""Submit R3 closure evidence pack to GPT via CDP with cookie handling."""
import asyncio
import json
import sys
from pathlib import Path

try:
    from playwright.async_api import async_playwright
except ImportError:
    sys.exit(1)

TASK_DIR = Path(r"D:\agent-acceptance\_reports\conversation-registry-r3-close-and-multi-agent-pilot-prep-a1")
EVIDENCE_PACK = TASK_DIR / "EVIDENCE_PACK.zip"
CHAT_URL = "https://chatgpt.com/c/6a26cc03-235c-83a2-a0fc-cd29be615959"
RUN_ID = "CONVERSATION_REGISTRY_R3_CLOSE_AND_MULTI_AGENT_PILOT_PREP_A1_20260609T191900_RD"

MSG = f"""你正在审查 CONVERSATION-REGISTRY-R3-CLOSE-AND-MULTI-AGENT-PILOT-PREP-A1 的 R3 closure evidence pack。

这是一个包含 38 个文件的 ZIP 压缩包，包含：
- actual_deliverables/: 17 个源代码和配置文件
- reports/: 21 个报告文件（CLOSURE_REPORT, EXECUTION_REPORT, SAFETY_ATTESTATION, test outputs 等）

Run ID: {RUN_ID}

请检查 ZIP 中的实际代码，重点审查：
1. Real JSON Schema（$schema, type, properties, required, enum, const）
2. Schema-backed validation
3. role 字段
4. pending_manual_binding vs active binding 策略
5. capture_policy strict true 检查
6. multi-agent pilot plan 安全性
7. 测试覆盖率

请使用以下格式给出判决：

overall_judgment: accepted | accepted_with_limitation | blocked | human_required
run_id: {RUN_ID}
findings:
  - category: ...
    severity: ...
    description: ...
next_task_authorization: ...

---END_OF_GPT_RESPONSE---"""

async def main():
    if not EVIDENCE_PACK.exists():
        print(f"ERROR: Evidence pack not found: {EVIDENCE_PACK}")
        sys.exit(1)
    
    print(f"Evidence pack: {EVIDENCE_PACK} ({EVIDENCE_PACK.stat().st_size:,} bytes)")
    
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://localhost:9222")
        context = browser.contexts[0] if browser.contexts else await browser.new_context()
        page = context.pages[0] if context.pages else await context.new_page()
        
        # Navigate to chat URL
        print(f"Navigating to chat...")
        await page.goto(CHAT_URL, wait_until="domcontentloaded", timeout=30000)
        await asyncio.sleep(5)
        
        # Handle cookie banner
        try:
            accept_btn = page.locator('button:has-text("Accept"), button:has-text("接受"), button:has-text("全部接受")')
            if await accept_btn.count() > 0:
                await accept_btn.first.click()
                print("Cookie banner accepted")
                await asyncio.sleep(2)
        except Exception as e:
            print(f"Cookie handling: {e}")
        
        # Check if we're on the chat page
        current_url = page.url
        print(f"Current URL: {current_url}")
        
        if "login" in current_url or "auth" in current_url:
            print("ERROR: Not logged in - redirected to login page")
            await browser.close()
            sys.exit(1)
        
        # Try to upload the ZIP file
        print("Looking for file upload...")
        file_input = page.locator('input[type="file"]')
        fi_count = await file_input.count()
        
        file_uploaded = False
        if fi_count > 0:
            await file_input.first.set_input_files(str(EVIDENCE_PACK))
            print(f"File uploaded via input[type=file]")
            file_uploaded = True
            await asyncio.sleep(3)
        else:
            # Try the attachment button
            try:
                attach_btn = page.locator('button[aria-label*="Attach"], button[aria-label*="attach"], button[data-testid*="attach"], button[aria-label*="file"]')
                ab_count = await attach_btn.count()
                if ab_count > 0:
                    async with page.expect_file_chooser(timeout=5000) as fc:
                        await attach_btn.first.click()
                    file_chooser = await fc.value
                    await file_chooser.set_files(str(EVIDENCE_PACK))
                    print("File uploaded via attachment button")
                    file_uploaded = True
                    await asyncio.sleep(3)
            except Exception as e:
                print(f"Attachment button approach failed: {e}")
        
        if not file_uploaded:
            print("WARNING: Could not upload file. Submitting text only with inline evidence summary.")
        
        # Type the message
        input_sel = '#prompt-textarea'
        try:
            await page.wait_for_selector(input_sel, timeout=10000)
        except:
            input_sel = 'textarea, [contenteditable="true"]'
            try:
                await page.wait_for_selector(input_sel, timeout=10000)
            except:
                print("ERROR: Could not find input area")
                await browser.close()
                sys.exit(1)
        
        await page.click(input_sel)
        await asyncio.sleep(0.5)
        await page.keyboard.press("Control+a")
        await asyncio.sleep(0.2)
        await page.keyboard.press("Backspace")
        await asyncio.sleep(0.3)
        
        # Type message in chunks
        chunk_size = 500
        for i in range(0, len(MSG), chunk_size):
            chunk = MSG[i:i+chunk_size]
            await page.keyboard.type(chunk, delay=5)
            await asyncio.sleep(0.1)
        
        print(f"Message typed ({len(MSG)} chars)")
        await asyncio.sleep(1)
        
        # Submit
        print("Submitting...")
        await page.keyboard.press("Enter")
        await asyncio.sleep(5)
        print("R3 closure evidence pack submitted to GPT!")
        
        # Save status
        status = {
            "submitted": True,
            "chat_url": CHAT_URL,
            "current_url": current_url,
            "file_uploaded": file_uploaded,
            "evidence_pack_size": EVIDENCE_PACK.stat().st_size,
            "message_length": len(MSG),
            "method": "playwright_cdp",
            "round": "R3-closure",
            "run_id": RUN_ID
        }
        status_file = TASK_DIR / "GPT_REVIEW_SUBMISSION_STATUS.json"
        status_file.write_text(json.dumps(status, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"Status saved: {status_file}")
        
        await browser.close()

asyncio.run(main())
