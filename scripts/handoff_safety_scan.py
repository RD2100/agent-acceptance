#!/usr/bin/env python3
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from validate_context_memory import validate_file


def scan_files(paths):
    results = []
    issues = []
    for path in paths:
        fp = Path(path)
        result = validate_file(fp)
        results.append(result)
        for issue in result.get("issues", []):
            issues.append(issue)

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "pass": len(issues) == 0,
        "files_checked": len(results),
        "issues": issues,
        "results": results,
        "scanner": "validate_context_memory.validate_file",
    }


def write_markdown(result, output_path):
    lines = [
        "# Handoff Safety Scan",
        "",
        f"- generated_at: {result['generated_at']}",
        f"- scanner: {result['scanner']}",
        f"- files_checked: {result['files_checked']}",
        f"- pass: {result['pass']}",
        "",
        "## Issues",
    ]
    if result["issues"]:
        for issue in result["issues"]:
            lines.append(f"- {issue.get('file')}:{issue.get('line')} pattern={issue.get('pattern')} matches={issue.get('matches')}")
    else:
        lines.append("- none")
    Path(output_path).write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/handoff_safety_scan.py <file> [<file> ...] [--md-output path]", file=sys.stderr)
        return 2
    args = sys.argv[1:]
    md_output = None
    if "--md-output" in args:
        idx = args.index("--md-output")
        md_output = args[idx + 1]
        del args[idx:idx + 2]
    result = scan_files([Path(a) for a in args])
    if md_output:
        write_markdown(result, md_output)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
