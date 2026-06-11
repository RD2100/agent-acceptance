import asyncio, hashlib, pyperclip, os
from playwright.async_api import async_playwright

os.chdir("D:/agent-acceptance")
idx = open("_reports/PAPER_PROJECT_INDEX_GPT_VIEW.md", encoding="utf-8").read()
msg = idx + "\n\nNew tools: project_index, citation_workspace, proofreading_gate, memory_compiler installed. 296 PASS. Next task?"

pyperclip.copy(msg)

async def submit():
    async with async_playwright() as pw:
        browser = await pw.chromium.connect_over_cdp("http://localhost:9222")
        page = None
        for ctx in browser.contexts:
            for pg in ctx.pages:
                if "6a23dd8c" in pg.url: page = pg; break
        if not page: return
        await page.keyboard.press("Escape"); await asyncio.sleep(0.3)
        editor = page.locator('div[contenteditable="true"].ProseMirror')
        await editor.click(); await asyncio.sleep(0.3)
        await page.keyboard.press("Control+v"); await asyncio.sleep(2)
        await page.keyboard.press("Control+Enter")
        print("Sent. Waiting 120s...")
        await asyncio.sleep(120)
        reply = await page.locator('div[data-message-author-role="assistant"]').last.inner_text()
        sha = hashlib.sha256(reply.encode("utf-8")).hexdigest()
        for line in reply.split("\n"):
            if "recommended_task_id" in line: print(line.strip()[:120])
        print(f"SHA256={sha[:16]}... {reply[:200]}")

asyncio.run(submit())
