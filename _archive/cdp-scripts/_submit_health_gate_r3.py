"""Submit round 3 final confirmation to GPT."""
import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

CONVO_URL = "https://chatgpt.com/c/6a2a8cb1-b228-83aa-addb-79bda9aba043"

MSG = """【第三轮确认】CONVERSATION-HEALTH-GATE 最终共识

两轮讨论后方案已经收敛。我整理最终共识如下，请确认或指出遗漏：

## 最终共识

### 架构：四层防御

Layer 1: Pre-Task Hard Gate (C)
- sadp_pre_task_enforcer.py 集成 conversation health check
- force_handoff → BLOCKED
- 只读 .ai/conversation/current.json，不发起 CDP 操作
- current.json missing/stale → WARNING（不 BLOCKED）

Layer 2: Pre-GPT Gate (B')
- scripts/pre_gpt_gate.py 模块化 gate
- 现有脚本过渡方案：开头 import check_pre_gpt_gate()
- 目标架构：统一 submit_gpt_review.py wrapper
- current.json missing → BLOCKED（必须刷新）
- submit wrapper 负责实时 CDP 指标采集和 current.json 更新

Layer 3: Evidence Pack Hard Requirement
- build_evidence_pack.py 强制包含 conversation-health/latest.json
- 缺失 → evidence incomplete → reviewer 不得 ACCEPTED
- review.yaml 新增 conversation_health 字段

Layer 4: Pre-Commit Advisory (A)
- pre-commit.governance.ps1 新增 conversation-health ADVISORY stage
- 只做审计提醒，不作为主门禁

### 阈值分级

Force: assistant_message_count>=60, review_round_count>=3, last_nav_result in [access_denied, not_found]
Suggest: assistant_message_count>=45, response_time>=60s, last_gpt_reply_bytes<2000, metrics_stale>=12h
Composite Force: response_time>=60 + reply_bytes<2000 + review_round_count>=2
阈值存放在 configs/conversation-health-policy.yaml，不硬编码

### 数据源

.ai/conversation/current.json — 统一 metrics source of truth
metrics_source 字段标注可信度：cdp_dom_count > wrapper_counter > manual_estimate
Pre-Task 只读 last known state，Submit wrapper 才实时刷新

### chat_url 检测

passive recording：submit wrapper 捕获导航失败写入 last_nav_result
枚举值：ok, access_denied, not_found, timeout, auth_required, cdp_unavailable, unknown

### 任务拆分

A1: Data + Decision + Pre-Task + Evidence Pack（最小可接受闭环）
A2: Pre-GPT + CDP metrics refresh + legacy script integration
A3: Pre-Commit advisory + registry reconciliation

### Migration Record

必须记录：old/new conversation、failure_reason、registry update、context_transferred
handoff_generated=false 允许但必须有解释
force_handoff due to length/round → handoff 应该生成

请确认这份共识是否完整准确。如果没问题，我会将其作为 CONVERSATION-HEALTH-GATE-A1 的正式 TaskSpec 基础。"""


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://localhost:9222")
        context = browser.contexts[0]
        page = context.pages[0] if context.pages else await context.new_page()

        await page.goto(CONVO_URL, wait_until="domcontentloaded")
        await asyncio.sleep(5)
        print(f"URL: {page.url}")

        textarea = page.locator("#prompt-textarea")
        await textarea.click()
        await asyncio.sleep(0.5)
        await page.keyboard.type(MSG, delay=2)
        await asyncio.sleep(1)

        send_btn = page.locator('button[data-testid="send-button"]')
        if await send_btn.is_visible():
            await send_btn.click()
            print("Message sent!")
        else:
            await page.keyboard.press("Enter")
            print("Sent via Enter")

        await asyncio.sleep(3)
        print("Round 3 submitted.")


asyncio.run(main())
