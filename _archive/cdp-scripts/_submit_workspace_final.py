"""Submit EVIDENCE_PACK_R18_WORKSPACE_CLEANUP_FINAL.zip to ChatGPT via CDP."""
import asyncio
from playwright.async_api import async_playwright

ZIP_PATH = r"D:\agent-acceptance\_evidence\EVIDENCE_PACK_R18_WORKSPACE_CLEANUP_FINAL.zip"
TARGET_URL = "https://chatgpt.com/c/6a297f76-3e7c-83a5-a0e5-b4413d923c7e"
CDP_URL = "http://localhost:9222"

SUBMISSION_MSG = """R18 Workspace Cleanup FINAL Evidence - R18-WORKSPACE-CLEANUP-BLOCKING-01 Closure

## EVIDENCE_PACK_R18_WORKSPACE_CLEANUP_FINAL.zip (13 files, 2439 KB)
## Two commits: 104ac8b1 (44 files) + f06ce965 (18 files)

### R18-WORKSPACE-CLEANUP-BLOCKING-01: CLOSED

All 5 non-NEG untracked items resolved:
- _build_r18_workspace_cleanup.py -> committed in f06ce965
- _gen_r18_cleanup_evidence.py -> committed in f06ce965
- _evidence/R18-WORKSPACE-CLEANUP/ -> committed in f06ce965 (13 files including deferred register)
- 2x secret-scan-output.txt -> formally registered as denied in deferred-files-register.yaml (cannot be committed through SADP hook due to mock secret patterns)

### New Evidence in This Pack
1. **diff-combined.patch**: Full diff bc974d2f..f06ce965 (60 diff headers covering both commits)
2. **diff-104ac8b1.patch**: Individual diff for first commit (44 files)
3. **diff-f06ce965.patch**: Individual diff for second commit (18 files)
4. **git-show-104ac8b1.txt**: Name-status for first commit
5. **git-show-f06ce965.txt**: Name-status for second commit
6. **deferred-files-register.yaml**: Complete register of all 19 deferred/denied files
7. **secret-scan-output.txt**: Scan results for all 19 deferred/denied files (0 real violations)
8. **safety-report.json**: Combined safety report for both commits with staging reconciliation
9. **ai-guard-scope-check-output.txt**: 238 files checked, 0 violations
10. **sadp-audit-raw.txt**: Full pre-commit governance chain replay (all PASS)
11. **staging-count-reconciliation.md**: Explains 238 vs 229 count difference

### Post-Commit State (after f06ce965)
- Untracked: 19 files (all accounted for)
  - 17x NEG-009-secrets-read.json (deny_paths)
  - 2x secret-scan-output.txt (deny_list)
  - 0x unexpected files
- Modified tracked: 1 (.agent/PROJECT_REGISTRY.json - committed in 104ac8b1)

### Note
A third commit (e1bbd516) was made to commit the FINAL evidence pack itself. This commit is not part of the reviewed scope but is documented for completeness."""

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
            page = ctx.pages[0] if ctx.pages else await ctx.new_page()
            await page.goto(TARGET_URL, wait_until="networkidle", timeout=30000)
            target_page = page
        
        print(f"Page: {target_page.url}")
        await target_page.wait_for_timeout(3000)
        
        user_msgs_before = await target_page.locator('div[data-message-author-role="user"]').count()
        print(f"User messages before: {user_msgs_before}")
        
        print("Uploading ZIP...")
        file_input = target_page.locator('#upload-files')
        await file_input.set_input_files(ZIP_PATH)
        await target_page.wait_for_timeout(3000)
        print("File uploaded.")
        
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
        
        print("Sending...")
        send_btn = target_page.locator('button[data-testid="send-button"]')
        if await send_btn.count() > 0:
            await send_btn.first.click()
            print("Sent via button click.")
        else:
            await editor.press("Enter")
            print("Sent via Enter.")
        
        await target_page.wait_for_timeout(5000)
        
        user_msgs_after = await target_page.locator('div[data-message-author-role="user"]').count()
        print(f"User messages after: {user_msgs_after}")
        
        if user_msgs_after > user_msgs_before:
            print(f"SUCCESS: Message sent ({user_msgs_before} -> {user_msgs_after})")
        else:
            print("WARNING: Message count unchanged")
        
        print("Waiting for GPT response (180s)...")
        await target_page.wait_for_timeout(180000)
        
        assistant_msgs = target_page.locator('div[data-message-author-role="assistant"]')
        count = await assistant_msgs.count()
        if count > 0:
            last_reply = await assistant_msgs.last.inner_text()
            print(f"\n=== GPT REPLY ({len(last_reply)} chars) ===")
            print(last_reply[:3000])
            
            import os
            out_path = r"D:\agent-acceptance\_evidence\R18-WORKSPACE-CLEANUP-FINAL\gpt_reply_final2.txt"
            os.makedirs(os.path.dirname(out_path), exist_ok=True)
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(last_reply)
            print(f"\nSaved to {out_path}")

asyncio.run(main())
