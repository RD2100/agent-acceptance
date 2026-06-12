"""Wait for GPT R3 verdict and capture."""
import asyncio
import sys
from pathlib import Path
from playwright.async_api import async_playwright

sys.stdout.reconfigure(encoding='utf-8')

OUTPUT = Path(r"D:\agent-acceptance\_evidence\conversation_health_gate_a1_r3_verdict.txt")


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://localhost:9222")
        ctx = browser.contexts[0]
        page = ctx.pages[0]

        # Wait for generation to complete
        stop_btn = page.locator('button[aria-label="Stop generating"]')
        print("Waiting for GPT to finish generating...")
        for i in range(36):  # up to 3 minutes
            await asyncio.sleep(5)
            is_gen = await stop_btn.is_visible()
            if not is_gen:
                print(f"  Complete after {(i+1)*5}s")
                break
            print(f"  Still generating... {(i+1)*5}s")

        await asyncio.sleep(5)

        # Capture the last assistant message
        full_text = await page.evaluate("""() => {
            const msgs = document.querySelectorAll('[data-message-author-role="assistant"]');
            const last = msgs[msgs.length - 1];
            return last ? last.innerText : 'NO MESSAGE';
        }""")

        OUTPUT.write_text(full_text, encoding="utf-8")
        print(f"\nSaved {len(full_text)} chars to {OUTPUT.name}")

        # Print verdict
        print(f"\n{'='*60}")
        print(full_text)
        print(f"{'='*60}")

        # Check for verdict
        upper = full_text.upper()
        for kw in ["ACCEPTED_WITH_MINOR_LIMITATIONS", "ACCEPTED", "REJECTED",
                    "NEEDS_REVISION", "NEEDS REVISION"]:
            if kw in upper:
                print(f"\n*** VERDICT: {kw} ***")
                break


asyncio.run(main())
