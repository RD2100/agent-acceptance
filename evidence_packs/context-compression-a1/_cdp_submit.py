import asyncio, subprocess
from playwright.async_api import async_playwright

msg = """CONTEXT-COMPRESSION-A1 evidence pack ready for review.

## Task Summary
Implemented a privacy-safe context compression layer. New agents now read BOOT_CONTEXT.md (~3K chars) + memory index instead of full PROJECT_HISTORY (~25K chars).

## Deliverables
- contracts/context_compression_contract.yaml
- schemas/compressed_memory_entry.schema.json + boot_context.schema.json
- scripts/compress_project_context.py (6-stage pipeline)
- scripts/build_boot_context.py (BOOT_CONTEXT generator)
- scripts/validate_context_memory.py (privacy guard, fail-closed)
- BOOT_CONTEXT.md (3035 chars, 8 sections)
- memory/index.md + 18 task memories + 6 knowledge files
- 3 test files (35 new tests)

## Verification
- Targeted tests: 35 PASS
- Full test suite: 216 PASS (no regressions)
- Privacy guard: 27 files ALL CLEAR
- BOOT_CONTEXT within 3000-6000 char limit: YES (3035)
- No dirty baseline files included: YES
- No paper text/secrets/raw transcripts: YES

CLOSURE_REPORT.md and GPT_REVIEW_PROMPT.md in the ZIP for full details.

Please review and return structured YAML verdict.
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
            print('ERROR: GPT page not found')
            return
        print(f'Found: {page.url[:80]}...')

        file_input = page.locator('input[type="file"]').first
        await file_input.set_input_files('D:/agent-acceptance/evidence_packs/context-compression-a1/closure-pack.zip')
        print('ZIP uploaded')
        await asyncio.sleep(2)

        editor = page.locator('div[contenteditable="true"].ProseMirror')
        await editor.click()
        await editor.fill(msg)
        print(f'Message pasted ({len(msg)} chars)')
        await asyncio.sleep(1)

        send_btn = page.locator('button[data-testid="send-button"]')
        await send_btn.click()
        print('Sent. Waiting 90s...')
        await asyncio.sleep(90)

        replies = page.locator('div[data-message-author-role="assistant"]')
        count = await replies.count()
        print(f'Assistant replies: {count}')
        if count > 0:
            last = replies.last
            text = await last.inner_text()
            print(f'=== GPT REPLY ===')
            print(text[:3000])
            out = 'D:/agent-acceptance/evidence_packs/context-compression-a1/GPT_REVIEW_RESULT.txt'
            with open(out, 'w', encoding='utf-8') as f:
                f.write(text)
            print(f'Saved to GPT_REVIEW_RESULT.txt')

asyncio.run(submit())
