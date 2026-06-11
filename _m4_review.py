"""M4 first-pass review: Generate GPT prompt for Module M4."""
import json, os, sys
os.chdir("D:/agent-acceptance")
sys.path.insert(0, "scripts")
import PyPDF2, paper_c5_full_section_reader as c5, paper_c6_revision_suggester as c6

pdf = r"D:\Program Files\Wechat\Document\xwechat_files\wxid_b47pcpd71t7v22_dbd7\msg\file\2026-06\教育强国战略下高等教育提质扩容的必然逻辑、内在张力与治理进路.pdf"
r = PyPDF2.PdfReader(pdf)
full = "".join(p.extract_text() + "\n" for p in r.pages)
m4_text = c5.extract_section(full, "一、高等教育提质扩容的必然逻辑")
idx3 = m4_text.find("（三）")
m4 = m4_text[idx3:] if idx3 > 0 else m4_text

diag = c5.analyze_section(m4, "M4-协同推进-初轮")
strat = c6.generate_suggestions(diag)

# Save
json.dump({"diagnosis": diag, "strategy": strat}, open("_reports/m4_round1.json", "w", encoding="utf-8"), indent=2, ensure_ascii=False)

# Generate GPT prompt
prompt = f"""## M4 First-Pass Review
Section: 高等教育提质扩容的必然逻辑 - （三）协同推进
Chars: {diag['paragraph_count']} paragraphs

### Claude Diagnosis
Issues: {diag.get('structure_issues', [])}
Functions: {diag.get('function_distribution', {})}

### Revision Strategy ({strat['suggestion_count']} suggestions)
"""
for s in strat['suggestions']:
    prompt += f"- [{s['type']}] {s['strategy'][:120]}\n"

prompt += "\nReview: Any P0/P1 issues missed? Return verdict. END_OF_GPT_RESPONSE"

with open("_reports/_c7_gpt_prompt_m4_r1.txt", "w", encoding="utf-8") as f:
    f.write(prompt)

print(f"M4: {diag['paragraph_count']} paragraphs, {len(diag.get('structure_issues', []))} issues, {strat['suggestion_count']} strategies")
print("GPT prompt saved")
