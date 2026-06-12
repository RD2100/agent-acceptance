"""Submit round 2 discussion to GPT."""
import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

CONVO_URL = "https://chatgpt.com/c/6a2a8cb1-b228-83aa-addb-79bda9aba043"

MSG = """【第二轮讨论】Conversation Health Gate — 落地实施细节

你的四层方案我认可：C + B' + Evidence Pack + A advisory。现在讨论落地细节。

## 我同意的部分

1. C (Pre-Task hard gate) — 完全合理，force_handoff 时 BLOCKED 与现有 SADP 逻辑一致
2. Evidence Pack hard requirement — 这是最强的防绕过手段，"缺少证据则不能 ACCEPTED"是 evidence-first 思维
3. 阈值重分级 — 同意把 last_gpt_reply_bytes < 2000 从 force 降级到 suggest，composite 触发更稳
4. .ai/conversation/current.json 作为统一数据源 — 必要前提

## 需要讨论的落地难点

### 难点 1：B' 统一入口 vs 现有脚本生态

当前项目中有大量独立 CDP 提交脚本：
- _submit_hrv_v5.py
- _submit_cleanup_a1.py
- _capture_cleanup_a1.py
- _submit_health_gate_proposal.py
...

这些脚本直接用 playwright CDP，没有经过统一 wrapper。

**问题**：如果要做 B' 统一入口，是先：
(a) 建一个 submit_gpt_review.py 统一 wrapper，让所有提交都经过它？
(b) 还是保留现有脚本，但在每个脚本开头加一段 `from pre_gpt_gate import check; check()` 调用？

(a) 更干净但工作量大且要迁移所有调用方
(b) 更务实但仍有绕过风险（agent 可以删掉那行 import）

**我的倾向**：(a) 作为目标架构，(b) 作为过渡方案。你怎么看？

### 难点 2：assistant_message_count 数据源

这是最脆弱的指标。当前 CDP 脚本用 `page.locator('[data-message-author-role="assistant"]').all()` 来计数，但这只在 capture 阶段才做。

**问题**：
- 如果把 assistant_message_count 放在 pre-task gate 里检查，但此时 CDP 浏览器可能还没打开
- 如果把检查放在 CDP submit wrapper 里，那第一次提交前的健康度就是空白的

**我的建议**：pre-task gate 只检查 `.ai/conversation/current.json` 的**已记录**数据（last known state），不实时查询 CDP。如果 current.json 不存在或过期超过 N 小时，视为 metrics_stale → suggest_handoff。实时查询只在 GPT submit wrapper 中做。

### 难点 3：chat_url inaccessible 的自动检测

你提到 "chat_url inaccessible" 应该作为 force_handoff 条件。但这需要实际访问 URL 才能知道。

**问题**：pre-task gate 检查时，要不要主动发起一次 CDP 导航来验证 URL 可达？还是只在 submit 失败时被动记录？

**我的建议**：passive recording。submit wrapper 捕获导航失败后写入 current.json: `"last_nav_result": "inaccessible"`。pre-task gate 只读 current.json，不主动发起 CDP 操作。这样 pre-task gate 保持轻量。

### 难点 4：conversation-migration-record

你提出 agent 在切换对话时必须生成 migration record。这个产物的格式和存放位置？

**我的建议**：
```yaml
# _evidence/conversation-health/migration-records/{timestamp}.yaml
old_conversation_id: 6a297f76
old_chat_url: https://chatgpt.com/c/6a297f76-...
failure_reason: "access_denied"
new_conversation_id: 6a2a8cb1
new_chat_url: https://chatgpt.com/c/6a2a8cb1-...
migration_time: "2026-06-11T..."
context_transferred: "V1-V5 review history"
handoff_generated: false
```

是否合理？

## 总结：我建议的 CONVERSATION-HEALTH-GATE-A1 任务分解

Phase 1 (数据层)：
- .ai/conversation/current.json schema + 写入机制
- check_handoff_needed.py 升级（支持 --write --fail-on-force --composite）

Phase 2 (门禁层)：
- sadp_pre_task_enforcer.py 集成 conversation health check
- pre_gpt_gate.py 新脚本（或统一 wrapper 的 gate 部分）

Phase 3 (证据层)：
- build_evidence_pack.py 强制包含 conversation-health evidence
- conversation-migration-record 格式标准化

Phase 4 (审计层)：
- pre-commit.governance.ps1 新增 conversation-health ADVISORY stage
- startup-read-gate.md 新增第 7 项

请确认这个分解是否合理，或者提出调整。"""


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
        print("Round 2 submitted.")


asyncio.run(main())
