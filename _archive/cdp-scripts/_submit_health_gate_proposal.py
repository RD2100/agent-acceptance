"""Submit conversation-health-gate proposal to GPT for discussion."""
import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

CONVO_URL = "https://chatgpt.com/c/6a2a8cb1-b228-83aa-addb-79bda9aba043"

MSG = """【方案讨论】对话健康度自动检验机制 — 从被动忽略到主动执行

## 问题诊断

项目中已存在 `scripts/check_handoff_needed.py`，定义了 4 个强制切换阈值：
- assistant_message_count >= 60 → force handoff
- response_time_seconds >= 60 → force handoff
- review_round_count >= 3 → force handoff
- last_gpt_reply_bytes < 2000 → force handoff

**但这些阈值从未被主动执行过。** 原因：

1. **没有执行入口**：check_handoff_needed.py 是一个独立脚本，没有任何 hook、gate 或 workflow 步骤调用它
2. **Startup Read Gate 不包含它**：startup-read-gate.md 定义了 6 个必读书项，但没有"对话健康度检查"
3. **Pre-commit hook 不涉及它**：pre-commit.governance.ps1 只检查 sadp-audit、ai-guard、test-governance、manifest-regen
4. **SADP Pre-Task Enforcer 不涉及它**：sadp_pre_task_enforcer.py 只检查 TaskSpec、Gate 0、conflict registry
5. **Agent 的被动模式**：agent 不会主动去阅读 scripts/ 目录寻找有用工具，除非被明确指引

实际发生的案例：V3 阶段旧对话 6a297f76 返回"你无权访问此对话"，agent 直接在侧边栏找到新对话 6a2a8cb1 继续工作，完全跳过了阈值检查和对话注册表更新。

## 我的初始方案（供讨论）

### 方案 A：集成到 pre-commit hook（新增 evidence-submit 阶段）
在 pre-commit.governance.ps1 中新增第 5 个 stage `conversation-health`（ADVISORY），在每次 commit 时自动检查对话状态。

优点：每次 commit 都触发，覆盖率高
问题：commit 时不一定有 GPT 交互，response_time 等指标不适用

### 方案 B：集成到证据提交前（新增 pre-submit gate）
在每个 CDP 提交脚本（_submit_*.py）之前，强制运行阈值检查。如果 force_handoff=true，阻止提交并生成 handoff。

优点：精确卡在 GPT 交互点
问题：需要修改所有现有提交脚本，且 agent 可以绕过脚本直接 CDP

### 方案 C：集成到 SADP Pre-Task Enforcer（pre_task 阶段）
在 sadp_pre_task_enforcer.py 的 pre_task 检查中，加入对话健康度验证。如果对话已超限，BLOCKED 并强制 handoff。

优点：与现有 SADP 治理无缝衔接，每个任务开始前都会检查
问题：如果一个对话中只做 1 个任务就结束，阈值可能永远不会被触发

### 方案 D：扩展 Startup Read Gate（新增第 7 项）
在 startup-read-gate.md 中新增第 7 项必做步骤："运行 check_handoff_needed.py 并报告对话健康度"。

优点：每个 session 开始都执行
问题：startup read gate 是文档规范而非代码强制，agent 仍然可能跳过

### 我的推荐：A+C 组合
- pre_task 阶段（方案 C）：任务级别的硬门禁，force_handoff 时阻止任务启动
- pre-commit 阶段（方案 A）：commit 级别的软提醒，suggest_handoff 时输出 WARNING

请审核这个分析，指出：
1. 哪个方案或组合最合理？
2. 有没有我遗漏的执行入口？
3. 阈值数据从哪里获取？（当前 agent 运行时不一定能拿到 assistant_message_count 等指标）
4. 如何确保 agent 不会绕过检查？"""


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
        print("Submission complete.")


asyncio.run(main())
