"""Capture latest GPT reply."""
import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://localhost:9222")
        ctx = browser.contexts[0]
        page = None
        for pg in ctx.pages:
            if "chatgpt.com/c/" in pg.url:
                page = pg
                break
        if not page:
            print("No page")
            return
        
        # Get latest assistant message
        msgs = await page.query_selector_all('[data-message-author-role="assistant"]')
        if msgs:
            last = msgs[-1]
            text = await last.inner_text()
            print(f"Latest assistant message ({len(text)} chars):")
            print(text[:3000])
            # Save to file
            with open("_evidence/hfs_verdict.txt", "w", encoding="utf-8") as f:
                f.write(text)
            print(f"\n--- Saved to _evidence/hfs_verdict.txt ---")
        else:
            print("No assistant messages found yet")

asyncio.run(main())
