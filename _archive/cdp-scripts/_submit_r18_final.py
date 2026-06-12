"""
Submit EVIDENCE_PACK_R18_FOLLOWUP_FINAL.zip to ChatGPT via CDP.
Target: https://chatgpt.com/c/6a297f76-3e7c-83a5-a0e5-b4413d923c7e
"""
import asyncio
from playwright.async_api import async_playwright

ZIP_PATH = r"D:\agent-acceptance\_evidence\EVIDENCE_PACK_R18_FOLLOWUP_FINAL.zip"
TARGET_URL = "https://chatgpt.com/c/6a297f76-3e7c-83a5-a0e5-b4413d923c7e"
CDP_URL = "http://localhost:9222"

SUBMISSION_MSG = """R18 Follow-Up FINAL Evidence Pack - All 4 Blockers Addressed

## EVIDENCE_PACK_R18_FOLLOWUP_FINAL.zip (15 files, 193.2 KB)

### BLOCKING-01 CLOSED: Complete diff.patch
- diff.patch covers ALL 238 changes including hooks/sealed-files-manifest.json
- hooks-sealed-files-manifest-diff.txt provided as standalone governance review artifact
- git-show-name-status-bc974d2f.txt cross-references all entries

### BLOCKING-02 CLOSED: chain-evidence.json includes bc974d2f
- commits_in_scope now: [511c54ab, 283b5834, dae0e9fb, a9ad148d, 3fc33dac, 4efcbac9, bc974d2f]
- chain_id updated to R18-FOLLOWUP-CLEANUP-A1-FINAL

### BLOCKING-03 CLOSED: Post-commit status evidence
- git-status-after.txt: actual post-commit git status
- deferred-files-register.yaml: 17 NEG-009 deferred (deny_paths) + 9 other session artifacts + 1 NUL device file
- secret-scan-output.txt: all deferred files scanned, 0 real secret violations

### BLOCKING-04 CLOSED: Raw/replayable hook output
- sadp-audit-raw.txt: full pre-commit governance chain replay (Update-GovernanceManifest + sadp-audit + Test-Governance) all exit_code=0, all PASS
- ai-guard-scope-check-output.txt: 238 committed files checked, 0 scope violations, 0 deny violations

### Additional Evidence
- staging-count-reconciliation.md: explains 238 (git diff --stat) vs 229 (safety-report) count difference
- safety-report.json: updated with staging_count_reconciliation field
- final-report.md: post-commit closure status with NUL file status and governance authorization

### Project Migration Note
project-beta -> dev-frame-writing was interpreted by Git as mostly renames (R100/R059), not pure deletion+addition. This is documented in final-report.md and hooks-sealed-files-manifest-diff.txt."""

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp(CDP_URL)
        ctx = browser.contexts[0]
        
        # Find target page
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
        
        # Count current user messages
        user_msgs_before = await target_page.locator('div[data-message-author-role="user"]').count()
        print(f"User messages before: {user_msgs_before}")
        
        # Upload ZIP file - use #upload-files (not the image upload inputs)
        print("Uploading ZIP file...")
        file_input = target_page.locator('#upload-files')
        await file_input.set_input_files(ZIP_PATH)
        await target_page.wait_for_timeout(3000)
        print("File uploaded.")
        
        # Type submission message
        print("Typing message...")
        editor = target_page.locator('#prompt-textarea, div[contenteditable="true"]').last
        await editor.click()
        await editor.fill("")
        await target_page.wait_for_timeout(500)
        
        # Use clipboard paste for long text
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
        print("Sending message...")
        send_btn = target_page.locator('button[data-testid="send-button"]')
        if await send_btn.count() > 0:
            await send_btn.first.click()
            print("Clicked send button.")
        else:
            # Fallback: press Enter
            await editor.press("Enter")
            print("Pressed Enter as fallback.")
        
        await target_page.wait_for_timeout(5000)
        
        # Verify message was sent
        user_msgs_after = await target_page.locator('div[data-message-author-role="user"]').count()
        print(f"User messages after: {user_msgs_after}")
        
        if user_msgs_after > user_msgs_before:
            print(f"SUCCESS: Message sent ({user_msgs_before} -> {user_msgs_after})")
        else:
            print(f"WARNING: Message count unchanged ({user_msgs_before} -> {user_msgs_after})")
        
        # Wait for GPT response
        print("Waiting for GPT response (180s)...")
        await target_page.wait_for_timeout(180000)
        
        # Capture latest assistant message
        assistant_msgs = target_page.locator('div[data-message-author-role="assistant"]')
        count = await assistant_msgs.count()
        if count > 0:
            last_reply = await assistant_msgs.last.inner_text()
            print(f"\n=== GPT REPLY (last {min(2000, len(last_reply))} chars) ===")
            print(last_reply[:2000])
            
            # Save full reply
            with open(r"D:\agent-acceptance\_evidence\R18-followup-final\gpt_reply_final.txt", "w", encoding="utf-8") as f:
                f.write(last_reply)
            print(f"\nFull reply saved ({len(last_reply)} chars)")
        else:
            print("No assistant messages found.")

asyncio.run(main())
