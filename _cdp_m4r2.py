import asyncio, hashlib, pyperclip, json, os
from playwright.async_api import async_playwright

os.chdir("D:/agent-acceptance")
m4 = json.load(open("_reports/m4_round3_strategy.json", encoding="utf-8"))
rs = m4["revision_structure"]
rf = m4["reframing"]
lc = m4["logic_chain"]

msg = f"""## M4 Round 3 (FINAL): Reframed as inevitability proof

### Reframing: {rf}
### Logic chain: {lc}

### Revision Structure (3 units):
"""
for u in rs:
    msg += f"- Unit {u['unit']}: {u['name']} — {u['content'][:120]}\n"

msg += f"\nCitation map: {', '.join(m4['citation_function_map'].keys())}"

msg += "\n\n### P1 Resolution:"
for p1, r in m4['p1_resolution'].items():
    msg += f"\n- {p1}: {r}"

msg += "\n\nRound 3/3 FINAL. Accept and close M4? END_OF_GPT_RESPONSE"

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
        print("M4 R2 sent. Waiting 120s...")
        await asyncio.sleep(120)
        reply = await page.locator('div[data-message-author-role="assistant"]').last.inner_text()
        sha = hashlib.sha256(reply.encode("utf-8")).hexdigest()
        for line in reply.split("\n"):
            if any(w in line for w in ["verdict","accepted","blocked","pass","close"]):
                print(line.strip()[:120])
        print(f"SHA256={sha[:16]}...")
        with open("_reports/m4_round2_gpt_response.txt", "w", encoding="utf-8") as f:
            f.write(reply)

asyncio.run(submit())
