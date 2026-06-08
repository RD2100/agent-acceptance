#!/usr/bin/env python3
"""
paper_c6_revision_suggester.py — Bounded revision suggestion generator.
Takes C5 structural diagnosis + C4 review result, generates concrete revision strategies.
Does NOT generate full rewrites. Only strategies, transition examples, and compression hints.
"""
import json, sys
from pathlib import Path
from datetime import datetime, timezone

REPO = Path(__file__).resolve().parent.parent


def generate_suggestions(c5_result: dict, c4_result: dict = None) -> dict:
    """Generate bounded revision suggestions from structural diagnosis."""
    suggestions = []
    func_dist = c5_result.get("function_distribution", {})
    para_diags = c5_result.get("paragraph_diagnoses", [])
    paras_count = c5_result.get("paragraph_count", 0)

    # 1. Overlong paragraphs → compression strategy
    overlong = [p for p in para_diags if "overlong" in p.get("functions", [])]
    if overlong:
        for p in overlong[:3]:
            suggestions.append({
                "type": "compression",
                "target": f"P{p['index']}",
                "current_chars": p["char_count"],
                "strategy": f"该段{p['char_count']}字，建议压缩至{p['char_count']//2}字以内。方法：提取1个核心论点，将支撑性论证移至脚注或附录",
                "example": None  # Don't generate rewrite — only strategy
            })

    # 2. Missing citations → evidence strategy
    uncited = [p for p in para_diags if p.get("citation_count", 0) == 0 and p["char_count"] > 300]
    if uncited:
        suggestions.append({
            "type": "evidence_gap",
            "target": ", ".join(f"P{p['index']}" for p in uncited[:3]),
            "count": len(uncited),
            "strategy": f"发现{len(uncited)}个长段落缺少引用。建议：(1)每个事实性陈述补充1个文献支撑 (2)每个方法论选择补充1个方法论文献 (3)每个对立观点补充1个对比文献",
        })

    # 3. High expository ratio → topic sentence strategy
    expo_count = func_dist.get("expository", 0)
    if expo_count > 0 and paras_count > 0:
        ratio = expo_count / paras_count
        if ratio > 0.2:
            suggestions.append({
                "type": "topic_sentence",
                "ratio": f"{ratio:.0%}",
                "strategy": f"阐述性段落占比{ratio:.0%}，功能不够明确。建议每段首句改为明确的主题句，直接陈述该段的论证功能（如'本节论证X的三个理由'），而非单纯叙述",
            })

    # 4. Evidence density → balance strategy
    evidence_count = func_dist.get("evidence", 0)
    if evidence_count < paras_count * 0.3:
        suggestions.append({
            "type": "evidence_balance",
            "current": evidence_count,
            "target": max(1, paras_count // 3),
            "strategy": "实证段落占比偏低。建议每3段至少包含1处数据引用或案例支撑",
        })

    # 5. Prescriptive ratio → academic balance
    presc_count = func_dist.get("prescriptive", 0)
    if presc_count > paras_count * 0.4:
        suggestions.append({
            "type": "prescriptive_balance",
            "current": presc_count,
            "ratio": f"{presc_count/paras_count:.0%}",
            "strategy": f"规范性/政策建议段落占比{presc_count/paras_count:.0%}，偏高。建议压缩至总段数的30%以内，将腾出的空间用于理论分析和实证验证",
        })

    # 6. Transition examples (without reading the original text)
    if paras_count >= 3:
        suggestions.append({
            "type": "transition_example",
            "strategy": "段落间衔接建议：在每段末尾添加1句过渡句，预告下一段的论证方向。示例模板：'以上分析了X的三个方面，下文将从Y角度进一步探讨其深层原因'",
            "template": "以上分析了{current_topic}，下文将从{next_topic}角度进一步探讨。",
        })

    return {
        "task_id": c5_result.get("task_id", "unknown"),
        "section_name": c5_result.get("section_name", ""),
        "suggestions": suggestions,
        "suggestion_count": len(suggestions),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "disclaimer": "仅提供修改策略和模板，不生成具体改写文本。用户需自行完成修改。",
    }


def main():
    if len(sys.argv) < 2:
        print("Usage: paper_c6_revision_suggester.py <c5_analysis.json> [c4_review.json]")
        sys.exit(1)

    c5_result = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    c4_result = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8")) if len(sys.argv) > 2 else None

    result = generate_suggestions(c5_result, c4_result)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    sys.exit(0)


if __name__ == "__main__":
    main()
