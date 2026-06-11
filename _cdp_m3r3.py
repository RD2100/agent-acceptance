import asyncio, hashlib, pyperclip, json, os
from playwright.async_api import async_playwright

os.chdir("D:/agent-acceptance")
r3 = json.load(open("_reports/m3_round3_strategy.json", encoding="utf-8"))
td = r3["title_decision"]
rs = r3["revision_structure"]
cm = r3["citation_function_map"]

msg = f"""## M3 Round 3 (FINAL): GPT-guided structural revision

### P1 Resolution
- M3-P1-01: Title decision → {td['action']}
- M3-P1-02: Bidirectional mechanism chain defined:
  Mechanism 1: Scale expansion → per-student resources diluted → forces reform in training, resource allocation, governance
  Mechanism 2: Quality improvement → enhances social recognition → provides legitimacy, capacity, and sustainability for expansion
- M3-P1-03: Citation function map with 5 categories:
  {', '.join(cm.keys())}

### Revision Structure (3 units):
"""
for u in rs:
    msg += f"- Unit {u['unit']}: {u['name']} ({u['suggested_sentences']} sentences) — {u['content_strategy'][:100]}\n"

msg += "\nRound 3/3. This is the final attempt per iteration policy. Accept and close M3, or mark human_required? END_OF_GPT_RESPONSE"

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
        for line in reply.split("\n"):
            if any(w in line for w in ["verdict","accepted","blocked","human_required","close"]):
                print(line.strip()[:120])
        print(f"SHA256={sha[:16]}...")
        with open("_reports/m3_round3_gpt_response.txt", "w", encoding="utf-8") as f:
            f.write(reply)

asyncio.run(submit())
