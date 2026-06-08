#!/usr/bin/env python3
"""
paper_c7_collab_iterator.py — Claude+GPT collaborative paper revision loop.

For each module: Claude diagnoses → GPT reviews abstract → Claude generates strategy
→ GPT confirms → close or human_required.
GPT NEVER sees original text — only diagnosis summaries and revision strategies.
"""
import json, sys, subprocess, os
from pathlib import Path
from datetime import datetime, timezone

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))
from paper_c7_iteration_ledger import start_round, add_issue, close_round, module_status, load


def run_module_iteration(module: dict, round_num: int = 1) -> dict:
    """Run one iteration on a single module. Returns iteration result."""
    module_id = f"M{module['index']}"
    result = {"module_id": module_id, "round": round_num, "timestamp": datetime.now(timezone.utc).isoformat()}

    # Step 1: Claude diagnoses (C5 reader on module text)
    c5_path = str(REPO / "scripts" / "paper_c5_full_section_reader.py")
    tmp_text = REPO / "_reports" / f"_c7_tmp_m{module['index']}.txt"
    tmp_text.parent.mkdir(parents=True, exist_ok=True)
    module_text = module.get("full_text", f"# {module['section']}\n{module.get('subsection','')}")
    tmp_text.write_text(module_text, encoding="utf-8")

    r = subprocess.run([sys.executable, c5_path, str(tmp_text), module["section"]],
                       capture_output=True, text=True, timeout=30, cwd=str(REPO))
    try:
        c5_diag = json.loads(r.stdout)
    except:
        c5_diag = {"error": "C5 parse failed"}
    result["claude_diagnosis"] = _summarize_c5(c5_diag)

    # Step 2: Claude generates revision strategy (C6)
    c6_path = str(REPO / "scripts" / "paper_c6_revision_suggester.py")
    tmp_json = REPO / "_reports" / f"_c7_tmp_m{module['index']}.json"
    tmp_json.write_text(json.dumps(c5_diag, ensure_ascii=False), encoding="utf-8")

    r = subprocess.run([sys.executable, c6_path, str(tmp_json)],
                       capture_output=True, text=True, timeout=15, cwd=str(REPO))
    try:
        c6_strategy = json.loads(r.stdout)
    except:
        c6_strategy = {"error": "C6 parse failed"}
    result["revision_strategy"] = _summarize_c6(c6_strategy)

    # Cleanup
    tmp_text.unlink(missing_ok=True)
    tmp_json.unlink(missing_ok=True)

    return result


def _summarize_c5(c5: dict) -> dict:
    """Create GPT-safe summary of C5 diagnosis (no original text)."""
    return {
        "paragraph_count": c5.get("paragraph_count", 0),
        "function_distribution": c5.get("function_distribution", {}),
        "structure_issues": c5.get("structure_issues", [])[:5],
        "summary": c5.get("summary", ""),
    }


def _summarize_c6(c6: dict) -> dict:
    """Create GPT-safe summary of C6 strategy (strategies and templates only)."""
    return {
        "suggestion_count": c6.get("suggestion_count", 0),
        "strategies": [
            {"type": s.get("type"), "strategy": s.get("strategy", "")[:200], "target": s.get("target", "")}
            for s in c6.get("suggestions", [])
        ],
    }


def generate_gpt_prompt(module: dict, iter_result: dict, round_num: int) -> str:
    """Generate the GPT review prompt for this module iteration."""
    lines = [
        f"## Module M{module['index']}: {module['section'][:50]}",
        f"Subsection: {module.get('subsection', 'N/A')[:50]}",
        f"Chars: {module['char_count']}, Citations: {module['citation_count']}",
        f"Function: {', '.join(module.get('functions', []))}",
        f"Round: {round_num}/{3}",
        "",
        "## Claude Diagnosis (C5)",
        f"Paragraphs: {iter_result['claude_diagnosis']['paragraph_count']}",
        f"Functions: {json.dumps(iter_result['claude_diagnosis']['function_distribution'], ensure_ascii=False)}",
        f"Issues: {json.dumps(iter_result['claude_diagnosis']['structure_issues'], ensure_ascii=False)}",
        "",
        "## Revision Strategy (C6)",
        f"Suggestions: {iter_result['revision_strategy']['suggestion_count']}",
    ]
    for s in iter_result['revision_strategy']['strategies']:
        lines.append(f"- [{s['type']}] {s['strategy'][:150]}")
    lines.append("")
    lines.append("Review: Any P0/P1 issues missed? Additional strategies needed? Or accept and close?")
    lines.append("Return: severity_issues: [], verdict: pass|blocked|pass_with_limitation")
    lines.append("END_OF_GPT_RESPONSE")
    return '\n'.join(lines)


def main():
    if len(sys.argv) < 2:
        print("Usage: paper_c7_collab_iterator.py <module_manifest.json>")
        sys.exit(1)

    manifest = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    modules = manifest.get("modules", [])
    print(f"Paper: {manifest['paper_title'][:80]}")
    print(f"Modules: {len(modules)}")

    for mod in modules[:3]:  # Limit to 3 for demo
        mid = f"M{mod['index']}"
        status = module_status(mid)
        print(f"\n{'='*50}")
        print(f"M{mod['index']}: {mod['section'][:40]} ({mod['char_count']}字) — Status: {status['status']}")

        if status['status'] in ("accepted", "accepted_with_limitation", "blocked"):
            print(f"  Skip: already {status['status']}")
            continue

        # Start round
        r = start_round(mid, 1)
        if not r["allowed"]:
            print(f"  Blocked: {r['reason']}")
            continue

        # Run iteration
        result = run_module_iteration(mod, 1)
        gpt_prompt = generate_gpt_prompt(mod, result, 1)

        # Output GPT prompt for CDP submission
        prompt_path = REPO / "_reports" / f"_c7_gpt_prompt_m{mod['index']}_r1.txt"
        prompt_path.parent.mkdir(parents=True, exist_ok=True)
        prompt_path.write_text(gpt_prompt, encoding="utf-8")
        print(f"  Diagnosis: {len(result['claude_diagnosis']['structure_issues'])} issues")
        print(f"  Strategies: {result['revision_strategy']['suggestion_count']}")
        print(f"  GPT prompt saved: {prompt_path}")

    print(f"\nAll GPT prompts saved to _reports/_c7_gpt_prompt_m*_r1.txt")
    print("Use CDP to submit each prompt to GPT for review.")


if __name__ == "__main__":
    main()
