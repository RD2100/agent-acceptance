"""Submit M7 and M8 R2 strategies to GPT."""
import asyncio, hashlib, pyperclip, json, os
from playwright.async_api import async_playwright
os.chdir("D:/agent-acceptance")

async def submit_one(mid, path):
    m = json.load(open(path, encoding="utf-8"))
    msg = f"""## {mid} Round 2

### P1 Fixes ({len(m['p1_resolution'])}):
""" + "\n".join(f"- {p['id']}: {p['action']}" for p in m['p1_resolution']) + """

### Revision Structure:
""" + "\n".join(f"- Unit {u['unit']}: {u['name']} — {u['content'][:100]}" for u in m['revision_structure']) + """

Citation map: """ + ", ".join(m['citation_map'].keys()) + f"""

Round 2/3. {mid} R2. Accept/close or blocked? END_OF_GPT_RESPONSE"""

    pyperclip.copy(msg)
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
        await asyncio.sleep(120)
        reply = await page.locator('div[data-message-author-role="assistant"]').last.inner_text()
        verdict = "pass" if "pass_with_limitation" in reply or "accepted" in reply else "blocked"
        print(f"  {mid}: {verdict}")
        with open(f"_reports/{mid.lower()}_round2_gpt_response.txt", "w", encoding="utf-8") as f:
            f.write(reply)
        return verdict

async def main():
    for mid in ["M7", "M8"]:
        path = f"_reports/{mid.lower()}_round2_strategy.json"
        v = await submit_one(mid, path)
        print(f"{mid} R2: {v}")

asyncio.run(main())
