"""Send follow-up to GPT and wait for detailed R3 review."""
import asyncio
import json
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

        # Check latest message length
        msgs = await page.locator('[data-message-author-role="assistant"]').all()
        last_text = await msgs[-1].text_content()
        print(f"Last message: {len(last_text)} chars")
        print(f"Content: {last_text[:200]}")

        if len(last_text) < 300:
            print("\nSending follow-up to prompt detailed review...")
            textarea = page.locator("#prompt-textarea")
            await textarea.click()
            await asyncio.sleep(0.5)

            follow_up = "请开始详细核验。逐项检查 R3 证据包中：1) composite_force.txt 的 policy 值是否已改为 suggest 2) 负路径证据与 diff.patch 代码是否一致 3) latest.json 的字段是否符合 schema 4) 给出最终判定 ACCEPTED / REJECTED / NEEDS_REVISION"

            await page.evaluate(
                "navigator.clipboard.writeText(arguments[0])",
                follow_up
            )
            await asyncio.sleep(0.3)
            await page.keyboard.press("Control+v")
            await asyncio.sleep(1)
            await page.keyboard.press("Enter")
            print("Follow-up sent!")

            # Wait for full response
            stop_btn = page.locator('button[aria-label="Stop generating"]')
            print("\nWaiting for GPT review...")
            for i in range(48):  # up to 4 minutes
                await asyncio.sleep(5)
                is_gen = await stop_btn.is_visible()
                if not is_gen:
                    # Double check - wait 10 more seconds and verify still done
                    await asyncio.sleep(10)
                    is_gen2 = await stop_btn.is_visible()
                    if not is_gen2:
                        print(f"  Review complete after ~{(i+1)*5}s")
                        break
                    else:
                        print(f"  Still generating... {(i+1)*5 + 10}s")
                else:
                    print(f"  Still generating... {(i+1)*5}s")

        # Capture final response
        msgs = await page.locator('[data-message-author-role="assistant"]').all()
        last_text = await msgs[-1].text_content()
        OUTPUT.write_text(last_text, encoding="utf-8")
        print(f"\nSaved {len(last_text)} chars")
        print()
        print(last_text)

        # Verdict detection
        upper = last_text.upper()
        for kw in ["ACCEPTED_WITH_MINOR_LIMITATIONS", "ACCEPTED", "REJECTED",
                    "NEEDS_REVISION", "NEEDS REVISION"]:
            if kw in upper:
                print(f"\n*** VERDICT: {kw} ***")
                break


asyncio.run(main())
