import asyncio, hashlib, pyperclip
from playwright.async_api import async_playwright

msg = """C6 revision suggester ready for review, alongside updated C5.

## C5 (updated): Full-section structural reader
- Fixed PDF line break normalization (4 paragraphs/section, not 36)
- Paragraph function mapping: opening, definitional, evidence, prescriptive, closing, etc.
- 3 sections analyzed on real paper

## C6 (new): Bounded revision suggester
- Takes C5 diagnosis → generates concrete revision strategies
- 7 suggestions generated for Section 1:
  - 3 compression strategies (P2=1075字, P3=1058字, P4=1241字)
  - Evidence gap detection + citation strategy
  - Prescriptive ratio warning (50%, should be <30%)
  - Transition sentence template
- Strategy-level only, no full rewrites
- Disclaimer: "仅提供修改策略和模板，用户自行完成修改"

## Safety
- No original text in output
- No rewrites generated
- No external upload
- 296 PASS
- Committed + pushed

Review both C5 and C6. Combined verdict. END_OF_GPT_RESPONSE"""

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
        print("Sent. Waiting 180s...")
        await asyncio.sleep(180)
        reply = await page.locator('div[data-message-author-role="assistant"]').last.inner_text()
        sha = hashlib.sha256(reply.encode("utf-8")).hexdigest()
        print(f"GPT: {len(reply)} chars, SHA256={sha[:16]}...")
        for line in reply.split("\n"):
            if any(w in line for w in ["verdict","accepted","blocked","recommended"]):
                print(line.strip()[:120])
        with open("D:/agent-acceptance/GPT_C6_REVIEW.txt", "w", encoding="utf-8") as f:
            f.write(reply)

asyncio.run(submit())
