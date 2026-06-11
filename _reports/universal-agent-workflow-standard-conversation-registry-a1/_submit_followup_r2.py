#!/usr/bin/env python3
"""Send follow-up message to GPT requesting formal R2 verdict."""
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

FOLLOWUP = """请根据我提交的 R2 证据，给出正式的 R2 审查判决。

以下是 R2 已实现的修复摘要：

1. **AWSP_VERSION = "1.3.0"**: awsp_scaffold.py、validate_conversation_registry.py 均已更新，测试断言已更新
2. **CONVERSATION_REGISTRY.schema.json**: 已替换为真正的 JSON Schema（$schema, type, properties, required, enum, const:true, if/then）
3. **role 字段**: CONVERSATION_BINDING.json 模板包含 "role": "reviewer"，validate_scaffold() 和 validate_binding() 均校验 4 个允许值
4. **Schema-based validation**: validate_conversation_registry.py 加载 CONVERSATION_REGISTRY.schema.json，验证 enum 约束和 const 约束
5. **测试覆盖**: 18 个新测试（TestR2RoleAndSchemaValidation 11个 + TestR2ConversationRegistryValidation 7个），目标测试 106 passed，完整套件 611 passed

请使用以下格式给出正式判决：

```
## Overall Judgment

verdict: PASS | CONDITIONAL_PASS | FAIL

### Finding 1: AWSP_VERSION
status: RESOLVED | PARTIAL | UNRESOLVED

### Finding 2: JSON Schema
status: RESOLVED | PARTIAL | UNRESOLVED

### Finding 3: Role Field
status: RESOLVED | PARTIAL | UNRESOLVED

### Finding 4: Schema-based Validation
status: RESOLVED | PARTIAL | UNRESOLVED

### Finding 5: Test Coverage
status: RESOLVED | PARTIAL | UNRESOLVED

### Summary
[总结]

### Next Authorized Task
[如果 PASS，授权下一个任务]
```"""

async def main():
    chat_url = CHAT_URL_FILE.read_text(encoding="utf-8").strip()
    
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://localhost:9222")
        context = browser.contexts[0] if browser.contexts else await browser.new_context()
        page = context.pages[0] if context.pages else await context.new_page()
        
        current_url = page.url
        if "chatgpt.com" not in current_url or "6a26cc03" not in current_url:
            await page.goto(chat_url, wait_until="domcontentloaded", timeout=30000)
            await asyncio.sleep(3)
        
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
        for i in range(0, len(FOLLOWUP), chunk_size):
            chunk = FOLLOWUP[i:i+chunk_size]
            await page.keyboard.type(chunk, delay=5)
            await asyncio.sleep(0.1)
        
        print(f"Followup typed ({len(FOLLOWUP)} chars)")
        await asyncio.sleep(1)
        
        print("Submitting followup...")
        await page.keyboard.press("Enter")
        await asyncio.sleep(5)
        print("Followup submitted!")
        
        await browser.close()

asyncio.run(main())
