import asyncio, hashlib, pyperclip
from playwright.async_api import async_playwright

msg = """C5 全文结构阅读器已完成。提交审查。

## 新功能
paper_c5_full_section_reader.py：
- 直接读取 PDF 章节全文（不限于元数据）
- 段落级论证功能映射：标记每段是 开场/定义/阐述/证据/转折/结论/规范性/引用密集 等
- 输出仅包含诊断，不输出原文
- 处理方式：临时读取，不入 memory，不入 evidence pack 原文

## 测试结果（真实论文 3 节）
- 必然逻辑：36 段，33% 阐述性（功能不明），56% 展开不足
- 内在张力：40 段，30% 阐述性，1 处引用密集
- 平衡之道：47 段，21% 阐述性，3 处规范性建议
- 总计：123 段，28% 功能不明确
- 跨节发现：阐述性段落占比偏高，建议每段添加明确主题句

## 安全边界
- 未储存论文原文（JSON 输出不包含段落正文）
- 未上传外部
- 未调用 Web GPT
- 296 PASS
- committed + pushed

## 问题
PDF 文本提取破坏了自然段落边界（行断变成段断），导致"展开不足"检出率高。这是 PDF 提取的已知限制。

请审查：C5 reader 是否达到 accepted 标准？下一步是否应该进入 C6（修订建议生成器）？END_OF_GPT_RESPONSE"""

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
        print("Sent. Waiting 120s...")
        await asyncio.sleep(120)
        reply = await page.locator('div[data-message-author-role="assistant"]').last.inner_text()
        sha = hashlib.sha256(reply.encode("utf-8")).hexdigest()
        print(f"GPT: {len(reply)} chars, SHA256={sha[:16]}...")
        for line in reply.split("\n"):
            if any(w in line for w in ["verdict","accepted","blocked","recommended"]):
                print(line.strip()[:120])
        with open("D:/agent-acceptance/GPT_C5_REVIEW.txt", "w", encoding="utf-8") as f:
            f.write(reply)

asyncio.run(submit())
