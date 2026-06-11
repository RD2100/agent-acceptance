#!/usr/bin/env python3
"""Submit PILOT-A1 full closure evidence to GPT via CDP (2-part split)."""
import asyncio, json, sys
from pathlib import Path

try:
    from playwright.async_api import async_playwright
except ImportError:
    sys.exit("ERROR: playwright not installed")

TASK_DIR = Path(r"D:\agent-acceptance\_reports\multi-agent-multi-gpt-pilot-a1")
EVIDENCE_FILE = TASK_DIR / "_inline_evidence_r2.txt"
RUN_ID = "MULTI_AGENT_MULTI_GPT_PILOT_A1_20260610T102443_RD"


def split_evidence(text):
    """Split evidence into 2 parts at a section boundary."""
    marker = "=== FILE 4:"
    idx = text.find(marker)
    if idx == -1 or idx < 2000:
        marker = "=== FILE 5:"
        idx = text.find(marker)
    if idx == -1 or idx < 2000:
        idx = len(text) // 2
    part1 = f"=== PILOT-A1 FULL CLOSURE EVIDENCE PART 1/2 ===\n{text[:idx].strip()}\n\nPart 2/2 will include remaining files and review request."
    part2 = f"=== PILOT-A1 FULL CLOSURE EVIDENCE PART 2/2 ===\n{text[idx:].strip()}"
    return part1, part2


async def paste_and_send(page, message, part_label):
    """Paste message via clipboard API and submit with Enter."""
    print(f"  [{part_label}] Sending {len(message)} chars...")

    input_sel = '#prompt-textarea'
    try:
        await page.wait_for_selector(input_sel, timeout=8000)
    except Exception:
        input_sel = '[contenteditable="true"]'
        await page.wait_for_selector(input_sel, timeout=8000)

    await page.click(input_sel)
    await asyncio.sleep(0.3)
    await page.keyboard.press("Control+a")
    await asyncio.sleep(0.1)
    await page.keyboard.press("Backspace")
    await asyncio.sleep(0.2)

    pasted = await page.evaluate("""(text) => {
        const el = document.querySelector('#prompt-textarea') ||
                   document.querySelector('[contenteditable="true"]');
        if (!el) return {ok: false, reason: 'no editable element'};
        el.focus();
        const dt = new DataTransfer();
        dt.setData('text/plain', text);
        const pasteEvent = new ClipboardEvent('paste', {
            clipboardData: dt, bubbles: true, cancelable: true,
        });
        el.dispatchEvent(pasteEvent);
        if (el.innerText && el.innerText.length > 100) {
            return {ok: true, method: 'paste_event', length: el.innerText.length};
        }
        const ok2 = document.execCommand('insertText', false, text);
        return {ok: ok2, method: 'insertText', length: el.innerText ? el.innerText.length : 0};
    }""", message)

    print(f"  [{part_label}] Paste result: {pasted}")

    if not pasted.get("ok") or pasted.get("length", 0) < 100:
        print(f"  [{part_label}] Fallback to keyboard.insertText...")
        await page.keyboard.insert_text(message)
        await asyncio.sleep(1)

    await asyncio.sleep(0.5)
    await page.keyboard.press("Enter")
    print(f"  [{part_label}] Submitted!")


async def wait_for_response(page, timeout_s=120):
    """Wait for GPT to finish generating a response."""
    print("  Waiting for GPT response...")
    for i in range(timeout_s // 5):
        stop_btn = page.locator('button[aria-label="Stop generating"]')
        generating = await stop_btn.count() > 0
        if not generating and i > 2:
            msgs = page.locator('[data-message-author-role="assistant"]')
            count = await msgs.count()
            if count > 0:
                last = msgs.nth(count - 1)
                text = await last.inner_text()
                if len(text) > 50:
                    print(f"  GPT finished. Response: {len(text)} chars")
                    return text
        await asyncio.sleep(5)

    msgs = page.locator('[data-message-author-role="assistant"]')
    count = await msgs.count()
    if count > 0:
        text = await msgs.nth(count - 1).inner_text()
        return text
    return None


async def main():
    evidence = EVIDENCE_FILE.read_text(encoding="utf-8")
    print(f"Evidence loaded: {len(evidence)} chars")

    part1, part2 = split_evidence(evidence)
    print(f"Part 1: {len(part1)} chars")
    print(f"Part 2: {len(part2)} chars")

    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://localhost:9222")
        context = browser.contexts[0]
        page = context.pages[0]

        title = await page.title()
        url = page.url
        print(f"Connected to: {title} ({url})")

        if "chatgpt.com" not in url:
            print("ERROR: Current page is not ChatGPT")
            await browser.close()
            sys.exit(1)

        # Record message count before submission
        msgs_before = page.locator('[data-message-author-role="assistant"]')
        count_before = await msgs_before.count()
        print(f"Messages before submission: {count_before}")

        # Part 1
        print("\n--- Sending Part 1/2 ---")
        await paste_and_send(page, part1, "Part 1/2")
        resp1 = await wait_for_response(page, timeout_s=90)
        if resp1:
            print(f"  Part 1 response preview: {resp1[:200]}")

        # Part 2
        print("\n--- Sending Part 2/2 ---")
        await paste_and_send(page, part2, "Part 2/2")
        resp2 = await wait_for_response(page, timeout_s=180)

        if resp2:
            result_file = TASK_DIR / "GPT_REVIEW_RESULT_R2.txt"
            result_file.write_text(resp2, encoding="utf-8")
            print(f"\nFinal response saved: {result_file}")
            print(f"Response length: {len(resp2)} chars")
            has_judgment = "overall_judgment" in resp2.lower() or "overall" in resp2.lower()
            has_accepted = "accepted" in resp2.lower()
            print(f"has_judgment={has_judgment}, has_accepted={has_accepted}")
            print(f"\nPreview:\n{resp2[:500]}")
        else:
            print("ERROR: Could not capture GPT response")

        # Save status
        status = {
            "submitted": True,
            "method": "playwright_cdp_2parts",
            "parts": 2,
            "part1_chars": len(part1),
            "part2_chars": len(part2),
            "total_chars": len(part1) + len(part2),
            "run_id": RUN_ID,
            "submission_type": "full_closure",
        }
        status_file = TASK_DIR / "GPT_REVIEW_SUBMISSION_STATUS_R2.json"
        status_file.write_text(json.dumps(status, indent=2, ensure_ascii=False), encoding="utf-8")


asyncio.run(main())
