#!/usr/bin/env python3
"""Submit 10-project scaling plan request to GPT reviewer via CDP."""

import json
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
REVIEWER_CONV_ID = "6a26cc03-235c-83a2-a0fc-cd29be615959"
CHAT_URL = f"https://chatgpt.com/c/{REVIEWER_CONV_ID}"
CDP_ENDPOINT = "http://localhost:9222"


def submit():
    from playwright.sync_api import sync_playwright

    message = (
        "AWSP 多项目扩展规划请求\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "背景：MULTI-PROJECT-ISOLATION-A1 和 SMOKE-A1 均已 accepted_with_limitation。\n"
        "架构层和双端口隔离已验证通过。\n\n"
        "新信息：用户实际有约10个项目需要同时运行。\n"
        "每个项目一个agent，对应一个GPT对话，互不干扰。\n"
        "预计需要10个Chrome CDP实例（端口9222-9231）。\n\n"
        "当前已完成：\n"
        "- multi_cdp_launcher.py: 多端口Chrome管理\n"
        "- multi_project_router.py: 项目路由+隔离验证\n"
        "- PROJECT_REGISTRY.json: 全局项目注册表\n"
        "- 双端口冒烟测试 8/8 PASS\n"
        "- 全套测试 805 passed / 0 failed\n\n"
        "请给出10个项目规模下的分阶段推进计划，包括：\n"
        "1. 哪些acceptance应该先做、哪些可以后做\n"
        "2. 资源管理策略（10个Chrome实例的内存/CPU开销）\n"
        "3. 是否需要按需启动（lazy-launch）还是全部预启动\n"
        "4. 批量初始化 vs 逐个接入GPT对话的优先级\n"
        "5. 哪些步骤可以自动化、哪些需要human-gated\n"
        "6. 建议的acceptance路线图（含依赖关系）\n\n"
        "请用结构化格式输出计划，方便我们按步骤执行。"
    )

    print(f"Message length: {len(message)} chars")

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

        print("Inserting message...")
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
            message,
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

            out_path = REPO / "_reports" / "multi-project-smoke-a1" / "GPT_SCALING_PLAN.txt"
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
