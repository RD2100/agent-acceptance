import asyncio, hashlib, pyperclip
from playwright.async_api import async_playwright

msg = """对比分析请求：我们当前的论文系统 vs OpenAI Prism

## 我们已有的功能
1. PDF 全文提取 + 模块分割（12 个模块）
2. C4 元数据诊断（章节结构、论证链、引用分析）
3. C5 全文结构阅读器（段落功能映射：开场/定义/证据/规范性/结论）
4. C6 修订策略生成器（压缩建议、引用补充、过渡句模板、不代写）
5. C7 Claude+GPT 协作循环（Claude 诊断 → GPT 审查摘要 → 迭代修改）
6. 五道安全闸门（preflight、privacy guard、auth gate、GO/NOGO、dry run）
7. 迭代账本（issue 追踪、loop hash 去重、轮次预算）

## 问题
1. 你了解 OpenAI Prism 吗？它有哪些核心功能？
2. 和 Prism 相比，我们缺少什么？
3. 哪些是我们不应该做的（Prism 做但我们不应该复制的）？
4. 哪些是 Prism 没有但我们独有的优势？
5. 如果要缩小差距，优先级最高的 3 个功能是什么？

请给出具体分析，不要泛泛而谈。END_OF_GPT_RESPONSE"""

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
        with open("D:/agent-acceptance/GPT_PRISM_ANALYSIS.txt", "w", encoding="utf-8") as f:
            f.write(reply)
        print("Saved.")

asyncio.run(submit())
