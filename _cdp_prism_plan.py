import asyncio, hashlib, pyperclip
from playwright.async_api import async_playwright

msg = """用户看了 Prism 分析后，明确想要以下功能：

1. 引用搜索 + 参考文献检索
2. AI 校稿 + 格式修正 + LaTeX 纠错
3. 项目感知型 AI（AI 知道整篇论文的全部内容）
4. 全文上传云端

但同时保留我们已有的安全优势（9 道闸门、evidence-first）。

这里有一个明显矛盾：功能 3 和 4（全文给 AI、上传云端）与我们当前的核心规则"全文不入 GPT 对话"冲突。用户认为这些是合理需求。

## 请制定一个平衡方案：

1. 哪些可以直接加？哪些需要改造式实现？哪些不应该加？
2. 对于"全文上传云端 + 项目感知 AI"这个矛盾，给出一个折中方案——比如是否是加密上传？本地处理？端侧模型？其他方案？
3. 引用搜索+参考文献检索的技术实现方案（本机网络被防火墙阻断，但 gh CLI 可联网——也许可以走这个通道？）
4. AI 校稿+格式修正：是否需要接入本地模型？还是通过审查链交给 GPT？
5. 给出优先级排序和可执行的 TaskSpec。

请务实——考虑我们当前的架构限制（Paper C4-C7 pipeline、CDP bridge、本地处理为主、9 道安全闸门）。不要给空中楼阁方案。END_OF_GPT_RESPONSE"""

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
        print("Sent. Waiting 240s for detailed plan...")
        await asyncio.sleep(240)
        reply = await page.locator('div[data-message-author-role="assistant"]').last.inner_text()
        sha = hashlib.sha256(reply.encode("utf-8")).hexdigest()
        print(f"GPT: {len(reply)} chars, SHA256={sha[:16]}...")
        print(reply[:5000])
        with open("D:/agent-acceptance/GPT_PRISM_PLAN.txt", "w", encoding="utf-8") as f:
            f.write(reply)
        print("Saved.")

asyncio.run(submit())
