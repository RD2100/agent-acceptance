"""Generate M10/M11/M12 R3 strategies + CDP submit."""
import asyncio, hashlib, pyperclip, json, os
from playwright.async_api import async_playwright
os.chdir("D:/agent-acceptance")

m10_r3 = {
    "module": "M10", "round": 3, "final": True,
    "title_decision": {"chosen": "reframe", "action": "从应然描述转为路径分析：如何实现从优先到协同的具体转向"},
    "revision_structure": [
        {"unit": 1, "name": "转向的三步路径",
         "content": "第一步：承认公平与效率的矛盾不可消除，只能动态管理。第二步：建立协同的优先规则。第三步：制度化协同机制。"},
        {"unit": 2, "name": "实证支撑",
         "content": "引用某省或某高校在扩招中兼顾质量保障的具体案例，证明价值平衡不只是理论可能。"},
        {"unit": 3, "name": "向M11过渡",
         "content": "价值平衡为资源平衡提供了原则框架。"}
    ],
    "citation_map": {"政策研究": "教育公平与效率协同", "案例": "扩招+提质双轨实践", "国际": "OECD质量保障框架"}
}
json.dump(m10_r3, open("_reports/m10_round3_strategy.json", "w", encoding="utf-8"), indent=2, ensure_ascii=False)

m11_r3 = {
    "module": "M11", "round": 3, "final": True,
    "title_decision": {"chosen": "operationalize", "action": "定义精准供给四个维度"},
    "revision_structure": [
        {"unit": 1, "name": "精准供给四维定义",
         "content": "对象维度(研究型vs应用型vs技能型)、领域维度(基础vs应用vs交叉)、时机维度(经常性vs竞争性)、方式维度(公式拨款vs绩效拨款)。每个维度1个案例。"},
        {"unit": 2, "name": "与M7的方案对应",
         "content": "精准供给不是放弃普惠，而是在普惠基础上针对卓越需求增加精准靶向。"},
        {"unit": 3, "name": "向M12过渡",
         "content": "资源精准供给需要制度保障——分类评价制度支撑资源精准配置。"}
    ],
    "citation_map": {"资源精准化": "教育财政精准化分配", "拨款模式": "公式拨款vs绩效拨款", "国际": "英国REF资源分配机制"}
}
json.dump(m11_r3, open("_reports/m11_round3_strategy.json", "w", encoding="utf-8"), indent=2, ensure_ascii=False)

m12_r3 = {
    "module": "M12", "round": 3, "final": True,
    "title_decision": {"chosen": "split", "action": "将7027字拆为4个独立论证单元"},
    "revision_structure": [
        {"unit": 1, "name": "分类评价的三种维度",
         "content": "按功能(研究型/应用型/技能型)、按学科(基础/应用/交叉)、按发展阶段(新建/成长/成熟)。每种说明适用政策情境。"},
        {"unit": 2, "name": "弹性框架操作化",
         "content": "刚性标准保底线(学位审核、学科评估)。弹性空间促特色(自主设定指标)。刚性+弹性共存。"},
        {"unit": 3, "name": "实证案例",
         "content": "某省分类评价改革案例，说明实施效果和遇到的问题。"},
        {"unit": 4, "name": "第四节引桥",
         "content": "分类评价是制度平衡的核心抓手。引出第四部分的协同治理进路。"}
    ],
    "citation_map": {"分类标准": "高校分类评价标准", "弹性框架": "刚性vs弹性评价", "试点": "某省改革案例", "国际": "美国卡内基分类/英国REF"}
}
json.dump(m12_r3, open("_reports/m12_round3_strategy.json", "w", encoding="utf-8"), indent=2, ensure_ascii=False)

print("M10 M11 M12 R3 generated. Now CDP submit...")

async def submit_one(mid, data):
    msg = f"## {mid.upper()} R3 FINAL\n\n### Structure ({len(data['revision_structure'])} units):\n"
    for u in data["revision_structure"]:
        msg += f"- {u['name']}: {u['content'][:120]}\n"
    msg += f"\nCitation map: {', '.join(data['citation_map'].keys())}\n"
    msg += f"\nRound 3/3 FINAL. Accept/close? END_OF_GPT_RESPONSE"

    pyperclip.copy(msg)
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
        await page.keyboard.press("Control+Enter")
        await asyncio.sleep(120)
        reply = await page.locator('div[data-message-author-role="assistant"]').last.inner_text()
        v = "PASS" if "pass_with_limitation" in reply else "BLOCKED"
        print(f"  {mid.upper()}: {v}")
        with open(f"_reports/{mid}_round3_gpt_response.txt", "w", encoding="utf-8") as f:
            f.write(reply)

async def main():
    for mid, data in [("m10", m10_r3), ("m11", m11_r3), ("m12", m12_r3)]:
        await submit_one(mid, data)

asyncio.run(main())
