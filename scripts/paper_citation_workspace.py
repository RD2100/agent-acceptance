#!/usr/bin/env python3
"""
paper_citation_workspace.py — Local citation function map and gap analyzer.
Works with user-provided BibTeX/Zotero export. No remote API required.
"""
import json, re, sys
from pathlib import Path
from datetime import datetime, timezone
from collections import Counter

REPO = Path(__file__).resolve().parent.parent

CITATION_TYPES = {
    "methodology": ["方法论", "方法", "模型", "框架", "approach", "method", "framework", "model"],
    "empirical": ["实证", "数据", "统计", "调查", "实验", "data", "empirical", "survey", "experiment"],
    "theoretical": ["理论", "概念", "定义", "范式", "theory", "concept", "definition", "paradigm"],
    "comparative": ["对比", "比较", "差异", "优于", "vs", "compared", "versus"],
    "policy": ["政策", "法规", "制度", "文件", "规划", "policy", "regulation", "law"],
}


def analyze_from_modules(manifest_path: str) -> dict:
    """Analyze citation patterns across paper modules from module manifest."""
    manifest = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
    modules = manifest.get("modules", [])

    result = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_citations": sum(m["citation_count"] for m in modules),
        "modules_with_zero_citations": [],
        "modules_below_threshold": [],
        "citation_gap_map": [],
        "recommended_citation_types": {},
    }

    for mod in modules:
        mid = f"M{mod['index']}"
        citations = mod["citation_count"]
        chars = mod["char_count"]

        # Zero citations
        if citations == 0:
            result["modules_with_zero_citations"].append({
                "id": mid, "section": mod["section"][:40],
                "subsection": mod["subsection"][:40], "chars": chars
            })

        # Below threshold (1 citation per 500 chars)
        expected = max(1, chars // 500)
        if citations < expected:
            result["modules_below_threshold"].append({
                "id": mid, "current": citations, "expected": expected, "chars": chars
            })

        # Recommended citation types based on module function
        funcs = mod.get("functions", [])
        needs = []
        if "规范性/政策建议" in funcs:
            needs.extend(["policy", "empirical"])
        if "阐述/论证" in funcs:
            needs.extend(["theoretical", "methodology"])
        if "实证/案例" in funcs:
            needs.extend(["empirical", "comparative"])
        if needs:
            result["recommended_citation_types"][mid] = list(set(needs))

        # Gap map
        if citations < expected:
            result["citation_gap_map"].append({
                "id": mid,
                "gap": expected - citations,
                "suggested_types": result["recommended_citation_types"].get(mid, ["theoretical"]),
                "priority": "P1" if citations == 0 else "P2",
            })

    return result


def render_markdown(analysis: dict) -> str:
    lines = ["# Citation Function Map & Gap Analysis", "",
             f"Total citations: {analysis['total_citations']}",
             f"Modules with zero citations: {len(analysis['modules_with_zero_citations'])}",
             f"Modules below threshold: {len(analysis['modules_below_threshold'])}",
             f"Citation gaps: {len(analysis['citation_gap_map'])}", ""]

    if analysis["citation_gap_map"]:
        lines.append("## Priority Citation Gaps")
        for g in sorted(analysis["citation_gap_map"], key=lambda x: x["priority"]):
            types = ", ".join(g["suggested_types"])
            lines.append(f"- [{g['priority']}] {g['id']}: need {g['gap']} more citations ({types})")

    if analysis["recommended_citation_types"]:
        lines.append("")
        lines.append("## Per-Module Citation Recommendations")
        for mid, types in analysis["recommended_citation_types"].items():
            lines.append(f"- {mid}: {', '.join(types)}")

    lines.append("")
    lines.append("> Citation workspace analysis only. Does NOT generate citations automatically.")
    return "\n".join(lines)


def main():
    if len(sys.argv) < 2:
        print("Usage: paper_citation_workspace.py <module_manifest.json>")
        sys.exit(1)

    analysis = analyze_from_modules(sys.argv[1])

    out = REPO / "_reports" / "PAPER_CITATION_WORKSPACE.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(analysis, indent=2, ensure_ascii=False), encoding="utf-8")

    md = render_markdown(analysis)
    md_out = REPO / "_reports" / "PAPER_CITATION_WORKSPACE.md"
    md_out.write_text(md, encoding="utf-8")

    print(f"Citation gaps: {len(analysis['citation_gap_map'])}")
    print(f"Zero-citation modules: {len(analysis['modules_with_zero_citations'])}")
    print(f"Report: {md_out}")


if __name__ == "__main__":
    main()
