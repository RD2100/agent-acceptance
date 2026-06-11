"""Batch process Sections 2+3 modules (M5-M12)."""
import json, os, sys
os.chdir("D:/agent-acceptance")
sys.path.insert(0, "scripts")
import PyPDF2, paper_c5_full_section_reader as c5, paper_c6_revision_suggester as c6

pdf = r"D:\Program Files\Wechat\Document\xwechat_files\wxid_b47pcpd71t7v22_dbd7\msg\file\2026-06\教育强国战略下高等教育提质扩容的必然逻辑、内在张力与治理进路.pdf"
r = PyPDF2.PdfReader(pdf)
full = "".join(p.extract_text() + "\n" for p in r.pages)
manifest = json.load(open("_reports/c7_module_manifest.json", encoding="utf-8"))

processed = 0
for mod in manifest["modules"]:
    if mod["index"] <= 4: continue  # Skip already-processed Section 1
    mid = f"M{mod['index']}"
    text = mod.get("full_text", "")
    if not text or mod["char_count"] < 200:
        print(f"SKIP {mid}: too short")
        continue

    diag = c5.analyze_section(text, mod["section"][:40])
    strat = c6.generate_suggestions(diag)

    # Generate GPT prompt
    prompt = f"""## {mid} First-Pass Review
Section: {mod['section'][:60]}
Subsection: {mod['subsection'][:60]}
Chars: {mod['char_count']}, Citations: {mod['citation_count']}

### Claude Diagnosis
Issues: {diag.get('structure_issues', [])}
Functions: {diag.get('function_distribution', {})}

### Strategy ({strat['suggestion_count']} suggestions)
"""
    for s in strat.get('suggestions', [])[:5]:
        prompt += f"- [{s.get('type','')}] {s.get('strategy','')[:120]}\n"
    prompt += "\nReview: P0/P1 issues? Return verdict. END_OF_GPT_RESPONSE"

    with open(f"_reports/_c7_gpt_prompt_{mid}_r1.txt", "w", encoding="utf-8") as f:
        f.write(prompt)
    json.dump({"diagnosis": diag, "strategy": strat},
              open(f"_reports/{mid}_round1.json", "w", encoding="utf-8"), indent=2, ensure_ascii=False)

    processed += 1
    print(f"{mid}: {mod['char_count']} chars, {len(diag.get('structure_issues',[]))} issues → prompt saved")

print(f"\n{processed} prompts generated for Sections 2+3")
