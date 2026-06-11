#!/usr/bin/env python3
"""Submit MULTI-PROJECT-ISOLATION-A1 evidence to GPT reviewer via CDP."""

import json
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
SCRIPTS = REPO / "scripts"
sys.path.insert(0, str(SCRIPTS))

EVIDENCE_FILE = REPO / "_reports" / "multi-project-isolation-a1" / "_inline_evidence.txt"
REVIEWER_CONV_ID = "6a26cc03-235c-83a2-a0fc-cd29be615959"
CHAT_URL = f"https://chatgpt.com/c/{REVIEWER_CONV_ID}"
CDP_ENDPOINT = "http://localhost:9222"


def submit_via_cdp():
    """Submit evidence to GPT reviewer using Playwright CDP."""
    from playwright.sync_api import sync_playwright

    evidence = EVIDENCE_FILE.read_text(encoding="utf-8")

    header = (
        "AWSP MULTI-PROJECT-ISOLATION-A1 — Multi-Project Isolation Architecture\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "Please review the following evidence pack for the multi-project isolation "
        "architecture. This extends the PILOT-A1 dual-agent binding model to support "
        "multiple independent projects running simultaneously.\n\n"
    )

    review_request = (
        "\n\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "REVIEW REQUEST: Please evaluate this multi-project isolation architecture.\n"
        "Check: (1) isolation guarantees completeness, (2) registry/binding integration, "
        "(3) collision detection coverage, (4) test adequacy, (5) backward compatibility, "
        "(6) architectural soundness.\n"
        "Provide verdict: accepted / accepted_with_limitation / needs_revision / blocked"
    )

    full_message = header + evidence + review_request

    print(f"Message length: {len(full_message)} chars")
    print(f"Target: {CHAT_URL}")

    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(CDP_ENDPOINT)
        context = browser.contexts[0]

        # Find or navigate to reviewer conversation
        target_page = None
        for page in context.pages:
            if REVIEWER_CONV_ID in page.url:
                target_page = page
                break

        if target_page is None:
            target_page = context.new_page()
            target_page.goto(CHAT_URL, wait_until="networkidle")
            time.sleep(3)

        # Insert message via direct DOM manipulation + React-compatible events
        print("Inserting evidence via DOM...")
        input_sel = "#prompt-textarea"
        target_page.wait_for_selector(input_sel, timeout=15000)

        # Click to focus
        target_page.click(input_sel)
        time.sleep(0.5)

        # Set text content using innerText approach for contenteditable
        target_page.evaluate(
            """(text) => {
                const el = document.querySelector('#prompt-textarea');
                el.focus();
                // Use execCommand for contenteditable (triggers React onChange)
                const sel = window.getSelection();
                sel.removeAllRanges();
                const range = document.createRange();
                range.selectNodeContents(el);
                sel.addRange(range);
                document.execCommand('insertText', false, text);
            }""",
            full_message,
        )
        time.sleep(2)

        # Verify content was inserted
        content = target_page.inner_text(input_sel)
        print(f"Inserted {len(content)} chars into input area")

        if len(content) < 100:
            print("WARNING: Content insertion seems incomplete. Trying alternative method...")
            target_page.click(input_sel)
            time.sleep(0.5)
            target_page.keyboard.press("Control+a")
            time.sleep(0.2)
            # Type in chunks to avoid buffer limits
            chunk_size = 500
            for i in range(0, len(full_message), chunk_size):
                target_page.keyboard.type(full_message[i:i+chunk_size], delay=1)
                time.sleep(0.1)
            content = target_page.inner_text(input_sel)
            print(f"Alt method: inserted {len(content)} chars")

        # Send with keyboard
        target_page.keyboard.press("Enter")
        print("Message sent. Waiting for response...")
        time.sleep(90)

        # Capture response
        messages = target_page.query_selector_all('[data-message-author-role="assistant"]')
        if messages:
            last_msg = messages[-1]
            text = last_msg.inner_text()
            print(f"\nCaptured response: {len(text)} chars")

            # Save response
            out_path = REPO / "_reports" / "multi-project-isolation-a1" / "GPT_REVIEW_RESULT.txt"
            out_path.write_text(text, encoding="utf-8")
            print(f"Saved to: {out_path}")

            # Check if response looks complete
            if len(text) < 200:
                print("WARNING: Response seems short. May need re-capture.")
            else:
                print("Response captured successfully.")
        else:
            print("ERROR: No assistant messages found.")

        browser.close()


if __name__ == "__main__":
    submit_via_cdp()
