"""Capture R4 verdict with follow-up if needed.

CONVERSATION-HEALTH-GATE-A2: Integrated with pre_gpt_gate.
"""
import asyncio
import json
import sys
from pathlib import Path
from playwright.async_api import async_playwright

# A2 integration: import gate check
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _cdp_submit_helper import run_pre_gpt_gate  # noqa: E402

sys.stdout.reconfigure(encoding='utf-8')

OUTPUT = Path(r"D:\agent-acceptance\_evidence\conversation_health_gate_a1_r4_verdict.txt")


async def main():
    # A2: Pre-GPT gate check before CDP interaction
    exit_code, decision, message = run_pre_gpt_gate()
    if exit_code != 0:
        print(f"GATE BLOCKED (exit {exit_code}): {message}")
        sys.exit(exit_code)
    print(f"GATE: {message}")

    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://localhost:9222")
        ctx = browser.contexts[0]
        page = ctx.pages[0]

        msgs = await page.locator('[data-message-author-role="assistant"]').all()
        last = await msgs[-1].text_content()
        print(f"Last msg: {len(last)} chars")

        if len(last) < 300:
            print("Short response, sending follow-up...")
            textarea = page.locator("#prompt-textarea")
            await textarea.click()
            await asyncio.sleep(0.5)
            follow = "请继续详细核验 R4 证据包，逐项检查并给出最终判定 ACCEPTED / REJECTED / NEEDS_REVISION。"
            await page.evaluate("navigator.clipboard.writeText(arguments[0])", follow)
            await asyncio.sleep(0.3)
            await page.keyboard.press("Control+v")
            await asyncio.sleep(1)
            await page.keyboard.press("Enter")
            print("Follow-up sent, waiting...")

            stop_btn = page.locator('button[aria-label="Stop generating"]')
            for i in range(48):
                await asyncio.sleep(5)
                if not await stop_btn.is_visible():
                    await asyncio.sleep(10)
                    if not await stop_btn.is_visible():
                        print(f"Done after ~{(i+1)*5}s")
                        break

            msgs = await page.locator('[data-message-author-role="assistant"]').all()
            last = await msgs[-1].text_content()

        OUTPUT.write_text(last, encoding="utf-8")
        print(f"\nSaved {len(last)} chars")
        print()
        print(last[:3000])
        if len(last) > 3000:
            print(f"\n... ({len(last) - 3000} more)")

        upper = last.upper()
        for kw in ["ACCEPTED_WITH_MINOR", "ACCEPTED", "REJECTED", "NEEDS_REVISION"]:
            if kw in upper:
                print(f"\n*** VERDICT: {kw} ***")
                break


asyncio.run(main())
