import asyncio, hashlib, pyperclip
from playwright.async_api import async_playwright

msg = """用户提出一个新的工作流方案，需要你评审和改进。

## 当前状态
论文管道已经建好：C4（元数据诊断）、C5（全文结构阅读+段落功能映射）、C6（修订策略生成）。已经成功在真实论文上跑通。

## 用户的新想法
建一个"Claude + GPT 协作对话迭代"的自动化流程：

1. 将论文拆分成子模块（比如按章节、按小节、按段落组）
2. 对每个子模块，Claude 读原文做初始诊断 → 把诊断结果发给 GPT → GPT 提修改建议 → Claude 根据建议生成修订策略 → 再发给 GPT 审查 → 循环直到通过
3. 每个模块迭代完成后再汇总成完整的修订计划

核心思路：不是 Claude 或 GPT 单独工作，而是两者对话——Claude 负责读文本、做本地分析，GPT 负责审查和提方向建议。

## 需要你回答的问题
1. 这个"Claude+GPT 对话迭代"的流程是否合理？有没有更好的协作模式？
2. 每个模块的迭代终止条件应该是什么？（比如 GPT 连续两轮不再提新问题？还是每模块最多 3 轮？）
3. 如何避免无限循环？（GPT 和 Claude 可能在某个细节上反复来回）
4. 技术上如何实现？现有的 CDP 桥 + paper pipeline 是否够用？
5. 和用户手动使用相比，自动化协作的真正增量价值在哪里？

## 约束
- 全文不入 GPT 对话（只发诊断摘要和策略）
- Claude 不替用户写论文正文（只做诊断和策略模板）
- 权限已常驻开放

请给出具体的改进方案和可执行的下一步 TaskSpec。END_OF_GPT_RESPONSE"""

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
        print(reply[:3000])
        with open("D:/agent-acceptance/GPT_COLLAB_PLAN.txt", "w", encoding="utf-8") as f:
            f.write(reply)

asyncio.run(submit())
