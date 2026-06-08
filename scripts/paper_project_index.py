#!/usr/bin/env python3
"""
paper_project_index.py — Generate paper project awareness index.
Unifies C4/C5/C6/C7 outputs into a single GPT-friendly structure abstract.
GPT sees full paper structure, never raw text.
"""
import json, sys
from pathlib import Path
from datetime import datetime, timezone

REPO = Path(__file__).resolve().parent.parent

def build_index(manifest_path: str, c7_outputs: dict = None) -> dict:
    """Build project index from module manifest + C5/C6/C7 results."""
    manifest = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
    modules = manifest.get("modules", [])

    # Load ledger statuses
    ledger_dir = REPO / ".ai" / "module_ledger"
    ledgers = {}
    if ledger_dir.is_dir():
        for f in ledger_dir.glob("M*.json"):
            ledgers[f.stem] = json.loads(f.read_text(encoding="utf-8"))

    # Build GPT-friendly index
    index = {
        "paper_title": manifest["paper_title"],
        "total_modules": manifest["total_modules"],
        "total_chars": manifest["total_chars"],
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "overall_status": _overall_status(ledgers),
        "modules": [],
        "structure_map": {},
        "issues_summary": {"P0": 0, "P1": 0, "P2": 0, "P3": 0},
    }

    for mod in modules:
        mid = f"M{mod['index']}"
        ledger = ledgers.get(mid, {})
        entry = {
            "id": mid,
            "section": mod["section"][:60],
            "subsection": mod["subsection"][:60],
            "chars": mod["char_count"],
            "citations": mod["citation_count"],
            "functions": mod["functions"],
            "review_status": ledger.get("status", "new"),
            "rounds": len(ledger.get("rounds", [])),
        }

        # Count issues from ledger
        p_count = {"P0": 0, "P1": 0, "P2": 0, "P3": 0}
        for rd in ledger.get("rounds", []):
            for issue in rd.get("issues", []):
                sev = issue.get("severity", "P3")
                p_count[sev] = p_count.get(sev, 0) + 1
        entry["issue_counts"] = p_count
        for sev in ["P0", "P1", "P2", "P3"]:
            index["issues_summary"][sev] += p_count.get(sev, 0)

        index["modules"].append(entry)

        # Structure map (section -> modules)
        sec = mod["section"][:30]
        index["structure_map"].setdefault(sec, []).append(mid)

    return index


def _overall_status(ledgers: dict) -> str:
    statuses = [l.get("status", "new") for l in ledgers.values()]
    if "blocked" in statuses:
        return "blocked"
    if all(s in ("accepted", "accepted_with_limitation") for s in statuses):
        return "all_accepted"
    if any(s == "in_progress" for s in statuses):
        return "in_progress"
    return "pending"


def render_gpt_view(index: dict) -> str:
    """Render index as GPT-friendly abstract (no raw text)."""
    lines = [f"# Paper Project Index: {index['paper_title'][:60]}",
             f"Total: {index['total_modules']} modules, {index['total_chars']} chars",
             f"Status: {index['overall_status']}",
             f"Issues: P0={index['issues_summary']['P0']} P1={index['issues_summary']['P1']} P2={index['issues_summary']['P2']}",
             "", "## Structure", ""]
    for sec, mods in index["structure_map"].items():
        lines.append(f"### {sec}")
        for mid in mods:
            m = next((m for m in index["modules"] if m["id"] == mid), None)
            if m:
                funcs = ",".join(m["functions"])
                issues = m["issue_counts"]
                lines.append(f"- {mid}: {m['subsection'][:40]} ({m['chars']}字, {m['citations']} refs) [{funcs}] status={m['review_status']} P1={issues['P1']}")
    lines.append("")
    lines.append("> Note: GPT sees this abstract only. Full text never leaves local machine.")
    return "\n".join(lines)


def main():
    if len(sys.argv) < 2:
        print("Usage: paper_project_index.py <module_manifest.json>")
        sys.exit(1)

    index = build_index(sys.argv[1])
    out = REPO / "_reports" / "PAPER_PROJECT_INDEX.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(index, indent=2, ensure_ascii=False), encoding="utf-8")

    gpt_view = render_gpt_view(index)
    view_out = REPO / "_reports" / "PAPER_PROJECT_INDEX_GPT_VIEW.md"
    view_out.write_text(gpt_view, encoding="utf-8")

    print(f"Index: {index['total_modules']} modules, {index['issues_summary']['P1']} P1 issues")
    print(f"GPT view: {view_out}")
    sys.exit(0)


if __name__ == "__main__":
    main()
