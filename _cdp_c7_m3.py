import asyncio, hashlib, pyperclip
from playwright.async_api import async_playwright

msg = open("D:/agent-acceptance/_reports/_c7_gpt_prompt_m3_r1.txt", encoding="utf-8").read() + "\n\nThis is the FIRST collaborative module review. Module M3: Section 1, Subsection 2 of the paper. Claude diagnosed 2 issues + 4 strategies. GPT reviews the abstract (never sees full text). Return verdict and any missed P0/P1 issues. END_OF_GPT_RESPONSE"
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
        print(f"Pasted: {len(await editor.inner_text())} chars")
        await page.keyboard.press("Control+Enter")
        print("Sent. Waiting 120s...")
        await asyncio.sleep(120)
        reply = await page.locator('div[data-message-author-role="assistant"]').last.inner_text()
        sha = hashlib.sha256(reply.encode("utf-8")).hexdigest()
        print(f"GPT: {len(reply)} chars, SHA256={sha[:16]}...")
        for line in reply.split("\n"):
            if any(w in line for w in ["verdict","severity_issues","P0","P1","blocked","pass"]):
                print(line.strip()[:120])
        with open("D:/agent-acceptance/_reports/_c7_gpt_response_m3_r1.txt", "w", encoding="utf-8") as f:
            f.write(reply)
        print("Saved.")

asyncio.run(submit())
