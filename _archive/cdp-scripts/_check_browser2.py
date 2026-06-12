"""Check browser state via CDP."""
import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        try:
            browser = await p.chromium.connect_over_cdp("http://localhost:9222")
        except Exception as e:
            print(f"Cannot connect to CDP: {e}")
            return
        
        print(f"Contexts: {len(browser.contexts)}")
        for i, ctx in enumerate(browser.contexts):
            print(f"\nContext {i}:")
            for j, pg in enumerate(ctx.pages):
                print(f"  Page {j}: {pg.url[:100]}")

asyncio.run(main())
