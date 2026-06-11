import asyncio, hashlib, pyperclip, os
from playwright.async_api import async_playwright
os.chdir("D:/agent-acceptance")
msg = open("_reports/_c7_gpt_prompt_M8_r1.txt", encoding="utf-8").read() + "\n\nFirst-pass for M8. Return P0/P1 and verdict. END_OF_GPT_RESPONSE"
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
        print("M8 sent. Waiting 120s...")
        await asyncio.sleep(120)
        reply = await page.locator('div[data-message-author-role="assistant"]').last.inner_text()
        for line in reply.split("\n"):
            if any(w in line for w in ["verdict","accepted","blocked","P1","P0"]):
                print(line.strip()[:120])
        with open("_reports/m8_round1_gpt_response.txt", "w", encoding="utf-8") as f:
            f.write(reply)
asyncio.run(submit())
