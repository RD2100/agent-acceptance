"""Generate R2 strategies for all blocked modules: M7, M8, M10, M11, M12."""
import json, os
os.chdir("D:/agent-acceptance")

strategies = {
    "M7": {
        "module": "M7", "round": 2,
        "section": "普惠与卓越的二元悖论",
        "p1_resolution": [
            {"id": "M7-P1-01", "action": "明确区分'普惠'和'卓越'在高等教育资源分配中的操作化定义——普惠=生均拨款+均等化分配，卓越=竞争性经费+择优支持"},
            {"id": "M7-P1-02", "action": "补充中央与地方高校经费差距的具体数据，将'中央部属高校生均经费是地方高校的1倍多'转化为可验证的统计"},
            {"id": "M7-P1-03", "action": "分析普惠与卓越悖论的结构性根源：财政分权+分级管理+资源稀缺三者叠加，不只是'两个导向的矛盾'"},
            {"id": "M7-P1-04", "action": "从M6的公平/效率价值博弈自然过渡到M7的资源分配悖论，说明这是同一问题的不同维度"}
        ],
        "revision_structure": [
            {"unit": 1, "name": "操作化界定", "content": "将普惠和卓越从抽象价值转化为具体制度安排。普惠=生均拨款机制。卓越=竞争性项目经费机制。"},
            {"unit": 2, "name": "数据论证", "content": "2021-2024年中央1.02万亿vs地方2.76万亿，但部属高校生均经费远高于地方。展示结构性不均衡。"},
            {"unit": 3, "name": "结构性根源", "content": "财政分权体制+央地分级管理+资源总量约束→普惠与卓越张力不可消解，只能动态平衡。"},
            {"unit": 4, "name": "向M8过渡", "content": "资源配置张力最终反映为评价体系的张力——统一评价与分类评价的矛盾。"}
        ],
        "citation_map": {"财政数据": "教育部年度经费统计", "制度分析": "央地关系与教育财政研究", "比较研究": "OECD国家高等教育拨款模式"}
    },
    "M8": {
        "module": "M8", "round": 2,
        "section": "统一与分类的两难选择",
        "p1_resolution": [
            {"id": "M8-P1-01", "action": "明确提出'统一评价的三大弊端'：同质化诱导+特色消解+质量信号失真。每点对应一个案例"},
            {"id": "M8-P1-02", "action": "补充分类评价的制度供给不足的具体数据：全国有多少省份出台了分类评价标准？覆盖了多少高校？"},
            {"id": "M8-P1-03", "action": "分析马太效应的传导机制：统一评价→资源集中→优者更优→评价更好→弱者更弱。形成恶性循环图。"},
            {"id": "M8-P1-04", "action": "与M6/M7形成论证递进：价值维度(M6)→资源维度(M7)→评价维度(M8)，三重张力层层递进"},
            {"id": "M8-P1-05", "action": "补充一个分类评价的成功案例（如某省或某类高校的评价改革试点）以增加论证的实证性"}
        ],
        "revision_structure": [
            {"unit": 1, "name": "统一评价的三大弊端+案例", "content": "弊端1-3各配一个案例。"},
            {"unit": 2, "name": "分类评价的制度供给现状", "content": "数据+政策文本分析。有多少省份出台了标准？"},
            {"unit": 3, "name": "马太效应的传导机制图", "content": "文字描述+逻辑链条：评价→资源→绩效→评价→..."},
            {"unit": 4, "name": "向M9(第三节)过渡", "content": "三重张力(M6价值/M7资源/M8评价)的总结+指向第三节的平衡之道。"}
        ],
        "citation_map": {"评价数据": "学科评估/大学排名报告", "政策文本": "各省分类评价政策", "案例分析": "某省/某类高校评价改革试点"}
    },
    "M10": {
        "module": "M10", "round": 2,
        "section": "价值平衡",
        "p1_resolution": [{"id": "M10-P1-01", "action": "从'应然'描述转为'路径'分析：如何实现从优先到协同的具体转向？"},
                          {"id": "M10-P1-02", "action": "补充一个价值平衡的实践案例或数据支撑"},
                          {"id": "M10-P1-03", "action": "与M6(公平/效率)形成呼应：第三节的方案回应第二节的问题"}],
        "revision_structure": [{"unit": 1, "name": "转向路径", "content": "从优先到协同的三步路径"}, {"unit": 2, "name": "案例+数据", "content": "实证支撑"}, {"unit": 3, "name": "向M11过渡", "content": "价值平衡引领资源平衡"}],
        "citation_map": {"政策研究": "教育公平与效率平衡研究", "案例": "某地区价值平衡实践"}
    },
    "M11": {
        "module": "M11", "round": 2,
        "section": "资源平衡",
        "p1_resolution": [{"id": "M11-P1-01", "action": "'精准供给'需要操作化定义：精准什么？如何精准？精准到什么程度？当前只用了7次但未定义"},
                          {"id": "M11-P1-02", "action": "与M7(普惠/卓越)形成方案对应：资源平衡是M7张力的解答"}],
        "revision_structure": [{"unit": 1, "name": "精准供给操作化", "content": "定义精准供给的四个维度"}, {"unit": 2, "name": "与M7的对应", "content": "资源平衡如何回应M7的普惠/卓越悖论"}],
        "citation_map": {"资源配置理论": "教育财政精准化研究", "案例": "某省拨款模式改革"}
    },
    "M12": {
        "module": "M12", "round": 2,
        "section": "制度平衡",
        "p1_resolution": [{"id": "M12-P1-01", "action": "拆分7027字为3-4个独立论证单元，避免单段过长"},
                          {"id": "M12-P1-02", "action": "分类评价的操作化路径：从'应该分类'到'如何分类'——给出3-5种分类维度"},
                          {"id": "M12-P1-03", "action": "弹性框架的操作化：刚性标准有哪些？弹性空间在哪里？二者如何共存？"},
                          {"id": "M12-P1-04", "action": "补充制度平衡的实证案例或试点经验"}],
        "revision_structure": [{"unit": 1, "name": "拆分+重组", "content": "将7027字拆为4个独立论证单元"}, {"unit": 2, "name": "分类维度", "content": "3-5种分类维度+适用条件"}, {"unit": 3, "name": "弹性框架", "content": "刚性/弹性并存的操作化方案"}, {"unit": 4, "name": "实证案例", "content": "试点经验"}],
        "citation_map": {"评价改革": "新时代教育评价改革研究", "分类标准": "高校分类评价标准研究", "国际比较": "美国卡内基分类、英国REF等"}
    }
}

for mid, s in strategies.items():
    path = f"_reports/{mid.lower()}_round2_strategy.json"
    json.dump(s, open(path, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    p1_count = len(s["p1_resolution"])
    print(f"{mid} R2: {p1_count} P1 fixes, {len(s['revision_structure'])} units → {path}")

print("\nAll R2 strategies generated. Ready for CDP submission.")
