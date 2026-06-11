#!/usr/bin/env python3
"""Submit Phase 5-6 evidence to GPT reviewer via CDP."""

import sys
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

REPO = Path(__file__).resolve().parent.parent.parent
EVIDENCE_FILE = REPO / "_reports" / "multi-project-batch-init-a1" / "_inline_evidence_phases5_6.txt"
REVIEWER_CONV_ID = "6a26cc03-235c-83a2-a0fc-cd29be615959"
CDP_ENDPOINT = "http://localhost:9222"


def submit():
    evidence = EVIDENCE_FILE.read_text(encoding="utf-8")
    header = (
        "AWSP Phase 5-6 — Gate0 Preflight + Dry-Run Dispatch (10 Projects)\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "Following your authorization of MULTI-PROJECT-GATE0-PREFLIGHT-10-A1 and "
        "MULTI-PROJECT-GPT-REVIEW-DRY-RUN-10-A1, both phases are complete.\n\n"
    )
    review_request = (
        "\n\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "REVIEW REQUEST: Evaluate Phase 5-6 completeness.\n"
        "Note: PARTIAL_PASS is the honest result — profile collision correctly detected.\n"
        "Please confirm Phase 1-6 overall status and advise on remaining manual steps.\n"
        "Provide verdict: accepted / accepted_with_limitation / needs_revision / blocked"
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
            target_page.goto(f"https://chatgpt.com/c/{REVIEWER_CONV_ID}", wait_until="domcontentloaded", timeout=30000)
            time.sleep(5)

        print("Inserting evidence...")
        target_page.wait_for_selector("#prompt-textarea", timeout=15000)
        target_page.click("#prompt-textarea")
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
        target_page.keyboard.press("Enter")
        print("Sent. Waiting for response...")
        time.sleep(90)

        messages = target_page.query_selector_all('[data-message-author-role="assistant"]')
        if messages:
            text = messages[-1].inner_text()
            print(f"Captured: {len(text)} chars")
            out = REPO / "_reports" / "multi-project-batch-init-a1" / "GPT_REVIEW_PHASES5_6.txt"
            out.write_text(text, encoding="utf-8")
            print(f"Saved: {out}")
        browser.close()


if __name__ == "__main__":
    submit()
