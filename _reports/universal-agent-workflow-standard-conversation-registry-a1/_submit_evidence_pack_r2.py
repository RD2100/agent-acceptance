#!/usr/bin/env python3
"""Upload evidence pack ZIP and resubmit R2 to GPT via CDP."""
import asyncio
import json
import sys
from pathlib import Path

try:
    from playwright.async_api import async_playwright
except ImportError:
    sys.exit(1)

TASK_DIR = Path(r"D:\agent-acceptance\_reports\universal-agent-workflow-standard-conversation-registry-a1")
CHAT_URL_FILE = TASK_DIR / "GPT_REVIEW_CHAT_URL.txt"
EVIDENCE_PACK = TASK_DIR / "EVIDENCE_PACK_R2.zip"

MSG = """这是 CONVERSATION-REGISTRY-A1 R2 的完整 Evidence Pack（ZIP 文件），包含：

- actual_deliverables/: 4个源代码文件（awsp_scaffold.py, validate_conversation_registry.py, test_conversation_registry.py, test_cross_project_scaffold.py）
- reports/: CLOSURE_REPORT_R2.md, EXECUTION_REPORT_R2.md, SAFETY_ATTESTATION_R2.md, GPT_REVIEW_PROMPT_R2.md
- reports/: TARGET_TEST_OUTPUT_R2.txt (106 passed), FULL_SUITE_OUTPUT_R2.txt (611 passed)

请检查 ZIP 中的实际代码文件，验证 R1 的 5 个 FAIL 发现是否已在 R2 中修复：

1. AWSP_VERSION 是否在所有文件中为 "1.3.0"
2. CONVERSATION_REGISTRY.schema.json 是否为真正的 JSON Schema
3. binding 模板是否包含 role 字段
4. validate_conversation_registry.py 是否加载并使用 schema 文件
5. 测试是否覆盖 role validation, schema compliance, negative cases

请基于 ZIP 中的实际代码给出正式判决。"""

async def main():
    chat_url = CHAT_URL_FILE.read_text(encoding="utf-8").strip()
    
    if not EVIDENCE_PACK.exists():
        print(f"ERROR: Evidence pack not found: {EVIDENCE_PACK}")
        sys.exit(1)
    
    print(f"Evidence pack: {EVIDENCE_PACK} ({EVIDENCE_PACK.stat().st_size:,} bytes)")
    
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://localhost:9222")
        context = browser.contexts[0] if browser.contexts else await browser.new_context()
        page = context.pages[0] if context.pages else await context.new_page()
        
        current_url = page.url
        if "chatgpt.com" not in current_url or "6a26cc03" not in current_url:
            await page.goto(chat_url, wait_until="domcontentloaded", timeout=30000)
            await asyncio.sleep(3)
        
        # Find the file upload button (paperclip icon)
        print("Looking for file upload...")
        
        # Try to find the attachment/upload button
        upload_btn = page.locator('[data-testid="file-upload-btn"], button[aria-label*="Attach"], button[aria-label*="upload"], label[for*="file"]')
        count = await upload_btn.count()
        
        if count > 0:
            # Click upload button
            await upload_btn.first.click()
            await asyncio.sleep(1)
            
            # Use file chooser
            async with page.expect_file_chooser() as fc:
                await upload_btn.first.click()
            file_chooser = await fc.value
            await file_chooser.set_files(str(EVIDENCE_PACK))
            print(f"File uploaded: {EVIDENCE_PACK.name}")
        else:
            # Try using the input[type=file] element directly
            file_input = page.locator('input[type="file"]')
            fi_count = await file_input.count()
            if fi_count > 0:
                await file_input.first.set_input_files(str(EVIDENCE_PACK))
                print(f"File set via input: {EVIDENCE_PACK.name}")
            else:
                print("WARNING: Could not find file upload mechanism. Trying drag-and-drop approach...")
                # Last resort: use the hidden file input
                await page.evaluate(f"""
                    const input = document.createElement('input');
                    input.type = 'file';
                    document.body.appendChild(input);
                    input.id = 'hidden-file-input';
                """)
                hidden = page.locator('#hidden-file-input')
                await hidden.set_input_files(str(EVIDENCE_PACK))
                print("Created hidden file input")
        
        await asyncio.sleep(2)
        
        # Type the message
        input_sel = '#prompt-textarea'
        try:
            await page.wait_for_selector(input_sel, timeout=10000)
        except:
            input_sel = 'textarea'
            await page.wait_for_selector(input_sel, timeout=10000)
        
        await page.click(input_sel)
        await asyncio.sleep(0.5)
        await page.keyboard.press("Control+a")
        await asyncio.sleep(0.2)
        await page.keyboard.press("Backspace")
        await asyncio.sleep(0.3)
        
        chunk_size = 500
        for i in range(0, len(MSG), chunk_size):
            chunk = MSG[i:i+chunk_size]
            await page.keyboard.type(chunk, delay=5)
            await asyncio.sleep(0.1)
        
        print(f"Message typed ({len(MSG)} chars)")
        await asyncio.sleep(1)
        
        # Submit
        print("Submitting with file attachment...")
        await page.keyboard.press("Enter")
        await asyncio.sleep(5)
        print("R2 evidence pack submission sent!")
        
        await browser.close()

asyncio.run(main())
