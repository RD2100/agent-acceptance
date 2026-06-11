#!/usr/bin/env python3
"""Resubmit Part 2/2 of pilot evidence via CDP."""
import asyncio, json, sys
from pathlib import Path
from playwright.async_api import async_playwright

TASK_DIR = Path(r"D:\agent-acceptance\_reports\multi-agent-multi-gpt-pilot-a1")
EVIDENCE_FILE = TASK_DIR / "_inline_evidence.txt"
RUN_ID = "MULTI_AGENT_MULTI_GPT_PILOT_A1_20260610T102443_RD"


async def main():
    evidence = EVIDENCE_FILE.read_text(encoding="utf-8")
    marker = "=== FILE 4:"
    idx = evidence.find(marker)
    if idx == -1:
        idx = len(evidence) // 2

    part2_body = evidence[idx:].strip()
    part2 = f"=== PILOT-A1 EVIDENCE PART 2/2 ===\n{part2_body}"

    print(f"Part 2: {len(part2)} chars")

    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://localhost:9222")
        context = browser.contexts[0]
        page = context.pages[0]
        print(f"Page: {await page.title()}")

        # Find input area
        input_sel = '#prompt-textarea'
        try:
            await page.wait_for_selector(input_sel, timeout=8000)
        except Exception:
            input_sel = '[contenteditable="true"]'
            await page.wait_for_selector(input_sel, timeout=8000)

        # Click, clear
        await page.click(input_sel)
        await asyncio.sleep(0.3)
        await page.keyboard.press("Control+a")
        await asyncio.sleep(0.1)
        await page.keyboard.press("Backspace")
        await asyncio.sleep(0.3)

        # Use keyboard.insertText (Playwright native, very reliable)
        print("  Inserting text via keyboard.insertText...")
        await page.keyboard.insert_text(part2)
        await asyncio.sleep(1)

        # Verify text was inserted
        textarea_text = await page.evaluate("""() => {
            const el = document.querySelector('#prompt-textarea') ||
                       document.querySelector('[contenteditable="true"]');
            return el ? el.innerText.length : 0;
        }""")
        print(f"  Textarea contains {textarea_text} chars")

        if textarea_text < 100:
            print("  WARNING: Text insertion may have failed. Retrying with paste event...")
            await page.evaluate("""(text) => {
                const el = document.querySelector('#prompt-textarea') ||
                           document.querySelector('[contenteditable="true"]');
                el.focus();
                const dt = new DataTransfer();
                dt.setData('text/plain', text);
                const pe = new ClipboardEvent('paste', {clipboardData: dt, bubbles: true, cancelable: true});
                el.dispatchEvent(pe);
            }""", part2)
            await asyncio.sleep(1)
            textarea_text = await page.evaluate("""() => {
                const el = document.querySelector('#prompt-textarea') ||
                           document.querySelector('[contenteditable="true"]');
                return el ? el.innerText.length : 0;
            }""")
            print(f"  After retry: {textarea_text} chars in textarea")

        # Submit
        await asyncio.sleep(0.5)
        print("  Submitting...")
        await page.keyboard.press("Enter")
        print("  Submitted!")

        # Wait for response
        print("  Waiting for GPT response (up to 180s)...")
        for i in range(36):
            await asyncio.sleep(5)
            stop_btn = page.locator('button[aria-label="Stop generating"]')
            generating = await stop_btn.count() > 0
            if not generating and i > 3:
                msgs = page.locator('[data-message-author-role="assistant"]')
                count = await msgs.count()
                if count > 4:  # More messages than before (was 4)
                    last = msgs.nth(count - 1)
                    text = await last.inner_text()
                    if len(text) > 50:
                        print(f"  GPT finished. Response: {len(text)} chars")
                        print(f"\n--- FULL RESPONSE ---\n{text}\n--- END ---")

                        result_file = TASK_DIR / "GPT_REVIEW_RESULT.txt"
                        result_file.write_text(text, encoding="utf-8")
                        print(f"\nSaved to {result_file}")

                        has_judgment = "overall_judgment" in text.lower()
                        has_accepted = "accepted" in text.lower()
                        has_blocked = "blocked" in text.lower()
                        print(f"judgment={has_judgment}, accepted={has_accepted}, blocked={has_blocked}")

                        # Save status
                        status = {
                            "submitted": True,
                            "method": "playwright_cdp_part2_resubmit",
                            "run_id": RUN_ID,
                            "part2_chars": len(part2),
                        }
                        status_file = TASK_DIR / "GPT_REVIEW_SUBMISSION_STATUS.json"
                        status_file.write_text(json.dumps(status, indent=2, ensure_ascii=False), encoding="utf-8")

                        await browser.close()
                        return

                print(f"  {(i+1)*5}s: {await msgs.count()} messages, generating={generating}")

        print("  Timeout waiting for response")
        await browser.close()


asyncio.run(main())
