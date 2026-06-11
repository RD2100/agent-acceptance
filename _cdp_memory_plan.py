import asyncio, hashlib, pyperclip
from playwright.async_api import async_playwright

msg = """需要安装 claude-memory-compiler (https://github.com/coleam00/claude-memory-compiler)，同时解决两个问题：

## 问题一：上下文 88%，急需压缩
当前编码智能体上下文已达 88%，需要自动化的记忆编译机制来清理。

## 问题二：agent-acceptance 缺第三方 Skill 接口
当前 agent-acceptance 没有 `.claude/skills/` 目录，也没有通用的第三方 skill 接入机制。
需要设计一个接口，让外部 skill 可以直接克隆到项目中就能用。

## 关于 claude-memory-compiler
它是一个 Claude Code Hook 驱动的自动记忆系统：
- Stop hook 捕获对话文本
- Claude Agent SDK 提取关键内容（决策、教训、模式）
- 写入 daily/YYYY-MM-DD.md
- compile.py 编译成结构化知识文章
- SessionStart hook 在下次会话注入记忆索引

## 需要你决策的问题

1. 安装位置：应该装在 `~/.claude/skills/claude-memory-compiler`（用户级）还是 `D:/agent-acceptance/.claude/skills/`（项目级）？
   考虑到 agent-acceptance 的定位是"规范验收层"，所有 governance 工具应该集中在这里。

2. 通用 Skill 接口设计：agent-acceptance 需要一个直接就能使用外来第三方 skill 的标准方式。
   参考 skill-installer 的模式：一个 `scripts/install_skill.py` 命令，接受 GitHub URL，自动 clone + 配置 + 注册。

3. 与现有 memory/ 系统的整合：我们已经有了 memory/index.md、memory/tasks/、memory/knowledge/。
   是替换为 compiler 格式，还是双轨并行？

4. 安装后的验证：如何确认安装成功并正常工作？

请给出具体方案，包含实现计划和 TaskSpec。这次必须安装，不只是讨论。END_OF_GPT_RESPONSE"""

pyperclip.copy(msg)

async def submit():
    async with async_playwright() as pw:
        browser = await pw.chromium.connect_over_cdp("http://localhost:9222")
        page = None
        for ctx in browser.contexts:
            for pg in ctx.pages:
                if "6a23dd8c" in pg.url: page = pg; break
        if not page: return
        await page.keyboard.press("Escape"); await asyncio.sleep(0.3)
        editor = page.locator('div[contenteditable="true"].ProseMirror')
        await editor.click(); await asyncio.sleep(0.3)
        await page.keyboard.press("Control+v"); await asyncio.sleep(2)
        print(f"Pasted: {len(await editor.inner_text())} chars")
        await page.keyboard.press("Control+Enter")
        print("Sent. Waiting 180s...")
        await asyncio.sleep(180)
        reply = await page.locator('div[data-message-author-role="assistant"]').last.inner_text()
        sha = hashlib.sha256(reply.encode("utf-8")).hexdigest()
        print(f"GPT: {len(reply)} chars, SHA256={sha[:16]}...")
        print(reply[:4000])
        with open("D:/agent-acceptance/GPT_MEMORY_PLAN.txt", "w", encoding="utf-8") as f:
            f.write(reply)
        print("Saved.")

asyncio.run(submit())
