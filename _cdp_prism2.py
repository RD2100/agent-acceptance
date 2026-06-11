import asyncio, hashlib, pyperclip
from playwright.async_api import async_playwright

msg = """OpenAI 发布了 Prism，官方页面：https://openai.com/zh-Hans-CN/prism/

由于网络限制我无法直接抓取页面内容。请你基于你的训练数据，告诉我：

1. OpenAI Prism 是什么产品？它的定位是什么？
2. 它有哪些核心功能？（逐条列出）
3. 它的工作流是怎样的？用户如何使用？
4. 它是如何与 ChatGPT/GPT 模型集成的？
5. 和我们当前论文系统的功能对比：Prism 有哪些我们有的功能？有哪些我们没有的？
6. 哪些是我们不应该复制的？哪些是我们可以学习的？

请尽可能详细回答。如果训练数据中没有 Prism 的具体信息，请如实告知，然后基于你对 OpenAI 产品生态的了解给出合理推测，并标注哪些是推测。END_OF_GPT_RESPONSE"""

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
        print("Sent. Waiting 240s...")
        await asyncio.sleep(240)
        reply = await page.locator('div[data-message-author-role="assistant"]').last.inner_text()
        sha = hashlib.sha256(reply.encode("utf-8")).hexdigest()
        print(f"GPT: {len(reply)} chars, SHA256={sha[:16]}...")
        print(reply[:5000])
        with open("D:/agent-acceptance/GPT_PRISM_ANALYSIS2.txt", "w", encoding="utf-8") as f:
            f.write(reply)
        print("Saved.")

asyncio.run(submit())
