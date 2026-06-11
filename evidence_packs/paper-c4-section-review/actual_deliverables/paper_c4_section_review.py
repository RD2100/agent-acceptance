#!/usr/bin/env python3
"""
paper_c4_section_review.py — Bounded section review runner.

Accepts sanitized/synthetic section input, runs safety checks,
generates structured diagnosis + revision plan + evidence report.
No real paper ingestion. No Web GPT. No external upload.
"""
import argparse, json, sys, yaml
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

def review(input_path: str) -> dict:
    """Run bounded section review. Returns result dict."""
    fp = Path(input_path)
    if not fp.exists():
        return _blocked("input_not_found", f"file not found: {input_path}")

    # Load input
    try:
        data = yaml.safe_load(fp.read_text(encoding="utf-8"))
    except Exception as e:
        return _blocked("yaml_parse_error", str(e))

    # Validate packet
    from paper_c4_section_packet_validator import validate
    v = validate(data)
    if not v["valid"]:
        return _blocked("validation_failed", "; ".join(v["errors"]))

    mode = v["privacy_mode"]
    task_id = data["task_id"]
    section = data.get("target_section_name","unknown")

    # Generate bounded diagnosis (rule-based, no LLM)
    diagnosis = _diagnose(data)
    priorities = _revision_priorities(data)
    structure = _suggest_structure(data)
    privacy_limits = _privacy_limits(mode)

    return {
        "task_id": task_id,
        "input_privacy_mode": mode,
        "safety_status": "PASS",
        "review_allowed": True,
        "target_section_name": section,
        "diagnosis": diagnosis,
        "revision_priorities": priorities,
        "suggested_structure": structure,
        "argument_continuity_notes": _argument_notes(data),
        "citation_or_evidence_needs": _citation_needs(data),
        "privacy_limitations": privacy_limits,
        "blocked_reasons": [],
        "next_recommended_human_action": _next_action(mode, diagnosis),
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


def _blocked(reason: str, detail: str) -> dict:
    return {
        "task_id": "unknown", "input_privacy_mode": "unknown",
        "safety_status": "BLOCKED", "review_allowed": False,
        "target_section_name": "N/A", "diagnosis": "",
        "revision_priorities": [], "suggested_structure": "",
        "argument_continuity_notes": "", "citation_or_evidence_needs": [],
        "privacy_limitations": ["review blocked"],
        "blocked_reasons": [f"{reason}: {detail}"],
        "next_recommended_human_action": "Fix input errors and retry",
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


def _diagnose(data: dict) -> str:
    problems = data.get("known_problems","")
    outline = data.get("argument_outline","")
    steps = len([s for s in outline.split("\n") if s.strip()])
    if steps < 2: return "Section argument structure is too thin. Add at least 3 logical steps."
    if problems: return f"Section has known issues: {problems[:200]}. Prioritize addressing these before expansion."
    return "Section structure appears adequate. Focus on evidence support and transitions."


def _revision_priorities(data: dict) -> list[str]:
    priorities = []
    if data.get("known_problems"): priorities.append("Address known problems first")
    outline = data.get("argument_outline","")
    if len([s for s in outline.split("\n") if s.strip()]) < 3: priorities.append("Expand argument structure to 3+ steps")
    if not data.get("research_question"): priorities.append("Clarify research question")
    priorities.append("Add supporting citations for each claim")
    priorities.append("Review transitions between subsections")
    return priorities


def _suggest_structure(data: dict) -> str:
    section = data.get("target_section_name","Section")
    return f"{section}\n1. Opening context (2-3 paragraphs)\n2. Core argument (3-5 paragraphs)\n3. Evidence and examples\n4. Counter-arguments addressed\n5. Transition to next section"


def _argument_notes(data: dict) -> str:
    outline = data.get("argument_outline","")
    if not outline: return "No argument outline provided. Cannot assess continuity."
    return f"Argument has {len([s for s in outline.split(chr(10)) if s.strip()])} steps. Check logical flow between each step."


def _citation_needs(data: dict) -> list[str]:
    return [
        "Each factual claim needs a citation",
        "Methodology choices need justification references",
        "Contrasting viewpoints should be cited",
    ]


def _privacy_limits(mode: str) -> list[str]:
    limits = {
        "synthetic_only": ["No real paper content was reviewed","All data is synthetic","Review is bounded to structural diagnosis only"],
        "metadata_only": ["Only metadata was reviewed","No paper body text was processed","Content quality assessment is limited"],
        "sanitized_section": ["Section content was reviewed in sanitized form","Redacted content was NOT inspected","Review scope is limited to sanitized excerpt"],
    }
    return limits.get(mode, ["Privacy mode unknown"])


def _next_action(mode: str, diagnosis: str) -> str:
    if mode == "synthetic_only": return "Replace synthetic data with real section metadata (not full text) for actual review"
    if mode == "sanitized_section": return "Review diagnosis and revision priorities. Apply changes to the original section."
    return "Review output and decide next step"


def main():
    parser = argparse.ArgumentParser(description="Bounded section review runner")
    parser.add_argument("--input", required=True, help="Input YAML file")
    parser.add_argument("--json-output", help="JSON result output path")
    parser.add_argument("--report-output", help="Markdown report output path")
    args = parser.parse_args()

    result = review(args.input)

    # JSON output
    if args.json_output:
        Path(args.json_output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.json_output).write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")

    # Markdown report
    if args.report_output:
        Path(args.report_output).parent.mkdir(parents=True, exist_ok=True)
        md = _render_report(result)
        Path(args.report_output).write_text(md, encoding="utf-8")

    print(json.dumps(result, indent=2, ensure_ascii=False))
    sys.exit(0 if result["review_allowed"] else 1)


def _render_report(result: dict) -> str:
    return f"""# Section Review Report — {result['task_id']}

## Scope
- Target section: {result['target_section_name']}
- Privacy mode: {result['input_privacy_mode']}
- Safety status: {result['safety_status']}
- Review allowed: {result['review_allowed']}

## Diagnosis
{result['diagnosis']}

## Revision Priorities
""" + "\n".join(f"- {p}" for p in result.get('revision_priorities',[])) + f"""

## Suggested Structure
{result.get('suggested_structure','')}

## Argument Continuity
{result.get('argument_continuity_notes','')}

## Citation & Evidence Needs
""" + "\n".join(f"- {c}" for c in result.get('citation_or_evidence_needs',[])) + f"""

## Privacy Limitations
""" + "\n".join(f"- {l}" for l in result.get('privacy_limitations',[])) + f"""

## Next Action
{result.get('next_recommended_human_action','')}

> Generated: {result.get('generated_at','')}
> Bounded section review only. No full paper processed.
"""


if __name__ == "__main__":
    main()
