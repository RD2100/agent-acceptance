#!/usr/bin/env python3
"""
paper_c4_revision_blueprint.py — Generate structured revision blueprint from section review.
Takes SECTION_REVIEW_RESULT.json and produces actionable REVISION_BLUEPRINT.md.
"""
import argparse, json, sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

def generate(result_json: str) -> dict:
    """Generate revision blueprint from section review result."""
    if not Path(result_json).exists():
        return {"error": f"file not found: {result_json}"}
    review = json.loads(Path(result_json).read_text(encoding="utf-8"))

    if not review.get("review_allowed"):
        return {"error": "review not allowed", "blocked_reasons": review.get("blocked_reasons",[])}

    priorities = review.get("revision_priorities", [])
    diagnosis = review.get("diagnosis", "")
    structure = review.get("suggested_structure", "")

    blueprint = {
        "task_id": review["task_id"],
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "based_on_review": True,
        "revision_phases": [],
        "estimated_effort": "2-4 hours per phase",
        "success_criteria": [],
    }

    # Phase 1: Address known problems
    if diagnosis:
        blueprint["revision_phases"].append({
            "phase": 1,
            "name": "Address Diagnosed Issues",
            "actions": [diagnosis],
            "duration": "1-2 hours",
        })

    # Phase 2: Apply revision priorities
    for i, p in enumerate(priorities[:5], 1):
        blueprint["revision_phases"].append({
            "phase": i + 1,
            "name": f"Priority {i}: {p[:60]}",
            "actions": [f"Implement: {p}"],
            "duration": "30-60 min",
        })

    # Phase 3: Restructure per suggested structure
    if structure:
        blueprint["revision_phases"].append({
            "phase": len(blueprint["revision_phases"]) + 1,
            "name": "Apply Suggested Structure",
            "actions": [f"Restructure section per: {structure[:100]}"],
            "duration": "1-2 hours",
        })

    # Success criteria
    blueprint["success_criteria"] = [
        "All diagnosed issues addressed",
        "Revision priorities applied",
        "Section follows suggested structure",
        "Citations added for factual claims",
        "Transition sentences between subsections",
    ]

    return blueprint

def render_md(blueprint: dict) -> str:
    lines = [
        f"# Revision Blueprint — {blueprint.get('task_id','')}",
        f"Generated: {blueprint.get('generated_at','')}",
        "",
        "## Revision Phases", ""
    ]
    for phase in blueprint.get("revision_phases", []):
        lines.append(f"### Phase {phase['phase']}: {phase['name']}")
        lines.append(f"Duration: {phase['duration']}")
        for a in phase["actions"]:
            lines.append(f"- {a}")
        lines.append("")
    lines.append("## Success Criteria")
    for c in blueprint.get("success_criteria", []):
        lines.append(f"- {c}")
    lines.append("")
    lines.append("> Bounded section revision only. No full paper ingestion.")
    return "\n".join(lines)

def main():
    parser = argparse.ArgumentParser(description="Revision blueprint generator")
    parser.add_argument("--review-json", required=True, help="SECTION_REVIEW_RESULT.json")
    parser.add_argument("--output-md", help="Output Markdown blueprint")
    args = parser.parse_args()

    bp = generate(args.review_json)
    if args.output_md:
        Path(args.output_md).parent.mkdir(parents=True, exist_ok=True)
        Path(args.output_md).write_text(render_md(bp), encoding="utf-8")

    print(json.dumps(bp, indent=2, ensure_ascii=False))
    sys.exit(0 if "error" not in bp else 1)

if __name__ == "__main__":
    main()
