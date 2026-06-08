#!/usr/bin/env python3
"""
paper_c5_full_section_reader.py — Full-text section structural reader.
Reads actual section text, generates paragraph-level function map + structural diagnosis.
Ephemeral processing — does NOT store original text in output.
"""
import re, sys, json
from pathlib import Path
from datetime import datetime, timezone

REPO = Path(__file__).resolve().parent.parent


def extract_section(text: str, section_header: str) -> str:
    """Extract a single section's text from full paper."""
    # Find the section header
    idx = text.find(section_header)
    if idx < 0:
        return ""
    section_text = text[idx:]

    # Find next section boundary (一、二、三、四、五)
    next_section = re.search(r'\n[二三四五六七八九十]、', section_text[len(section_header)+1:])
    if next_section:
        section_text = section_text[:len(section_header) + 1 + next_section.start()]

    return section_text.strip()


def split_paragraphs(text: str) -> list[dict]:
    """Split section text into paragraphs with metadata."""
    # Remove the section header line
    lines = text.split('\n')
    body_start = 0
    for i, line in enumerate(lines):
        if re.match(r'^[一二三四五六七八九十]、', line.strip()):
            body_start = i
            break

    body = '\n'.join(lines[body_start+1:])

    # Normalize PDF line breaks: single newline within text = PDF artifact, not para break.
    # Real paragraph breaks are: double newlines, sub-section headers, or indentation changes.
    body = re.sub(r'([^。\n])\n([^ \n（])', r'\1\2', body)  # Join broken lines within sentences

    # Split by sub-section headers first
    sub_sections = re.split(r'\n(?=（[一二三四五六七八九十]）)', body)
    paragraphs = []
    for ss in sub_sections:
        ss = ss.strip()
        if not ss or len(ss) < 30:
            continue
        # Split by natural paragraph markers
        chunks = re.split(r'\n{2,}', ss)  # Double newlines = real paragraph breaks
        for chunk in chunks:
            chunk = chunk.strip()
            if len(chunk) >= 100:  # Minimum paragraph size for meaningful analysis
                paragraphs.append(chunk)
        if not chunks and len(ss) >= 100:
            paragraphs.append(ss)

    result = []
    for i, para in enumerate(paragraphs):
        para = para.strip()
        if len(para) < 20:  # Skip very short fragments
            continue
        result.append({
            "index": len(result) + 1,
            "char_count": len(para),
            "starts_with": para[:50].replace('\n', ' '),
            # Don't include full text
        })
    return result


def diagnose_paragraph(para_text: str, para_index: int, total_paras: int) -> dict:
    """Analyze a single paragraph's argument function. Returns diagnosis only."""
    functions = []
    details = []

    # Position-based
    if para_index == 1:
        functions.append("opening")
        details.append("开场段落——应承担问题引入或背景铺垫功能")
    elif para_index == total_paras:
        functions.append("closing")
        details.append("结尾段落——应承担总结或过渡功能")
    elif para_index == 2:
        functions.append("definitional")
        details.append("第二段通常承担核心概念界定功能")

    # Length-based
    if len(para_text) > 800:
        functions.append("overlong")
        details.append(f"段落过长({len(para_text)}字)——可能混合多个论点，建议拆分为2-3段")
    elif len(para_text) < 100:
        functions.append("underdeveloped")
        details.append(f"段落过短({len(para_text)}字)——论证展开不充分")

    # Content-based (Heuristic)
    if re.search(r'(首先|第一|一方面)', para_text[:200]):
        functions.append("transition")
    if re.search(r'(例如|比如|如表|如图|数据显示|据统计)', para_text):
        functions.append("evidence")
        details.append("包含实证数据或案例引用")
    if re.search(r'(因此|所以|由此可见|综上|总之)', para_text):
        functions.append("conclusion")
    if re.search(r'(然而|但是|尽管|不过|另一方面)', para_text[:200]):
        functions.append("counterpoint")
        details.append("包含转折或对立论点")
    if re.search(r'(应当|需要|必须|建议|应|要)', para_text[:200]) and len(para_text) > 200:
        functions.append("prescriptive")
        details.append("包含规范性/政策建议表述")

    # Citation check
    citations = re.findall(r'\[\d+\]', para_text)
    if len(citations) == 0 and len(para_text) > 300:
        details.append("警告：本段超过300字但无引用标记——可能需要补充文献支撑")
    elif len(citations) >= 3:
        functions.append("citation_dense")
        details.append(f"引用密集({len(citations)}处)——确认非简单堆砌")

    # Concept density
    policy_terms = len(re.findall(r'(教育强国|高等教育|治理|战略|体系|制度)', para_text))
    if policy_terms > 10:
        details.append(f"政策术语密度高({policy_terms}次)——检查是否做了学理化转换")

    if not functions:
        functions.append("expository")
        details.append("阐述性段落——功能不明确，建议明确论证角色")

    return {
        "index": para_index,
        "char_count": len(para_text),
        "functions": functions,
        "diagnosis": details,
        "citation_count": len(citations),
        "policy_term_density": policy_terms if policy_terms > 5 else None,
    }


def analyze_section(text: str, section_name: str) -> dict:
    """Full analysis of a section. Returns diagnosis only, no original text."""
    paragraphs = split_paragraphs(text)
    para_diagnoses = []

    for p in paragraphs:
        idx = p["index"] - 1
        # Re-run the same split logic used in split_paragraphs
        body = text.split('\n', 1)[1] if '\n' in text else text
        body = re.sub(r'([^。\n])\n([^ \n（])', r'\1\2', body)
        ss_list = re.split(r'\n(?=（[一二三四五六七八九十]）)', body)
        all_texts = []
        for ss in ss_list:
            ss = ss.strip()
            if not ss or len(ss) < 30: continue
            chunks = re.split(r'\n{2,}', ss)
            for chunk in chunks:
                chunk = chunk.strip()
                if len(chunk) >= 100:
                    all_texts.append(chunk)
            if not chunks and len(ss) >= 100:
                all_texts.append(ss)
        full_para = all_texts[idx] if idx < len(all_texts) else ""

        diag = diagnose_paragraph(full_para, p["index"], len(paragraphs))
        para_diagnoses.append(diag)

    # Cross-paragraph analysis
    structure_issues = []
    function_sequence = []
    for pd in para_diagnoses:
        function_sequence.extend(pd["functions"])

    # Check for too many overlong paragraphs
    overlong_count = sum(1 for pd in para_diagnoses if "overlong" in pd["functions"])
    if overlong_count > len(para_diagnoses) * 0.3:
        structure_issues.append(f"段落过长问题突出：{overlong_count}/{len(para_diagnoses)}段超过800字")

    # Check for missing citations across all paragraphs
    uncited = sum(1 for pd in para_diagnoses if pd["citation_count"] == 0 and pd["char_count"] > 300)
    if uncited > 0:
        structure_issues.append(f"{uncited}个长段落缺少引用支撑")

    # Function distribution
    func_dist = {}
    for f in function_sequence:
        func_dist[f] = func_dist.get(f, 0) + 1

    return {
        "section_name": section_name,
        "paragraph_count": len(para_diagnoses),
        "total_chars": len(text),
        "paragraph_diagnoses": para_diagnoses,
        "function_distribution": func_dist,
        "structure_issues": structure_issues,
        "summary": _generate_summary(para_diagnoses, structure_issues, func_dist),
        "analyzed_at": datetime.now(timezone.utc).isoformat(),
    }


def _generate_summary(paras: list, issues: list, func_dist: dict) -> str:
    """Generate human-readable summary."""
    parts = []
    parts.append(f"本节共{len(paras)}段，总字数约{sum(p['char_count'] for p in paras)}字。")
    if issues:
        parts.append("结构问题：" + "；".join(issues[:3]))
    parts.append(f"论证功能分布：{json.dumps(func_dist, ensure_ascii=False)}。")
    return "".join(parts)


def main():
    if len(sys.argv) < 2:
        print("Usage: paper_c5_full_section_reader.py <section_text_file> [section_name]")
        sys.exit(1)

    text = Path(sys.argv[1]).read_text(encoding="utf-8")
    section_name = sys.argv[2] if len(sys.argv) > 2 else "未命名章节"

    result = analyze_section(text, section_name)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    sys.exit(0 if not result["structure_issues"] else 0)  # Always exit 0 — issues are findings, not failures


if __name__ == "__main__":
    main()
