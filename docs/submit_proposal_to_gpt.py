"""Submit proposal for GPT review prompt template to GPT for co-design iteration.
Rule: reuse existing GPT page, don't navigate/reload.
"""
import sys, time, os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROPOSAL = ROOT / "docs" / "proposal-gpt-review-template.md"
TARGET = "https://chatgpt.com/c/6a22dc07-18a4-83a3-a922-7c9ab770db3d"


def find_existing_page(browser):
    for ctx in browser.contexts:
        for pg in ctx.pages:
            if "chatgpt.com/c/" in pg.url:
                return pg
    return None


def submit():
    from playwright.sync_api import sync_playwright

    proposal_text = PROPOSAL.read_text(encoding="utf-8")

    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp("http://localhost:9222")
        page = find_existing_page(browser)

        if page:
            print(f"[1] Reusing existing page: {page.url[:80]}")
        else:
            page = browser.contexts[0].new_page()
            page.goto(TARGET, wait_until="domcontentloaded", timeout=30000)
            page.wait_for_timeout(3000)
            print(f"[1] Navigated to {TARGET[:60]}")

        baseline = page.locator('[data-message-author-role="assistant"]').count()
        print(f"    Baseline messages: {baseline}")

        # Upload proposal as file
        print("[2] Uploading proposal...")
        file_input = page.locator('input[type="file"]').first
        file_input.set_input_files(str(PROPOSAL))
        time.sleep(2)
        print(f"    Uploaded: proposal-gpt-review-template.md ({PROPOSAL.stat().st_size} bytes)")

        # Prompt
        prompt = (
            "以上是一份关于创建统一 GPT Review Prompt 模板的设计提案。\n\n"
            "请审查这份提案，重点回答：\n\n"
            "1. Base 层字段是否完备？缺少什么？\n"
            "2. task_type_specific 的结构是否合理？应该用 flat map 还是按 task_type 分组？\n"
            "3. overall_judgment vs Overall Judgment — 应该统一用哪个？\n"
            "4. evidence_inspected 应该只列文件名还是包含 SHA256？\n"
            "5. 模板应该是 .md 文件还是 .schema.json？\n"
            "6. 是否需要一个 task_type 枚举来驱动 task_type_specific 的验证？\n"
            "7. 发现任何矛盾或不一致的地方？\n\n"
            "请用结构化 YAML 格式回复你的审查意见和改进建议。"
        )

        prompt_box = page.locator('#prompt-textarea').first
        if prompt_box.count() == 0:
            prompt_box = page.locator('[data-testid="prompt-textarea"]').first
        if prompt_box.count() == 0:
            prompt_box = page.locator('textarea').first
        prompt_box.fill(prompt)
        time.sleep(1)

        print("[3] Sending...")
        send_btn = page.locator('[data-testid="send-button"]').first
        if send_btn.count() == 0:
            send_btn = page.locator('button:has(svg)').last
        send_btn.click()
        print("    Sent. Waiting for NEW reply...")

        # Wait for new message
        for i in range(30):
            time.sleep(10)
            msgs = page.locator('[data-message-author-role="assistant"]')
            current = msgs.count()
            if current > baseline:
                reply = msgs.last.text_content() or ""
                out_path = ROOT / "docs" / "GPT_PROPOSAL_REVIEW.txt"
                out_path.write_text(reply, encoding="utf-8")
                print(f"[4] [{i*10}s] NEW reply: {len(reply)} chars → {out_path}")
                break
            print(f"    [{i*10}s] Still {current} messages...")
        else:
            print("    Timeout")

    return 0


if __name__ == "__main__":
    sys.exit(submit())
