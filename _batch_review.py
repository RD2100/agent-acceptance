"""Batch review: M1 + M2 first pass + M4 round 2."""
import json, os, sys
os.chdir("D:/agent-acceptance")
sys.path.insert(0, "scripts")
import PyPDF2, paper_c5_full_section_reader as c5, paper_c6_revision_suggester as c6

pdf = r"D:\Program Files\Wechat\Document\xwechat_files\wxid_b47pcpd71t7v22_dbd7\msg\file\2026-06\教育强国战略下高等教育提质扩容的必然逻辑、内在张力与治理进路.pdf"
r = PyPDF2.PdfReader(pdf)
full = "".join(p.extract_text() + "\n" for p in r.pages)

manifest = json.load(open("_reports/c7_module_manifest.json", encoding="utf-8"))

for mod in manifest["modules"][:4]:  # M1-M4
    mid = f"M{mod['index']}"
    if mod["char_count"] < 200:  # Skip very short modules (section headers)
        print(f"SKIP {mid}: too short ({mod['char_count']} chars)")
        continue

    text = mod.get("full_text", "")
    if not text:
        print(f"SKIP {mid}: no full text")
        continue

    diag = c5.analyze_section(text, mod["section"][:40])
    strat = c6.generate_suggestions(diag)

    prompt = f"""## {mid} First-Pass Review
Section: {mod['section'][:40]}
Subsection: {mod['subsection'][:40]}
Chars: {mod['char_count']}, Citations: {mod['citation_count']}
Functions: {mod['functions']}

### Claude Diagnosis
Paragraphs: {diag['paragraph_count']}
Issues: {diag.get('structure_issues', [])}
Functions: {diag.get('function_distribution', {})}

### Strategy ({strat['suggestion_count']} suggestions)
"""
    for s in strat.get('suggestions', [])[:5]:
        prompt += f"- [{s.get('type','')}] {s.get('strategy','')[:120]}\n"
    prompt += "\nReview: P0/P1 issues? Return verdict. END_OF_GPT_RESPONSE"

    out = f"_reports/_c7_gpt_prompt_{mid}_r1.txt"
    with open(out, "w", encoding="utf-8") as f:
        f.write(prompt)

    # Save results
    json.dump({"diagnosis": diag, "strategy": strat},
              open(f"_reports/{mid}_round1.json", "w", encoding="utf-8"), indent=2, ensure_ascii=False)

    p1 = len(diag.get('structure_issues', []))
    print(f"{mid}: {mod['char_count']} chars, {p1} issues, {strat['suggestion_count']} strategies → {out}")

print("\nAll prompts generated. Ready for CDP submission.")
