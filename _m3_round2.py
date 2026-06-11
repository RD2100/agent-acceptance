import json, os, sys
os.chdir("D:/agent-acceptance")
sys.path.insert(0, "scripts")
import PyPDF2, paper_c5_full_section_reader as c5, paper_c6_revision_suggester as c6

pdf = r"D:\Program Files\Wechat\Document\xwechat_files\wxid_b47pcpd71t7v22_dbd7\msg\file\2026-06\教育强国战略下高等教育提质扩容的必然逻辑、内在张力与治理进路.pdf"
r = PyPDF2.PdfReader(pdf)
full = "".join(p.extract_text() + "\n" for p in r.pages)
m3_text = c5.extract_section(full, "一、高等教育提质扩容的必然逻辑")
idx2 = m3_text.find("（二）")
m3_sub2 = m3_text[idx2:] if idx2 > 0 else m3_text

diag = c5.analyze_section(m3_sub2, "M3-实然之境-第二轮")
strat = c6.generate_suggestions(diag)
strat["addressing_gpt_p1_issues"] = [
    {"issue": "M3-P1-01", "fix": "将标题从实然之境改为实然之困，或重写内容为正面论证实然层面的统一性"},
    {"issue": "M3-P1-02", "fix": "明确阐述内在统一性的具体机制：规模扩张如何倒逼质量提升？质量提升如何为规模扩张提供合法性？"},
    {"issue": "M3-P1-03", "fix": "补充3-5个高等教育研究文献：方法论文献1个，比较研究1个，实证数据1个"}
]

json.dump(strat, open("_reports/m3_round2_strategy.json", "w", encoding="utf-8"), indent=2, ensure_ascii=False)
print(f"Round 2: {strat['suggestion_count']} suggestions + 3 P1 fixes")
for fix in strat["addressing_gpt_p1_issues"]:
    print(f"  {fix['issue']}: {fix['fix'][:60]}")
