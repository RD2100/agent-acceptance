#!/usr/bin/env python3
"""Submit SMOKE-A1 evidence to GPT reviewer via CDP."""

import json
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
EVIDENCE_FILE = REPO / "_reports" / "multi-project-smoke-a1" / "_inline_evidence.txt"
REVIEWER_CONV_ID = "6a26cc03-235c-83a2-a0fc-cd29be615959"
CHAT_URL = f"https://chatgpt.com/c/{REVIEWER_CONV_ID}"
CDP_ENDPOINT = "http://localhost:9222"


def submit_via_cdp():
    from playwright.sync_api import sync_playwright

    evidence = EVIDENCE_FILE.read_text(encoding="utf-8")

    header = (
        "AWSP MULTI-PROJECT-ISOLATION-REAL-CDP-SMOKE-A1 — Controlled Two-Project Smoke Test\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "This is the real CDP smoke test authorized in the MULTI-PROJECT-ISOLATION-A1 review. "
        "Two distinct Chrome CDP instances (ports 9222 + 9223), two browser profiles, "
        "two project registries, router resolution against live CDP, isolation verification "
        "with real data.\n\n"
    )

    review_request = (
        "\n\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "REVIEW REQUEST: Evaluate this real CDP smoke test evidence.\n"
        "Check: (1) both CDP instances truly active, (2) port isolation confirmed, "
        "(3) registry+binding integration with live data, (4) router resolution accuracy, "
        "(5) gated dispatch (packets built but not sent), (6) test completeness.\n"
        "Provide verdict: accepted / accepted_with_limitation / needs_revision / blocked"
    )

    full_message = header + evidence + review_request
    print(f"Message length: {len(full_message)} chars")
    print(f"Target: {CHAT_URL}")

    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(CDP_ENDPOINT)
        context = browser.contexts[0]

        target_page = None
        for page in context.pages:
            if REVIEWER_CONV_ID in page.url:
                target_page = page
                break

        if target_page is None:
            target_page = context.new_page()
            target_page.goto(CHAT_URL, wait_until="networkidle")
            time.sleep(3)

        # Insert via DOM execCommand
        print("Inserting evidence...")
        input_sel = "#prompt-textarea"
        target_page.wait_for_selector(input_sel, timeout=15000)
        target_page.click(input_sel)
        time.sleep(0.5)

        target_page.evaluate(
            """(text) => {
                const el = document.querySelector('#prompt-textarea');
                el.focus();
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

        content = target_page.inner_text(input_sel)
        print(f"Inserted {len(content)} chars")

        target_page.keyboard.press("Enter")
        print("Message sent. Waiting for GPT response...")
        time.sleep(90)

        # Capture response
        messages = target_page.query_selector_all('[data-message-author-role="assistant"]')
        if messages:
            last_msg = messages[-1]
            text = last_msg.inner_text()
            print(f"\nCaptured response: {len(text)} chars")

            out_path = REPO / "_reports" / "multi-project-smoke-a1" / "GPT_REVIEW_RESULT.txt"
            out_path.write_text(text, encoding="utf-8")
            print(f"Saved to: {out_path}")

            if len(text) < 200:
                print("WARNING: Response seems short. May need re-capture.")
            else:
                print("Response captured successfully.")
        else:
            print("ERROR: No assistant messages found.")

        browser.close()


if __name__ == "__main__":
    submit_via_cdp()
