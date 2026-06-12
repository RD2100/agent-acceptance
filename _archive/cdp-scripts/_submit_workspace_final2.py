"""Submit R18 workspace cleanup FINAL ZIP to ChatGPT via CDP."""
import asyncio
from playwright.async_api import async_playwright

ZIP_PATH = r"D:\agent-acceptance\_evidence\EVIDENCE_PACK_R18_WORKSPACE_CLEANUP_FINAL.zip"
TARGET_URL = "https://chatgpt.com/c/6a297f76-3e7c-83a5-a0e5-b4413d923c7e"
CDP_URL = "http://localhost:9222"

SUBMISSION_MSG = """R18 Workspace Cleanup FINAL Evidence Pack - Addressing R18-WORKSPACE-CLEANUP-BLOCKING-01

## EVIDENCE_PACK_R18_WORKSPACE_CLEANUP_FINAL.zip (17 files, 2445 KB)

### What this resolves
R18-WORKSPACE-CLEANUP-BLOCKING-01: All 5 non-NEG untracked items now committed:
- _build_r18_workspace_cleanup.py -> committed in f06ce965
- _gen_r18_cleanup_evidence.py -> committed in f06ce965
- _submit_workspace_final.py -> committed in 6022c187
- _submit_r18_final.py -> committed in 6022c187
- _evidence/R18-WORKSPACE-CLEANUP/ -> committed in f06ce965

### Two commits in this cleanup
1. **104ac8b1** (44 files): registry reconciliation, 5 session scripts, evidence dirs, NUL removal, test fix
2. **f06ce965** (8 files): closure evidence, deferred register, raw audit output, remaining scripts

### Post-commit state (git-status-after.txt)
- 17x NEG-009-secrets-read.json: intentionally deferred (deny_paths, mock secret patterns)
- 2x secret-scan-output.txt: formally denied (contain mock patterns, cannot pass SADP hook)
- 0 unexpected untracked files

### Missing files now included
- ai-guard-scope-check-output.txt: 238 files checked, 0 violations (from bc974d2f replay)
- sadp-audit-raw.txt: Full pre-commit governance chain output (manifest regen + SADP audit + advisory)
- staging-count-reconciliation.md: Explains 238 vs 229 count difference (rename counting)

### Additional evidence
- diff-combined.patch: Full diff bc974d2f..f06ce965 (60 headers)
- diff-104ac8b1.patch + diff-f06ce965.patch: Individual commit diffs
- git-show for both commits
- chain-evidence.json: commits_in_scope = [511c54ab, 283b5834, dae0e9fb, a9ad148d, 3fc33dac, 4efcbac9, bc974d2f, 104ac8b1, f06ce965]
- safety-report.json with staging count reconciliation
- deferred-files-register.yaml with all 19 deferred/denied files documented
- test-output.txt: 1038 passed, 0 failed, 21 warnings

### Summary
All workspace cleanup items are now committed and accounted for. The only remaining untracked files are the 17 NEG-009 fixtures (deny_paths) and 2 secret-scan files (deny_list) - all formally registered in deferred-files-register.yaml."""

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp(CDP_URL)
        ctx = browser.contexts[0]
        
        target_page = None
        for page in ctx.pages:
            if "6a297f76-3e7c-83a5-a0e5-b4413d923c7e" in page.url:
                target_page = page
                break
        
        if not target_page:
            print("ERROR: Target page not found. Opening it...")
            page = ctx.pages[0] if ctx.pages else await ctx.new_page()
            await page.goto(TARGET_URL, wait_until="networkidle", timeout=30000)
            target_page = page
        
        print(f"Page: {target_page.url}")
        await target_page.wait_for_timeout(3000)
        
        user_msgs_before = await target_page.locator('div[data-message-author-role="user"]').count()
        print(f"User messages before: {user_msgs_before}")
        
        # Upload ZIP
        print("Uploading ZIP...")
        file_input = target_page.locator('#upload-files')
        await file_input.set_input_files(ZIP_PATH)
        await target_page.wait_for_timeout(3000)
        print("File uploaded.")
        
        # Type message via clipboard
        print("Typing message...")
        editor = target_page.locator('#prompt-textarea, div[contenteditable="true"]').last
        await editor.click()
        await editor.fill("")
        await target_page.wait_for_timeout(500)
        
        await target_page.evaluate(f"""
            async () => {{
                const text = {repr(SUBMISSION_MSG)};
                await navigator.clipboard.writeText(text);
            }}
        """)
        await target_page.wait_for_timeout(500)
        await editor.press("Control+v")
        await target_page.wait_for_timeout(2000)
        
        # Click send button
        print("Sending...")
        send_btn = target_page.locator('button[data-testid="send-button"]')
        if await send_btn.count() > 0:
            await send_btn.first.click()
            print("Clicked send button.")
        else:
            await editor.press("Enter")
            print("Pressed Enter.")
        
        await target_page.wait_for_timeout(5000)
        
        user_msgs_after = await target_page.locator('div[data-message-author-role="user"]').count()
        print(f"User messages after: {user_msgs_after}")
        
        if user_msgs_after > user_msgs_before:
            print(f"SUCCESS: Message sent ({user_msgs_before} -> {user_msgs_after})")
        else:
            print(f"WARNING: Message count unchanged")
        
        # Wait for GPT response
        print("Waiting for GPT response (180s)...")
        await target_page.wait_for_timeout(180000)
        
        assistant_msgs = target_page.locator('div[data-message-author-role="assistant"]')
        count = await assistant_msgs.count()
        if count > 0:
            last_reply = await assistant_msgs.last.inner_text()
            print(f"\n=== GPT REPLY ({len(last_reply)} chars) ===")
            print(last_reply[:3000])
            
            import os
            out_path = r"D:\agent-acceptance\_evidence\R18-WORKSPACE-CLEANUP-FINAL\gpt_reply_final3.txt"
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(last_reply)
            print(f"\nSaved to {out_path}")

asyncio.run(main())
