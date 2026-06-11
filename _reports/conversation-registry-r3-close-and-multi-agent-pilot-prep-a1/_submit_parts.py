#!/usr/bin/env python3
"""Send evidence to GPT in multiple parts via CDP."""
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

def read_file(path, max_lines=None):
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        text = path.read_text(encoding="utf-8", errors="replace")
    lines = text.split('\n')
    if max_lines:
        lines = lines[:max_lines]
    return '\n'.join(lines)

# Build 3 focused messages
parts = []

# Part 1: JSON Schema + Binding template
schema = read_file(PROJECT / ".agent" / "CONVERSATION_REGISTRY.schema.json")
binding = read_file(PROJECT / ".agent" / "CONVERSATION_BINDING.json")
parts.append(f"""=== R3 EVIDENCE PART 1/3: JSON Schema + Binding Template ===

--- .agent/CONVERSATION_REGISTRY.schema.json ---
{schema}

--- .agent/CONVERSATION_BINDING.json ---
{binding}

（后续 Part 2/3 和 3/3 将提供验证逻辑和测试代码）""")

# Part 2: Validation logic (role check + schema-based validation)
validator = read_file(PROJECT / "scripts" / "validate_conversation_registry.py", max_lines=400)
parts.append(f"""=== R3 EVIDENCE PART 2/3: validate_conversation_registry.py ===

{validator}

（Part 3/3 将提供测试代码和结果）""")

# Part 3: Test results + key test classes
target_output = read_file(TASK_DIR / "TARGET_TEST_OUTPUT.txt")
real_path = read_file(TASK_DIR / "REAL_PATH_PROBE.txt")

# Get test class names from test files
test_cr = read_file(PROJECT / "tests" / "test_conversation_registry.py")
test_scaffold = read_file(PROJECT / "tests" / "test_cross_project_scaffold.py")

# Extract just class names and method names
import re
def extract_test_info(code):
    classes = re.findall(r'class (\w+).*?:', code)
    methods = re.findall(r'def (test_\w+)', code)
    return classes, methods

cr_classes, cr_methods = extract_test_info(test_cr)
sc_classes, sc_methods = extract_test_info(test_scaffold)

parts.append(f"""=== R3 EVIDENCE PART 3/3: Tests + Results ===

--- TARGET_TEST_OUTPUT ---
{target_output}

--- REAL_PATH_PROBE ---
{real_path}

--- test_conversation_registry.py classes ---
{chr(10).join(cr_classes)}

--- test_conversation_registry.py methods ({len(cr_methods)} tests) ---
{chr(10).join(cr_methods)}

--- test_cross_project_scaffold.py classes ---
{chr(10).join(sc_classes)}

--- test_cross_project_scaffold.py methods ({len(sc_methods)} tests) ---
{chr(10).join(sc_methods)}

=== R3 REVIEW REQUEST ===
Run ID: CONVERSATION_REGISTRY_R3_CLOSE_AND_MULTI_AGENT_PILOT_PREP_A1_20260609T191900_RD

基于以上 3 部分证据，请给出正式判决：

overall_judgment: accepted | accepted_with_limitation | blocked | human_required
run_id: CONVERSATION_REGISTRY_R3_CLOSE_AND_MULTI_AGENT_PILOT_PREP_A1_20260609T191900_RD
findings:
  - ...
next_task_authorization: ...

---END_OF_GPT_RESPONSE---""")

# Check sizes
for i, part in enumerate(parts):
    print(f"Part {i+1}: {len(part)} chars")

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://localhost:9222")
        context = browser.contexts[0] if browser.contexts else await browser.new_context()
        page = context.pages[0] if context.pages else await context.new_page()
        
        if "chatgpt.com" not in page.url:
            await page.goto("https://chatgpt.com/", wait_until="domcontentloaded", timeout=30000)
            await asyncio.sleep(3)
        
        for i, msg in enumerate(parts):
            print(f"\nSending Part {i+1}/3 ({len(msg)} chars)...")
            
            input_sel = '#prompt-textarea'
            try:
                await page.wait_for_selector(input_sel, timeout=10000)
            except:
                input_sel = 'textarea, [contenteditable="true"]'
                await page.wait_for_selector(input_sel, timeout=10000)
            
            await page.click(input_sel)
            await asyncio.sleep(0.3)
            await page.keyboard.press("Control+a")
            await asyncio.sleep(0.2)
            await page.keyboard.press("Backspace")
            await asyncio.sleep(0.2)
            
            # Type in chunks
            chunk_size = 300
            for j in range(0, len(msg), chunk_size):
                chunk = msg[j:j+chunk_size]
                await page.keyboard.type(chunk, delay=2)
            
            print(f"  Typed {len(msg)} chars")
            await asyncio.sleep(1)
            
            # Submit
            await page.keyboard.press("Enter")
            print(f"  Part {i+1} submitted")
            
            # Wait for GPT to respond before sending next part
            if i < len(parts) - 1:
                print(f"  Waiting 30s for GPT to process...")
                await asyncio.sleep(30)
            else:
                print("  Final part submitted. Waiting for full response...")
                await asyncio.sleep(5)
        
        print("\nAll 3 parts submitted!")
        await browser.close()

asyncio.run(main())
