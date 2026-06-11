import asyncio, hashlib, pyperclip
from playwright.async_api import async_playwright

msg = open("D:/agent-acceptance/_gpt_msg.py", encoding="utf-8").read()
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
        await editor.click()
        await asyncio.sleep(0.3)
        await page.keyboard.press("Control+v")
        await asyncio.sleep(2)
        text = await editor.inner_text()
        print(f"Pasted: {len(text)} chars")
        await page.keyboard.press("Control+Enter")
        print("Sent. Waiting 180s...")
        await asyncio.sleep(180)
        reply = await page.locator('div[data-message-author-role="assistant"]').last.inner_text()
        sha = hashlib.sha256(reply.encode("utf-8")).hexdigest()
        print(f"GPT: {len(reply)} chars, SHA256={sha[:16]}...")
        print(reply[:3000])
        with open("D:/agent-acceptance/GPT_CAPABILITY_FINAL.txt", "w", encoding="utf-8") as f:
            f.write(reply)

asyncio.run(submit())
