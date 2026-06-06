"""Submit PAPER-A1 evidence pack to GPT via CDP for review.

Rule: If target GPT conversation page already exists in browser, reuse it.
      Do NOT navigate/reload — just append file + prompt + send.
      Only navigate if no matching page is found.
"""
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ZIP_PATH = ROOT / "paper-a1-evidence-pack.zip"
PROMPT_PATH = ROOT / "GPT_REVIEW_PROMPT.md"
TARGET = "https://chatgpt.com/c/6a22dc07-18a4-83a3-a922-7c9ab770db3d"


def find_or_create_page(browser):
    """Reuse existing page if target conversation is already open."""
    for ctx in browser.contexts:
        for pg in ctx.pages:
            if "chatgpt.com/c/" in pg.url:
                print(f"    Reusing existing page: {pg.url[:80]}...")
                return pg

    # No matching page — create a new one
    page = browser.contexts[0].new_page()
    print(f"    No matching page found, navigating to {TARGET}...")
    page.goto(TARGET, wait_until="domcontentloaded", timeout=30000)
    page.wait_for_timeout(3000)
    return page


def submit():
    if not ZIP_PATH.exists():
        print(f"ZIP not found: {ZIP_PATH}")
        return 1

    review_prompt = PROMPT_PATH.read_text(encoding="utf-8")

    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp("http://localhost:9222")

        # Rule: reuse existing GPT page, don't navigate/reload
        print("[1] Finding existing GPT conversation page...")
        page = find_or_create_page(browser)

        # Track baseline message count to detect new reply
        baseline = page.locator('[data-message-author-role="assistant"]').count()
        print(f"    Baseline assistant messages: {baseline}")

        # Upload ZIP as file attachment
        print("[2] Uploading evidence pack ZIP...")
        file_input = page.locator('input[type="file"]').first
        if file_input.count() > 0:
            file_input.set_input_files(str(ZIP_PATH))
            time.sleep(2)
            print(f"    ZIP attached ({ZIP_PATH.stat().st_size} bytes)")
        else:
            print("    ERROR: file input not found")
            return 1

        # Type review prompt using standard evidence pack format
        print("[3] Typing review prompt...")
        prompt_box = page.locator('#prompt-textarea').first
        if prompt_box.count() == 0:
            prompt_box = page.locator('[data-testid="prompt-textarea"]').first
        if prompt_box.count() == 0:
            prompt_box = page.locator('textarea').first

        if prompt_box.count() > 0:
            prompt_box.fill(review_prompt)
            time.sleep(1)
        else:
            print("    ERROR: prompt box not found")
            return 1

        # Click send
        print("[4] Sending...")
        send_btn = page.locator('[data-testid="send-button"]').first
        if send_btn.count() == 0:
            send_btn = page.locator('button:has(svg)').last
        if send_btn.count() > 0:
            send_btn.click()
            print("    Sent. Waiting for NEW reply (not old cached)...")
        else:
            print("    ERROR: send button not found")
            return 1

        # Wait for a NEW assistant message to appear
        print("[5] Waiting for new reply...")
        for i in range(30):
            time.sleep(10)
            msgs = page.locator('[data-message-author-role="assistant"]')
            current = msgs.count()
            if current > baseline:
                reply = msgs.last.text_content() or ""
                reply_path = ROOT / "GPT_REPLY.txt"
                reply_path.write_text(reply, encoding="utf-8")
                print(f"    [{i*10}s] NEW reply: {len(reply)} chars")
                r = reply.lower()
                if "overall judgment: accepted" in r:
                    print(f"    VERDICT: accepted")
                elif "overall judgment: blocked" in r:
                    print(f"    VERDICT: blocked")
                elif "overall judgment: partial" in r:
                    print(f"    VERDICT: partial")
                elif "overall judgment: human_required" in r:
                    print(f"    VERDICT: human_required")
                break
            print(f"    [{i*10}s] Still {current} messages...")
        else:
            print("    Timeout — no new message after 300s")

        print(f"\n=== Submission Complete ===")
        print(f"URL: {page.url}")

    return 0


if __name__ == "__main__":
    sys.exit(submit())
