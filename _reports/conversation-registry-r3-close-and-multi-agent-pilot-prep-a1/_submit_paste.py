#!/usr/bin/env python3
"""Submit R3 evidence via clipboard paste (more reliable than typing)."""
import asyncio
import json
import sys
from pathlib import Path

try:
    from playwright.async_api import async_playwright
except ImportError:
    sys.exit(1)

TASK_DIR = Path(r"D:\agent-acceptance\_reports\conversation-registry-r3-close-and-multi-agent-pilot-prep-a1")
PROJECT = Path(r"D:\agent-acceptance")

def safe_read(path, max_lines=None):
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        text = path.read_text(encoding="utf-8", errors="replace")
    lines = text.split('\n')
    if max_lines:
        lines = lines[:max_lines]
    return '\n'.join(lines)

import re
def get_test_summary(path):
    code = safe_read(path)
    classes = re.findall(r'class (\w+).*?:', code)
    methods = re.findall(r'    def (test_\w+)', code)
    return classes, methods

# Build single consolidated message
schema = safe_read(PROJECT / ".agent" / "CONVERSATION_REGISTRY.schema.json", max_lines=60)
binding = safe_read(PROJECT / ".agent" / "CONVERSATION_BINDING.json", max_lines=50)
validator = safe_read(PROJECT / "scripts" / "validate_conversation_registry.py", max_lines=200)
target = safe_read(TASK_DIR / "TARGET_TEST_OUTPUT.txt")
try:
    probe = safe_read(TASK_DIR / "REAL_PATH_PROBE.txt").replace('\x00', '').strip()
except:
    probe = "N/A"

cr_c, cr_m = get_test_summary(PROJECT / "tests" / "test_conversation_registry.py")
sc_c, sc_m = get_test_summary(PROJECT / "tests" / "test_cross_project_scaffold.py")

MSG = f"""R3 CLOSURE EVIDENCE - CONVERSATION-REGISTRY-R3-CLOSE-AND-MULTI-AGENT-PILOT-PREP-A1
Run ID: CONVERSATION_REGISTRY_R3_CLOSE_AND_MULTI_AGENT_PILOT_PREP_A1_20260609T191900_RD

[1] CONVERSATION_REGISTRY.schema.json (Real JSON Schema):
{schema}

[2] CONVERSATION_BINDING.json:
{binding}

[3] validate_conversation_registry.py (前200行):
{validator}

[4] TARGET TEST: {target}

[5] REAL PATH PROBE: {probe}

[6] TEST CLASSES:
test_conversation_registry.py: {len(cr_c)} classes ({', '.join(cr_c)}), {len(cr_m)} tests
test_cross_project_scaffold.py: {len(sc_c)} classes ({', '.join(sc_c)}), {len(sc_m)} tests

请基于以上实际代码给出正式判决:
overall_judgment: accepted | accepted_with_limitation | blocked | human_required
run_id: CONVERSATION_REGISTRY_R3_CLOSE_AND_MULTI_AGENT_PILOT_PREP_A1_20260609T191900_RD
findings: [category/severity/description]
next_task_authorization: ...
---END_OF_GPT_RESPONSE---"""

print(f"Message length: {len(MSG)} chars")

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://localhost:9222")
        context = browser.contexts[0]
        page = context.pages[0]
        
        print(f"URL: {page.url}")
        
        # Click the input
        sel = '#prompt-textarea'
        try:
            await page.wait_for_selector(sel, timeout=10000)
        except:
            sel = '[contenteditable="true"]'
            await page.wait_for_selector(sel, timeout=10000)
        
        await page.click(sel)
        await asyncio.sleep(0.3)
        
        # Clear
        await page.keyboard.press("Control+a")
        await asyncio.sleep(0.1)
        await page.keyboard.press("Backspace")
        await asyncio.sleep(0.2)
        
        # Use clipboard paste via JavaScript evaluation
        print("Setting clipboard and pasting...")
        await page.evaluate(f"""
            const el = document.querySelector('#prompt-textarea');
            if (el) {{
                el.focus();
                // Use execCommand to insert text
                document.execCommand('insertText', false, {json.dumps(MSG)});
            }}
        """)
        await asyncio.sleep(2)
        
        # Verify content was inserted
        content = await page.locator('#prompt-textarea').inner_text()
        print(f"Input content: {len(content)} chars")
        
        if len(content) < 100:
            print("Clipboard paste didn't work well, trying fill()...")
            await page.locator('#prompt-textarea').fill(MSG)
            await asyncio.sleep(1)
            content = await page.locator('#prompt-textarea').inner_text()
            print(f"After fill: {len(content)} chars")
        
        # Submit
        print("Submitting...")
        await page.keyboard.press("Enter")
        await asyncio.sleep(5)
        print("Evidence submitted!")
        
        # Save chat URL for later capture
        chat_url = page.url
        url_file = TASK_DIR / "GPT_REVIEW_CHAT_URL.txt"
        url_file.write_text(chat_url, encoding="utf-8")
        print(f"Chat URL saved: {chat_url}")
        
        await browser.close()

asyncio.run(main())
