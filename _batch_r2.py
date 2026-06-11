"""Generate round 2 strategies for M2 and M4 — GPT-guided structural revision."""
import json, os
os.chdir("D:/agent-acceptance")

# M2 Round 2: address 3 P1 issues (from GPT response)
m2_r2 = {
    "module": "M2",
    "round": 2,
    "title_decision": {
        "chosen": "rewrite_title",
        "old": "（一）应然之举：教育强国的双重规定性要求高等教育提质扩容",
        "new": "（一）应然之需：教育强国的双重规定及其对高等教育的提质扩容要求",
        "action": "将'之举'改为'之需'，弱化规范性语气，增强学术分析性"
    },
    "revision_structure": [
        {"unit": 1, "name": "双重规定性的内涵界定",
         "strategy": "从政策文本分析转入学术分析：教育强国的'强'=质量维度，'全'=规模维度。二者不是简单的政策并列，而是教育发展的内在逻辑。"},
        {"unit": 2, "name": "双重规定性对高等教育的传导机制",
         "strategy": "政策要求→制度传导→高校行为改变。需要增加1个案例说明具体的传导路径。"},
        {"unit": 3, "name": "从应然到实然的过渡",
         "strategy": "双重规定性提出了应然要求，但现实中二者存在张力。这自然过渡到第二节的内在张力分析。"}
    ],
    "citation_function_map": {
        "政策文本": "教育强国建设规划纲要、二十大报告等政策文件对高等教育的定位",
        "理论研究": "高等教育规模-质量关系的学术研究",
        "历史经验": "中国高等教育从精英化到普及化的规模扩张历程数据",
        "国际比较": "主要发达国家高等教育规模与质量协同发展的经验"
    },
    "status": "submitted_for_gpt_review"
}

# M4 Round 2: address 3 P1 issues from GPT (协同推进 lacks mechanism)
m4_r2 = {
    "module": "M4",
    "round": 2,
    "mechanism_fix": {
        "issue": "协同推进只是规范性表述，缺乏机制化说明",
        "fix": "具体化协同推进的三个维度：政策协同（中央与地方）、资源协同（财政与社会投入）、评价协同（政府部门与学术评价）"
    },
    "revision_structure": [
        {"unit": 1, "name": "协同推进的政策维度",
         "strategy": "中央顶层设计+地方差异化实施。增加1个省级政策案例。"},
        {"unit": 2, "name": "协同推进的资源维度",
         "strategy": "财政投入+社会资本+国际资源的多渠道经费保障机制。"},
        {"unit": 3, "name": "协同推进的评价维度",
         "strategy": "政府评估+学术评价+社会反馈的三维质量保障体系。"},
        {"unit": 4, "name": "向第四节治理进路过渡",
         "strategy": "协同推进需要具体的治理架构支撑，引出下一节。"}
    ],
    "citation_function_map": {
        "政策协同研究": "央地教育治理关系研究",
        "资源多元化": "高等教育经费来源结构研究",
        "评价改革": "新时代教育评价改革政策与实践"
    },
    "status": "submitted_for_gpt_review"
}

json.dump(m2_r2, open("_reports/m2_round2_strategy.json", "w", encoding="utf-8"), indent=2, ensure_ascii=False)
json.dump(m4_r2, open("_reports/m4_round2_strategy.json", "w", encoding="utf-8"), indent=2, ensure_ascii=False)
print("M2 R2: 3-unit revision + citation map")
print("M4 R2: 4-unit mechanism fix + citation map")
