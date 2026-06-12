"""Check browser tabs and navigate to ChatGPT."""
import asyncio
from playwright.async_api import async_playwright

TARGET_URL = "https://chatgpt.com/c/6a297f76-3e7c-83a5-a0e5-b4413d923c7e"
CDP_URL = "http://localhost:9222"

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp(CDP_URL)
        ctx = browser.contexts[0]

        print(f"Open tabs: {len(ctx.pages)}")
        for i, page in enumerate(ctx.pages):
            print(f"  [{i}] {page.url[:100]}")

        # Navigate to target
        print(f"\nNavigating to: {TARGET_URL}")
        page = ctx.pages[0] if ctx.pages else await ctx.new_page()
        await page.goto(TARGET_URL, wait_until="networkidle", timeout=30000)
        print(f"Done. URL: {page.url}")

asyncio.run(main())
