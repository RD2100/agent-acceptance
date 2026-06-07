import asyncio
from playwright.async_api import async_playwright

msg = """R2: CONTEXT-COMPRESSION-A1 — all three blockers fixed.

## R2 Delta

### BLOCKER-01: FULL_TEST_OUTPUT.txt added
reports/FULL_TEST_OUTPUT.txt now included in evidence pack. Shows 221 passed (216 baseline + 5 new security tests). No regressions.

### BLOCKER-02: Privacy guard file-level exemption removed
- Removed file_is_safety_doc blanket exemption
- Now uses per-line context-aware checking with backward chain scan for bullet lists
- 5 new security tests added: safety doc with embedded raw_paper_text/private_user_text/raw_transcript/doctor paper content MUST fail
- Pure safety bullet lists still pass
- Targeted tests: 40 PASS (up from 35)

### BLOCKER-03: actual_deliverables consistency fixed
- .ai/tasks/context-compression-a1.yaml now in actual_deliverables
- memory/index.md correctly placed as actual_deliverables/memory/index.md
- memory/knowledge/index.md (old GROUP-03 generated file, not CONTEXT-COMPRESSION-A1 output) removed from actual_deliverables
- SELECTED_FILES.txt updated accordingly

## Verification
- Full test suite: 221 PASS
- Privacy guard: 27 files ALL CLEAR
- BOOT_CONTEXT: 3035 chars (within 3000-6000 limit)

Please review the updated closure-pack-r2.zip.
"""

async def submit():
    async with async_playwright() as pw:
        browser = await pw.chromium.connect_over_cdp('http://localhost:9222')
        page = None
        for ctx in browser.contexts:
            for pg in ctx.pages:
                if '6a23dd8c' in pg.url:
                    page = pg
                    break
            if page:
                break
        if not page:
            print('ERROR: page not found')
            return
        print(f'Found: {page.url[:80]}...')

        file_input = page.locator('input[type="file"]').first
        await file_input.set_input_files('D:/agent-acceptance/evidence_packs/context-compression-a1/closure-pack-r2.zip')
        print('R2 ZIP uploaded')
        await asyncio.sleep(2)

        editor = page.locator('div[contenteditable="true"].ProseMirror')
        await editor.click()
        await editor.fill(msg)
        print(f'Pasted ({len(msg)} chars)')
        await asyncio.sleep(1)

        send_btn = page.locator('button[data-testid="send-button"]')
        await send_btn.click()
        print('Sent. Waiting 90s...')
        await asyncio.sleep(90)

        replies = page.locator('div[data-message-author-role="assistant"]')
        count = await replies.count()
        print(f'Replies: {count}')
        if count > 0:
            last = replies.last
            text = await last.inner_text()
            print(f'=== GPT R2 ===')
            print(text[:4000])
            out = 'D:/agent-acceptance/evidence_packs/context-compression-a1/GPT_REVIEW_RESULT_R2.txt'
            with open(out, 'w', encoding='utf-8') as f:
                f.write(text)
            print(f'Saved to GPT_REVIEW_RESULT_R2.txt')

asyncio.run(submit())
