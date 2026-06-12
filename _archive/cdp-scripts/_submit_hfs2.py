"""Retry submission with more robust input method."""
import asyncio
from playwright.async_api import async_playwright

ZIP_PATH = r"D:\agent-acceptance\_evidence\EVIDENCE_PACK_HOOK_FAILURE_SEMANTICS_A1.zip"
TARGET_URL = "https://chatgpt.com/c/6a297e5f-c9c8-83a8-b413-a8fc414e0e85"

MESSAGE = """EVIDENCE-CAPTURE-HOOK-FAILURE-SEMANTICS-A1 证据包提交。

任务目标：验证并收紧 hook 失败行为，不改变 SADP audit 语义。

完成工作：
1. 修复 schema — maxItems 3→4，enum 添加 ai-guard
2. 修复 overall_result — ai-guard 失败用 PASS_WITH_WARNINGS
3. 添加 ai_guard 30s 超时保护 (Start-Job)
4. 控制台消息匹配 overall_result
5. 新建 hook-failure-semantics.md
6. 32 个新测试

变更：5 文件，1070 tests passed
ZIP: 16 files, SHA-256: e6c09ce840908ba7b3967fa4a0e9c176f70ab0ca23ee07906930b2ef3675f54f

请审核证据包并给出裁决。"""

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://localhost:9222")
        context = browser.contexts[0]
        page = None
        for pg in context.pages:
            if "chatgpt.com/c/" in pg.url:
                page = pg
                break
        
        if not page:
            print("ERROR: No ChatGPT conversation page found")
            return
        
        print(f"Using page: {page.url}")
        
        # Wait for page to be fully loaded
        await asyncio.sleep(2)
        
        # Check if ZIP was already uploaded from previous attempt
        # Look for file attachment indicators
        attachments = await page.query_selector_all('[data-testid="file-attachment"]')
        print(f"Existing attachments: {len(attachments)}")
        
        # If no attachment, re-upload
        if len(attachments) == 0:
            print(f"Re-uploading {ZIP_PATH}")
            upload = await page.query_selector("#upload-files")
            if upload:
                await upload.set_input_files(ZIP_PATH)
                await asyncio.sleep(3)
                print("ZIP uploaded.")
            else:
                print("ERROR: #upload-files not found")
                return
        
        # Count messages before
        msgs_before = await page.evaluate("""() => {
            return document.querySelectorAll('[data-message-author-role]').length;
        }""")
        print(f"Messages before: {msgs_before}")
        
        # Focus the editor
        editor = await page.query_selector('[contenteditable="true"]')
        if not editor:
            print("ERROR: No contenteditable editor found")
            return
        
        # Click to focus
        await editor.click()
        await asyncio.sleep(0.5)
        
        # Use JS to set focus and then type
        await page.evaluate("""(el) => {
            el.focus();
            el.textContent = '';
        }""", editor)
        await asyncio.sleep(0.3)
        
        # Type message character by character with longer delay
        print("Typing message...")
        await page.keyboard.type(MESSAGE, delay=3)
        await asyncio.sleep(2)
        
        # Check editor content
        editor_text = await page.evaluate("""(el) => el.textContent""", editor)
        print(f"Editor text length: {len(editor_text)} chars")
        if len(editor_text) > 10:
            print(f"Editor preview: {editor_text[:80]}...")
        
        # Check send button state
        send_btn = await page.query_selector('button[data-testid="send-button"]')
        if send_btn:
            disabled = await send_btn.get_attribute("disabled")
            print(f"Send button disabled attr: {repr(disabled)}")
            
            if disabled is None:
                # Button is enabled — click it
                await send_btn.click()
                print("Clicked send button.")
            else:
                # Try pressing Enter
                print("Button disabled, trying Enter...")
                await page.keyboard.press("Enter")
                await asyncio.sleep(1)
                
                # Check again
                disabled2 = await send_btn.get_attribute("disabled")
                print(f"After Enter, disabled: {repr(disabled2)}")
                if disabled2 is None:
                    await send_btn.click()
                    print("Clicked send after Enter.")
                else:
                    # Last resort: try Ctrl+Enter
                    print("Trying Ctrl+Enter...")
                    await page.keyboard.press("Control+Enter")
        else:
            print("No send button found, pressing Enter")
            await page.keyboard.press("Enter")
        
        # Wait for response
        print("Waiting for message to appear...")
        await asyncio.sleep(5)
        
        msgs_after = await page.evaluate("""() => {
            return document.querySelectorAll('[data-message-author-role]').length;
        }""")
        print(f"Messages after: {msgs_after}")
        
        if msgs_after > msgs_before:
            print("SUCCESS: Message count increased!")
        else:
            print("Message count unchanged. Manual intervention may be needed.")

asyncio.run(main())
