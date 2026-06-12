"""Capture GPT verdict — v3 final."""
import asyncio
import sys
from pathlib import Path
from playwright.async_api import async_playwright

sys.stdout.reconfigure(encoding='utf-8')

REPO = Path(r"D:\agent-acceptance")
OUTPUT = REPO / "_evidence" / "conversation_health_gate_a1_verdict.txt"


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://localhost:9222")
        ctx = browser.contexts[0]
        page = ctx.pages[0]

        full_text = await page.evaluate("""() => {
            const msgs = document.querySelectorAll('[data-message-author-role="assistant"]');
            const last = msgs[msgs.length - 1];
            if (!last) return 'NO MESSAGE FOUND';
            return last.innerText;
        }""")

        OUTPUT.write_text(full_text, encoding="utf-8")
        print(f"Saved {len(full_text)} chars to {OUTPUT.name}")
        print()
        print(full_text)


asyncio.run(main())
