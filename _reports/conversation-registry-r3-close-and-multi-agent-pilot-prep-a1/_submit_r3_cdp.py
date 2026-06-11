#!/usr/bin/env python3
"""Submit R3 closure evidence to GPT via CDP — consistent pattern.

Pattern (from previous sessions):
  1. Playwright connect_over_cdp("http://localhost:9222")
  2. Use existing page (no new pages)
  3. Paste message via clipboard + execCommand('insertText')
  4. Submit with Enter key
  5. Wait for GPT response
  6. Capture via [data-message-author-role="assistant"]
"""
import asyncio, json, sys, textwrap
from pathlib import Path

try:
    from playwright.async_api import async_playwright
except ImportError:
    sys.exit("ERROR: playwright not installed")

TASK_DIR = Path(r"D:\agent-acceptance\_reports\conversation-registry-r3-close-and-multi-agent-pilot-prep-a1")
EVIDENCE_FILE = TASK_DIR / "_inline_evidence.txt"
RUN_ID = "CONVERSATION_REGISTRY_R3_CLOSE_AND_MULTI_AGENT_PILOT_PREP_A1_20260609T191900_RD"

def split_evidence(text):
    """Split evidence into 2 parts at a section boundary, each < 6000 chars."""
    # Split at FILE 3 boundary (roughly midpoint)
    marker = "=== FILE 3:"
    idx = text.find(marker)
    if idx == -1 or idx < 3000:
        # Fallback: split at midpoint
        mid = len(text) // 2
        idx = text.rfind("===", 0, mid + 500)
        if idx == -1:
            idx = mid

    header = text[:3].rstrip() + "\n"  # "以下是..."
    # Part 1: intro + files 1-2
    part1_body = text[:idx].strip()
    # Part 2: files 3-6 + footer
    part2_body = text[idx:].strip()

    part1 = f"=== R3 EVIDENCE PART 1/2 ===\n{part1_body}\n\nPart 2/2 将包含剩余文件和测试结果。请等待。"
    part2 = f"=== R3 EVIDENCE PART 2/2 ===\n{part2_body}\n\n以上为完整 R3 证据。请基于两部分实际代码和测试结果给出正式判决：\n\noverall_judgment: accepted | accepted_with_limitation | blocked | human_required\nrun_id: {RUN_ID}\nfindings:\n  - ...\nnext_task_authorization: ...\n\n---END_OF_GPT_RESPONSE---"

    return part1, part2


async def paste_and_send(page, message, part_label):
    """Paste message via clipboard API and submit with Enter."""
    print(f"  [{part_label}] Preparing to send {len(message)} chars...")

    # Find the input area
    input_sel = '#prompt-textarea'
    try:
        await page.wait_for_selector(input_sel, timeout=8000)
    except Exception:
        input_sel = '[contenteditable="true"]'
        await page.wait_for_selector(input_sel, timeout=8000)

    # Click and clear
    await page.click(input_sel)
    await asyncio.sleep(0.3)
    await page.keyboard.press("Control+a")
    await asyncio.sleep(0.1)
    await page.keyboard.press("Backspace")
    await asyncio.sleep(0.2)

    # Use clipboard paste — most reliable for large text
    pasted = await page.evaluate("""(text) => {
        // Focus the editable element
        const el = document.querySelector('#prompt-textarea') ||
                   document.querySelector('[contenteditable="true"]');
        if (!el) return {ok: false, reason: 'no editable element'};
        el.focus();

        // Try execCommand first
        const dt = new DataTransfer();
        dt.setData('text/plain', text);
        const pasteEvent = new ClipboardEvent('paste', {
            clipboardData: dt,
            bubbles: true,
            cancelable: true,
        });
        const dispatched = el.dispatchEvent(pasteEvent);

        if (el.innerText && el.innerText.length > 100) {
            return {ok: true, method: 'paste_event', length: el.innerText.length};
        }

        // Fallback: insertText
        const ok2 = document.execCommand('insertText', false, text);
        return {ok: ok2, method: 'insertText', length: el.innerText ? el.innerText.length : 0};
    }""", message)

    print(f"  [{part_label}] Paste result: {pasted}")

    if not pasted.get("ok") or pasted.get("length", 0) < 100:
        # Fallback: page.keyboard.insertText (Playwright native)
        print(f"  [{part_label}] Clipboard fallback → keyboard.insertText...")
        await page.keyboard.insert_text(message)
        await asyncio.sleep(1)

    # Brief pause then submit
    await asyncio.sleep(0.5)
    await page.keyboard.press("Enter")
    print(f"  [{part_label}] Submitted!")


async def wait_for_response(page, timeout_s=120):
    """Wait for GPT to finish generating a response."""
    print("  Waiting for GPT response...")
    for i in range(timeout_s // 5):
        # Check if stop button exists (still generating)
        stop_btn = page.locator('button[aria-label="Stop generating"]')
        generating = await stop_btn.count() > 0
        if not generating and i > 2:
            # Double-check: make sure there's content
            msgs = page.locator('[data-message-author-role="assistant"]')
            count = await msgs.count()
            if count > 0:
                last = msgs.nth(count - 1)
                text = await last.inner_text()
                if len(text) > 50:
                    print(f"  GPT finished. Response: {len(text)} chars")
                    return text
        await asyncio.sleep(5)

    # Timeout — grab whatever is there
    msgs = page.locator('[data-message-author-role="assistant"]')
    count = await msgs.count()
    if count > 0:
        text = await msgs.nth(count - 1).inner_text()
        print(f"  Timeout — captured {len(text)} chars")
        return text
    return None


async def main():
    # Load evidence
    evidence = EVIDENCE_FILE.read_text(encoding="utf-8")
    print(f"Evidence loaded: {len(evidence)} chars")

    part1, part2 = split_evidence(evidence)
    print(f"Part 1: {len(part1)} chars")
    print(f"Part 2: {len(part2)} chars")

    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://localhost:9222")
        context = browser.contexts[0]
        # Use existing page — do NOT open new pages
        page = context.pages[0]

        title = await page.title()
        url = page.url
        print(f"Connected to: {title} ({url})")

        if "chatgpt.com" not in url:
            print("ERROR: Current page is not ChatGPT")
            await browser.close()
            sys.exit(1)

        # Check login status
        login_modal = page.locator('[data-testid="login-modal"], .modal-no-auth-login')
        if await login_modal.count() > 0:
            print("ERROR: Not logged in (login modal detected)")
            await browser.close()
            sys.exit(1)

        # === Part 1 ===
        print("\n--- Sending Part 1/2 ---")
        await paste_and_send(page, part1, "Part 1/2")

        # Wait for GPT to finish responding to Part 1
        resp1 = await wait_for_response(page, timeout_s=90)
        if resp1:
            print(f"  Part 1 response preview: {resp1[:200]}")
        else:
            print("  WARNING: No response captured for Part 1, continuing anyway")

        # === Part 2 ===
        print("\n--- Sending Part 2/2 ---")
        await paste_and_send(page, part2, "Part 2/2")

        # Wait for GPT to finish responding to Part 2 (the actual review)
        resp2 = await wait_for_response(page, timeout_s=180)

        if resp2:
            # Save the final response
            result_file = TASK_DIR / "GPT_REVIEW_RESULT.txt"
            result_file.write_text(resp2, encoding="utf-8")
            print(f"\nFinal response saved: {result_file}")
            print(f"Response length: {len(resp2)} chars")

            has_judgment = "overall_judgment" in resp2.lower() or "judgment" in resp2.lower()
            has_accepted = "accepted" in resp2.lower()
            print(f"has_judgment={has_judgment}, has_accepted={has_accepted}")
            print(f"\nPreview:\n{resp2[:500]}")
        else:
            print("ERROR: Could not capture GPT response")

        # Update submission status
        status = {
            "submitted": True,
            "method": "playwright_cdp_2parts",
            "parts": 2,
            "part1_chars": len(part1),
            "part2_chars": len(part2),
            "total_chars": len(part1) + len(part2),
            "run_id": RUN_ID,
        }
        status_file = TASK_DIR / "GPT_REVIEW_SUBMISSION_STATUS.json"
        status_file.write_text(json.dumps(status, indent=2, ensure_ascii=False), encoding="utf-8")

        # Do NOT close browser — it's the user's browser
        # await browser.close()  # commented out intentionally


asyncio.run(main())
