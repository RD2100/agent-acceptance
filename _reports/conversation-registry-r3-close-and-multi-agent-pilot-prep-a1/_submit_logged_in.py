#!/usr/bin/env python3
"""Submit R3 closure evidence to logged-in GPT via CDP - send in 3 parts."""
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

# Build 3 focused parts (each under 6000 chars to avoid truncation)
schema_json = safe_read(PROJECT / ".agent" / "CONVERSATION_REGISTRY.schema.json", max_lines=80)
binding_json = safe_read(PROJECT / ".agent" / "CONVERSATION_BINDING.json", max_lines=60)

part1 = f"""=== R3 EVIDENCE PART 1/3 ===

--- CONVERSATION_REGISTRY.schema.json (JSON Schema) ---
{schema_json}

--- CONVERSATION_BINDING.json (binding template) ---
{binding_json}

Part 2/3 将提供 validate_conversation_registry.py 验证逻辑"""

# Part 2: validator key sections
validator = safe_read(PROJECT / "scripts" / "validate_conversation_registry.py", max_lines=250)

part2 = f"""=== R3 EVIDENCE PART 2/3 ===

--- validate_conversation_registry.py (前250行) ---
{validator}

Part 3/3 将提供测试结果和测试覆盖"""

# Part 3: test results and test class summary
import re

def get_test_summary(path):
    code = safe_read(path)
    classes = re.findall(r'class (\w+).*?:', code)
    methods = re.findall(r'    def (test_\w+)', code)
    return classes, methods

cr_c, cr_m = get_test_summary(PROJECT / "tests" / "test_conversation_registry.py")
sc_c, sc_m = get_test_summary(PROJECT / "tests" / "test_cross_project_scaffold.py")

target_out = safe_read(TASK_DIR / "TARGET_TEST_OUTPUT.txt")

# Real path probe
try:
    real_path = safe_read(TASK_DIR / "REAL_PATH_PROBE.txt")
    # Clean up UTF-16 encoding artifacts
    real_path = real_path.replace('\x00', '').strip()
except:
    real_path = "N/A"

part3 = f"""=== R3 EVIDENCE PART 3/3 ===

--- TARGET TEST OUTPUT ---
{target_out}

--- REAL PATH PROBE (validate_binding result) ---
{real_path}

--- test_conversation_registry.py: {len(cr_c)} classes, {len(cr_m)} tests ---
Classes: {', '.join(cr_c)}
Methods: {', '.join(cr_m)}

--- test_cross_project_scaffold.py: {len(sc_c)} classes, {len(sc_m)} tests ---
Classes: {', '.join(sc_c)}
Methods: {', '.join(sc_m)}

=== REVIEW REQUEST ===
Run ID: CONVERSATION_REGISTRY_R3_CLOSE_AND_MULTI_AGENT_PILOT_PREP_A1_20260609T191900_RD

基于以上 3 部分实际代码和测试结果，请给出正式判决：

overall_judgment: accepted | accepted_with_limitation | blocked | human_required
run_id: CONVERSATION_REGISTRY_R3_CLOSE_AND_MULTI_AGENT_PILOT_PREP_A1_20260609T191900_RD
findings:
  - category / severity / description
next_task_authorization: ...

---END_OF_GPT_RESPONSE---"""

parts = [part1, part2, part3]
for i, p in enumerate(parts):
    print(f"Part {i+1}: {len(p)} chars")

async def send_message(page, msg, part_num, total):
    """Type and send a message."""
    sel = '#prompt-textarea'
    try:
        await page.wait_for_selector(sel, timeout=10000)
    except:
        sel = '[contenteditable="true"]'
        await page.wait_for_selector(sel, timeout=10000)
    
    await page.click(sel)
    await asyncio.sleep(0.3)
    await page.keyboard.press("Control+a")
    await asyncio.sleep(0.1)
    await page.keyboard.press("Backspace")
    await asyncio.sleep(0.2)
    
    # Type in chunks
    chunk_size = 200
    for j in range(0, len(msg), chunk_size):
        await page.keyboard.type(msg[j:j+chunk_size], delay=2)
    
    print(f"  Part {part_num}/{total}: typed {len(msg)} chars")
    await asyncio.sleep(1)
    await page.keyboard.press("Enter")
    print(f"  Part {part_num}/{total}: submitted")

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://localhost:9222")
        context = browser.contexts[0]
        page = context.pages[0] if context.pages else await context.new_page()
        
        url = page.url
        print(f"Current URL: {url}")
        
        if "login" in url or "auth" in url:
            print("ERROR: Not logged in")
            await browser.close()
            sys.exit(1)
        
        # Send Part 1
        await send_message(page, parts[0], 1, 3)
        print("  Waiting 40s for GPT...")
        await asyncio.sleep(40)
        
        # Send Part 2
        await send_message(page, parts[1], 2, 3)
        print("  Waiting 40s for GPT...")
        await asyncio.sleep(40)
        
        # Send Part 3 (final)
        await send_message(page, parts[2], 3, 3)
        print("  Final part submitted. Waiting 5s...")
        await asyncio.sleep(5)
        
        print("All 3 parts submitted!")
        
        # Save status
        status = {"submitted": True, "method": "playwright_cdp_3parts", "parts": 3,
                  "total_chars": sum(len(p) for p in parts)}
        status_file = TASK_DIR / "GPT_REVIEW_SUBMISSION_STATUS.json"
        status_file.write_text(json.dumps(status, indent=2), encoding="utf-8")
        
        await browser.close()

asyncio.run(main())
