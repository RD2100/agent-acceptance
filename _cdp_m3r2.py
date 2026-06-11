import asyncio, hashlib, pyperclip, json, os
from playwright.async_api import async_playwright

os.chdir("D:/agent-acceptance")
strat = json.load(open("_reports/m3_round2_strategy.json", encoding="utf-8"))
fixes = strat["addressing_gpt_p1_issues"]

msg = f"""## M3 Round 2: P1 Issues Addressed

### GPT Issues from Round 1:
{fixes[0]['issue']}: {fixes[0]['fix']}
{fixes[1]['issue']}: {fixes[1]['fix']}
{fixes[2]['issue']}: {fixes[2]['fix']}

### Claude Round 2 Strategies ({strat['suggestion_count']} total):
"""
for s in strat["suggestions"][:5]:
    msg += f"- [{s['type']}] {s['strategy'][:150]}\n"

msg += "\nReview: Are P1 issues resolved? Accept and close module M3? Return verdict. END_OF_GPT_RESPONSE"

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
            if any(w in line for w in ["verdict","accepted","blocked","pass"]):
                print(line.strip()[:120])
        print(f"SHA256={sha[:16]}...")
        with open("_reports/m3_round2_gpt_response.txt", "w", encoding="utf-8") as f:
            f.write(reply)

asyncio.run(submit())
