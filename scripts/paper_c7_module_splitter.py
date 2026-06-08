#!/usr/bin/env python3
"""
paper_c7_module_splitter.py — Split paper into sub-modules for iterative review.
Outputs module manifest with section boundaries and argument function labels.
"""
import re, json, sys, PyPDF2
from pathlib import Path
from datetime import datetime, timezone

REPO = Path(__file__).resolve().parent.parent

LEVEL1_PATTERN = re.compile(r'^[一二三四五六七八九十]、')
LEVEL2_PATTERN = re.compile(r'^（[一二三四五六七八九十]）')


def split(pdf_path: str) -> dict:
    """Split paper into sub-modules. Returns structured manifest."""
    r = PyPDF2.PdfReader(pdf_path)
    full_text = ""
    for p in r.pages:
        t = p.extract_text()
        if t: full_text += t + "\n"

    modules = []
    current_l1 = None
    current_l2 = None
    current_text = []

    lines = full_text.split('\n')
    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Level 1 header
        l1_match = LEVEL1_PATTERN.match(line)
        if l1_match and len(line) > 5:
            # Save previous module
            if current_l1 and current_text:
                modules.append(_build_module(current_l1, current_l2, '\n'.join(current_text), len(modules)+1))
            current_l1 = line
            current_l2 = None
            current_text = []
            continue

        # Level 2 header
        l2_match = LEVEL2_PATTERN.match(line)
        if l2_match and current_l1:
            if current_text:
                modules.append(_build_module(current_l1, current_l2, '\n'.join(current_text), len(modules)+1))
            current_l2 = line
            current_text = []
            continue

        current_text.append(line)

    # Last module
    if current_text:
        modules.append(_build_module(current_l1, current_l2, '\n'.join(current_text), len(modules)+1))

    return {
        "paper_title": _extract_title(full_text),
        "total_modules": len(modules),
        "total_chars": sum(m["char_count"] for m in modules),
        "modules": modules,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


def _build_module(l1: str, l2: str, text: str, idx: int) -> dict:
    char_count = len(text)
    # Detect argument function from first 200 chars
    functions = []
    text_head = text[:200]
    if re.search(r'(首先|第一|第一个|其一)', text_head): functions.append("开篇/总论")
    if re.search(r'(例如|比如|如表|数据显示|据统计|以.*为例)', text_head): functions.append("实证/案例")
    if re.search(r'(因此|所以|综上|由此可见|总之)', text_head): functions.append("结论/总结")
    if re.search(r'(应当|需要|必须|建议|应|要)', text_head) and char_count > 300: functions.append("规范性/政策建议")
    if re.search(r'(然而|但是|尽管|不过|另一方面)', text_head): functions.append("转折/对立论点")
    if len(functions) == 0: functions.append("阐述/论证")

    # Citation count
    citations = len(re.findall(r'\[\d+\]', text))

    return {
        "index": idx,
        "section": l1 or "(引言)",
        "subsection": l2 or "",
        "char_count": char_count,
        "start_preview": text[:80].replace('\n', ' '),
        "functions": functions,
        "citation_count": citations,
        "full_text": text,
    }


def _extract_title(text: str) -> str:
    lines = text.split('\n')[:5]
    for line in lines:
        line = line.strip()
        if len(line) > 10 and '摘要' not in line:
            return line[:100]
    return "(未识别标题)"


def main():
    if len(sys.argv) < 2:
        print("Usage: paper_c7_module_splitter.py <pdf_path> [output_json]")
        sys.exit(1)

    result = split(sys.argv[1])

    if len(sys.argv) > 2:
        Path(sys.argv[2]).parent.mkdir(parents=True, exist_ok=True)
        Path(sys.argv[2]).write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")

    # Print summary
    print(f"Paper: {result['paper_title'][:80]}")
    print(f"Modules: {result['total_modules']}")
    print(f"Total chars: {result['total_chars']}")
    for m in result['modules']:
        func = ','.join(m['functions'])
        print(f"  M{m['index']}: [{m['section'][:20]}] {m['subsection'][:20]} ({m['char_count']}字) [{func}] {m['citation_count']} refs")
    sys.exit(0)


if __name__ == "__main__":
    main()
