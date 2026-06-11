import asyncio, hashlib, pyperclip, json, os
from playwright.async_api import async_playwright

os.chdir("D:/agent-acceptance")
m6 = json.load(open("_reports/m6_round2_strategy.json", encoding="utf-8"))
msg = f"""## M6 Round 2: Mechanism analysis + contemporary case

### P1 Resolution:
""" + "\n".join(f"- {p['id']}: {p['action']}" for p in m6['p1_resolution']) + """

### Revision Structure:
""" + "\n".join(f"- Unit {u['unit']}: {u['name']} — {u['content'][:120]}" for u in m6['revision_structure']) + f"""

Citation map: {', '.join(m6['citation_function_map'].keys())}

Round 2/3. Accept and close, or blocked? END_OF_GPT_RESPONSE"""
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
        print("M6 sent. Waiting 120s...")
        await asyncio.sleep(120)
        reply = await page.locator('div[data-message-author-role="assistant"]').last.inner_text()
        sha = hashlib.sha256(reply.encode("utf-8")).hexdigest()
        for line in reply.split("\n"):
            if any(w in line for w in ["verdict","accepted","blocked","P1","P0"]):
                print(line.strip()[:120])
        print(f"SHA256={sha[:16]}...")
        with open("_reports/m6_round1_gpt_response.txt", "w", encoding="utf-8") as f:
            f.write(reply)

asyncio.run(submit())
