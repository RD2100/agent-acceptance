#!/usr/bin/env python3
"""Submit Phase 1-4 evidence to GPT reviewer via CDP."""

import json
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
EVIDENCE_FILE = REPO / "_reports" / "multi-project-batch-init-a1" / "_inline_evidence_phases1_4.txt"
REVIEWER_CONV_ID = "6a26cc03-235c-83a2-a0fc-cd29be615959"
CHAT_URL = f"https://chatgpt.com/c/{REVIEWER_CONV_ID}"
CDP_ENDPOINT = "http://localhost:9222"


def submit():
    from playwright.sync_api import sync_playwright

    evidence = EVIDENCE_FILE.read_text(encoding="utf-8")

    header = (
        "AWSP 10-PROJECT MULTI-AGENT EXPANSION — Phases 1-4 Complete\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "Following your MULTI-PROJECT-REGISTRY-BATCH-INIT-A1 authorization, "
        "we have completed Phases 1 through 4 of the 10-project expansion plan:\n"
        "- Phase 1: 10-project batch registry init (7/7 PASS)\n"
        "- Phase 2: Lazy launch manager (24 tests PASS)\n"
        "- Phase 3: 10-project router stress test (19 tests PASS)\n"
        "- Phase 4: Real GPT conversation binding for project-alpha\n"
        "Full test suite: 848 passed, 0 failed.\n\n"
    )

    review_request = (
        "\n\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "REVIEW REQUEST: Evaluate Phases 1-4 of the 10-project expansion.\n"
        "Check: (1) batch registry completeness, (2) lazy-launch design, "
        "(3) router stress coverage, (4) real GPT binding validity, "
        "(5) test suite adequacy, (6) limitation handling.\n"
        "Provide verdict: accepted / accepted_with_limitation / needs_revision / blocked\n"
        "Authorize Phase 5-6 if acceptable."
    )

    full_message = header + evidence + review_request
    print(f"Message length: {len(full_message)} chars")

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
            target_page.goto(CHAT_URL, wait_until="domcontentloaded", timeout=30000)
            time.sleep(5)

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

        messages = target_page.query_selector_all('[data-message-author-role="assistant"]')
        if messages:
            last_msg = messages[-1]
            text = last_msg.inner_text()
            print(f"\nCaptured response: {len(text)} chars")

            out_path = REPO / "_reports" / "multi-project-batch-init-a1" / "GPT_REVIEW_PHASES1_4.txt"
            out_path.write_text(text, encoding="utf-8")
            print(f"Saved to: {out_path}")

            if len(text) < 200:
                print("WARNING: Response seems short.")
            else:
                print("Response captured successfully.")
        else:
            print("ERROR: No assistant messages found.")

        browser.close()


if __name__ == "__main__":
    submit()
