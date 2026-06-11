"""M2 Round 3: GPT-guided exact structural revision, same pattern as M3 R3."""
import json, os
os.chdir("D:/agent-acceptance")

m2_r3 = {
    "module": "M2", "round": 3,
    "title_decision": {
        "chosen": "rewrite_title_add_academic_framing",
        "old": "（一）应然之举：教育强国的双重规定性要求高等教育提质扩容",
        "new": "（一）应然之需：教育强国战略的双重内涵与高等教育提质扩容的内在关联",
        "action": "将政策叙事框架转为学术分析框架。'双重规定性'→'双重内涵'去掉政策口吻"
    },
    "revision_structure": [
        {"unit": 1, "name": "双重内涵的学理界定",
         "content": "教育强国的'强'要求高等教育在质量维度具有全球竞争力和创新支撑力。'全'要求高等教育在规模维度实现普及化覆盖和公平化供给。两者构成教育强国的内涵统一体而非简单政策并列。",
         "citations_needed": ["教育强国内涵研究文献2-3篇"]},
        {"unit": 2, "name": "双重内涵向高等教育的传导机制",
         "content": "传导路径一：战略需求→学科布局调整→人才培养模式改革。传导路径二：规模覆盖→资源投入增长→质量保障体系强化。每个路径需要1个具体案例或数据支撑。",
         "citations_needed": ["高等教育结构优化研究1-2篇", "高等教育资源配置效率研究1篇"]},
        {"unit": 3, "name": "从内涵规定到张力显现的逻辑过渡",
         "content": "双重内涵在逻辑上构成统一体，但在现实推进中必然产生公平与效率、涵盖与卓越、统一与差异等结构性张力。这与第二节的内在张力分析形成直接衔接。",
         "citations_needed": ["教育公平与效率关系理论文献1-2篇"]}
    ],
    "citation_function_map": {
        "教育强国理论研究": "二十大报告、教育强国规划纲要中关于高等教育定位的论述",
        "规模-质量关系研究": "高等教育大众化/普及化阶段规模扩张与质量保障的学术文献",
        "制度传导研究": "政策→制度→行为传导机制的高等教育治理文献",
        "国际比较": "OECD国家高等教育规模与质量协同发展的比较研究",
        "历史数据": "中国高等教育毛入学率、高校数量、在学规模等时间序列数据"
    },
    "p1_resolution": {
        "M2-P1-01": "标题已从政策口吻改为学术分析框架",
        "M2-P1-02": "双向传导机制已明确：战略需求→学科调整→培养改革；规模覆盖→资源增长→质量保障",
        "M2-P1-03": "引用功能地图5类，每类对应1-3条具体文献需求"
    },
    "status": "submitted_for_gpt_review_final_round"
}

json.dump(m2_r3, open("_reports/m2_round3_strategy.json", "w", encoding="utf-8"), indent=2, ensure_ascii=False)
print("M2 R3: 3-unit structure + mechanism chain + 5-category citation map")
for p1, resolution in m2_r3["p1_resolution"].items():
    print(f"  {p1}: {resolution[:80]}")
