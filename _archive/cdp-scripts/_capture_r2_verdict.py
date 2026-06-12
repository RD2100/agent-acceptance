"""Send follow-up to GPT and capture R2 verdict."""
import asyncio
import json
import sys
from pathlib import Path
from playwright.async_api import async_playwright

sys.stdout.reconfigure(encoding='utf-8')

REPO = Path(r"D:\agent-acceptance")
OUTPUT = REPO / "_evidence" / "conversation_health_gate_a1_r2_verdict.txt"
CHAT_URL = "https://chatgpt.com/c/6a2a8cb1-b228-83aa-addb-79bda9aba043"


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://localhost:9222")
        ctx = browser.contexts[0]
        page = ctx.pages[0]

        print(f"URL: {page.url}")

        # Check current state
        stop_btn = page.locator('button[aria-label="Stop generating"]')
        is_gen = await stop_btn.is_visible()
        print(f"Still generating: {is_gen}")

        # Check latest response length
        msgs = await page.locator('[data-message-author-role="assistant"]').all()
        last_text = await msgs[-1].text_content()
        print(f"Last message: {len(last_text)} chars")

        if len(last_text) < 200:
            # GPT only gave acknowledgment, send follow-up
            print("\nSending follow-up to prompt detailed review...")
            textarea = page.locator("#prompt-textarea")
            await textarea.click()
            await asyncio.sleep(0.5)

            follow_up = "请继续，逐项核验 R2 证据包并给出最终判定。重点检查：1) latest.json 是否入包 2) 阈值语义是否与共识一致 3) decision schema 是否能校验实际输出 4) 负路径汇总表是否准确"
            await page.evaluate(
                "navigator.clipboard.writeText(arguments[0])",
                follow_up
            )
            await asyncio.sleep(0.3)
            await page.keyboard.press("Control+v")
            await asyncio.sleep(1)

            # Try Enter to send
            await page.keyboard.press("Enter")
            print("Follow-up sent!")

            # Wait for GPT to generate full response
            print("\nWaiting for GPT detailed review...")
            for i in range(24):
                await asyncio.sleep(5)
                is_gen = await stop_btn.is_visible()
                if not is_gen:
                    print(f"  Generation complete after {(i+1)*5}s")
                    break
                print(f"  Still generating... {(i+1)*5}s")
            await asyncio.sleep(3)

        # Capture final response
        msgs = await page.locator('[data-message-author-role="assistant"]').all()
        last_text = await msgs[-1].text_content()
        OUTPUT.write_text(last_text, encoding="utf-8")
        print(f"\nSaved {len(last_text)} chars to {OUTPUT.name}")
        print()
        print(last_text[:3000])
        if len(last_text) > 3000:
            print(f"\n... ({len(last_text) - 3000} more chars)")

        # Check for verdict keywords
        for kw in ["ACCEPTED", "REJECTED", "NEEDS_REVISION", "NEEDS REVISION",
                    "ACCEPTED_WITH_MINOR_LIMITATIONS"]:
            if kw in last_text.upper():
                print(f"\n*** VERDICT: {kw} ***")
                break


asyncio.run(main())
