"""Debug: screenshot and DOM inspection of GPT page."""
import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

GPT_URL = "https://chatgpt.com/c/6a297f76-3e7c-83a5-a0e5-b4413f923c7e"
SCREENSHOT = r"D:\agent-acceptance\_evidence\gpt_page_debug.png"


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://localhost:9222")
        context = browser.contexts[0]
        page = context.pages[0] if context.pages else await context.new_page()

        await page.goto(GPT_URL, wait_until="domcontentloaded")
        await asyncio.sleep(5)

        # Screenshot
        await page.screenshot(path=SCREENSHOT, full_page=False)
        print(f"Screenshot saved: {SCREENSHOT}")

        # Check page URL
        print(f"Current URL: {page.url}")

        # Check for various message containers
        for sel in [
            '[data-message-author-role="assistant"]',
            '[data-message-author-role="user"]',
            'div[data-testid]',
            '[class*="message"]',
            '[class*="prose"]',
            'main',
            'article',
        ]:
            count = await page.locator(sel).count()
            if count > 0:
                print(f"  {sel}: {count} elements")

        # Get page title
        title = await page.title()
        print(f"Page title: {title}")


asyncio.run(main())
