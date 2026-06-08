#!/usr/bin/env python3
"""
paper_proofreading_gate.py — Rule-based proofreading and format checker.
Checks: heading levels, abstract/keywords format, reference placeholders,
word count, sentence length, policy term density. No AI model needed.
"""
import re, json, sys
from pathlib import Path
from datetime import datetime, timezone

REPO = Path(__file__).resolve().parent.parent


def check(text: str, section_name: str = "") -> dict:
    issues = []
    warnings = []

    # 1. Heading level consistency
    h1 = len(re.findall(r'^[一二三四五六七八九十]、', text, re.MULTILINE))
    h2 = len(re.findall(r'^（[一二三四五六七八九十]）', text, re.MULTILINE))
    if h1 == 0 and h2 == 0:
        issues.append({"type": "heading", "severity": "P1", "detail": "No numbered headings found"})

    # 2. Long sentence detection
    sentences = re.split(r'[。！？]', text)
    long_sentences = [s for s in sentences if len(s) > 150]
    if long_sentences:
        warnings.append({"type": "long_sentence", "severity": "P2", "count": len(long_sentences),
                         "detail": f"{len(long_sentences)} sentences exceed 150 chars"})

    # 3. Reference placeholder check
    refs = re.findall(r'\[\d+\]', text)
    placeholders = re.findall(r'\[TODO\]|\[待补\]|\[?\]|\[citation needed\]|\[需要引用\]', text, re.IGNORECASE)
    if placeholders:
        issues.append({"type": "placeholder", "severity": "P1", "detail": f"Found {len(placeholders)} reference placeholders: {placeholders[:3]}"})

    # 4. Policy term density
    policy_terms = re.findall(r'(教育强国|高等教育|治理|战略|体系|制度|机制|改革|发展|建设|创新)', text)
    density = len(policy_terms) / max(len(text), 1) * 1000
    if density > 30:
        warnings.append({"type": "policy_density", "severity": "P2",
                         "detail": f"Policy term density: {density:.0f}/1000 chars (high)"})

    # 5. Repeated phrases
    words = re.findall(r'[\u4e00-\u9fff]{4,8}', text)
    word_freq = {}
    for w in words:
        word_freq[w] = word_freq.get(w, 0) + 1
    repeated = {w: c for w, c in word_freq.items() if c > 10}
    if repeated:
        top3 = sorted(repeated.items(), key=lambda x: -x[1])[:3]
        warnings.append({"type": "repetition", "severity": "P3", "detail": f"Repeated phrases: {top3}"})

    # 6. Abstract/keywords format (if applicable)
    abstract = re.search(r'摘要[\s：:]*(.{50,500})', text)
    keywords = re.search(r'关键词[\s：:]*(.{10,100})', text)
    if abstract and not keywords:
        warnings.append({"type": "metadata", "severity": "P2", "detail": "Abstract found but no keywords"})

    # 7. Char count
    chars = len(text)
    if chars < 500:
        warnings.append({"type": "length", "severity": "P3", "detail": f"Section too short: {chars} chars"})

    has_p0 = any(i["severity"] == "P0" for i in issues)
    has_p1 = any(i["severity"] == "P1" for i in issues)

    return {
        "section": section_name,
        "chars": chars,
        "citations": len(refs),
        "policy_density": round(density, 1),
        "p0_issues": [i for i in issues if i["severity"] == "P0"],
        "p1_issues": [i for i in issues if i["severity"] == "P1"],
        "warnings": warnings,
        "pass": not has_p0,
        "recommendation": "blocked" if has_p0 else ("review" if has_p1 else "pass"),
        "checked_at": datetime.now(timezone.utc).isoformat(),
    }


def main():
    if len(sys.argv) < 2:
        print("Usage: paper_proofreading_gate.py <text_file_or_'modules'>")
        sys.exit(1)

    if sys.argv[1] == "modules":
        # Check all modules from manifest
        manifest = json.loads(Path("_reports/c7_module_manifest.json").read_text(encoding="utf-8"))
        all_results = []
        for mod in manifest["modules"]:
            text = mod.get("full_text", "")
            if text:
                r = check(text, mod["section"][:40])
                all_results.append(r)
                status = r["recommendation"]
                p1 = len(r["p1_issues"])
                print(f"[{status}] M{mod['index']}: {r['chars']} chars, {p1} P1 issues, {len(r['warnings'])} warnings")
        with open("_reports/PAPER_PROOFREADING_REPORT.json", "w", encoding="utf-8") as f:
            json.dump(all_results, f, indent=2, ensure_ascii=False)
        print(f"\nReport: _reports/PAPER_PROOFREADING_REPORT.json")
    else:
        text = Path(sys.argv[1]).read_text(encoding="utf-8")
        result = check(text, sys.argv[1])
        print(json.dumps(result, indent=2, ensure_ascii=False))
        sys.exit(0 if result["pass"] else 1)


if __name__ == "__main__":
    main()
