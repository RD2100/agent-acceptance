"""Submit all pending first-pass reviews in batch."""
import asyncio, hashlib, pyperclip, os
from playwright.async_api import async_playwright
os.chdir("D:/agent-acceptance")

results = []
for mid in ["M10","M11","M12"]:
    prompt = open(f"_reports/_c7_gpt_prompt_{mid}_r1.txt", encoding="utf-8").read()
    msg = prompt[:1500] + f"\n...\nFirst-pass for {mid}. Return P0/P1 and verdict. END_OF_GPT_RESPONSE"

    pyperclip.copy(msg)

    async def submit_one(mid=mid, msg=msg):
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
            p1_count = len([l for l in reply.split("\n") if "severity: P1" in l])
            print(f"{mid}: {p1_count} P1 issues, verdict={_extract_verdict(reply)}")
            with open(f"_reports/{mid.lower()}_round1_gpt_response.txt", "w", encoding="utf-8") as f:
                f.write(reply)

    asyncio.run(submit_one())
    print(f"  {mid} done")

def _extract_verdict(text):
    for line in text.split("\n"):
        if "verdict:" in line:
            return line.split(":")[-1].strip()
    return "unknown"
