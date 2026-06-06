"""Append a task row to the task registry table in PROJECT_HISTORY.md.

Usage:
    python scripts/append_to_project_history.py \
        --task-id PAPER-A2 \
        --verdict closed \
        --review-run-id paper-a2-io-redaction-protocol-v1 \
        --evidence-pack-path runs/paper-a2-closure/evidence-pack.zip
"""

import argparse
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROJECT_HISTORY_PATH = ROOT / "PROJECT_HISTORY.md"
END_MARKER = "END_OF_PROJECT_HISTORY"


def append_task(task_id: str, verdict: str, review_run_id: str, evidence_pack_path: str) -> bool:
    """Append a row to the task registry table and update the last-updated timestamp."""
    ph = PROJECT_HISTORY_PATH
    if not ph.exists():
        print(f"FAIL: {ph} not found")
        return False

    text = ph.read_text(encoding="utf-8")

    # Remove END_OF_PROJECT_HISTORY marker before appending
    if text.rstrip().endswith(END_MARKER):
        text = text.rstrip()[: -len(END_MARKER)].rstrip()
    else:
        print("WARN: END_OF_PROJECT_HISTORY marker not at end of file; appending anyway")

    # Find the task registry table (the one with 任务ID header)
    table_pattern = r"(\| 任务ID \|.*\| GPT审查 \|.*\| REVIEW_RUN_ID.*\n\|[-| ]+\n)"
    match = re.search(table_pattern, text)
    if not match:
        # Try looser match
        table_pattern = r"(\| 任务ID \|.*\n\|[-| ]+\n)"
        match = re.search(table_pattern, text)
        if not match:
            print("FAIL: task registry table not found in PROJECT_HISTORY.md")
            return False

    # Find where the table rows end (next blank line or next section header)
    table_start = match.end()
    # The table rows are after the header/separator. Find the end of the table.
    # Table ends at the next blank line or next ## section.
    lines = text[table_start:].split("\n")
    table_end_line = 0
    for i, line in enumerate(lines):
        if line.strip() == "" or line.startswith("## "):
            table_end_line = i
            break
    else:
        table_end_line = len(lines)

    # Build the new row
    now_ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    new_row = f"| {task_id} | agent-acceptance | — | {verdict} | {verdict} | {review_run_id} |"

    # Insert the new row after the existing rows (before the blank line)
    lines.insert(table_end_line, new_row)

    # Reconstruct: before-table + header + rows + rest
    after_table = "\n".join(lines[table_end_line + 1:])
    new_rows_text = "\n".join(lines[: table_end_line + 1])

    new_text = text[:table_start] + new_rows_text + "\n" + after_table

    # Update the "最后更新" timestamp
    new_text = re.sub(
        r"最后更新: .*",
        f"最后更新: {now_ts}",
        new_text
    )

    # Re-add the END_MARKER
    new_text = new_text.rstrip() + "\n" + END_MARKER + "\n"

    ph.write_text(new_text, encoding="utf-8")
    print(f"PASS: appended task {task_id} ({verdict}) to {ph}")
    print(f"  review_run_id: {review_run_id}")
    print(f"  evidence_pack: {evidence_pack_path}")
    return True


def main():
    parser = argparse.ArgumentParser(
        description="Append a task row to PROJECT_HISTORY.md task registry"
    )
    parser.add_argument("--task-id", required=True, help="Task identifier (e.g. PAPER-A2)")
    parser.add_argument("--verdict", required=True, help="Task verdict (e.g. closed, open, superseded)")
    parser.add_argument("--review-run-id", required=True, help="Review run identifier")
    parser.add_argument("--evidence-pack-path", required=True, help="Path to the evidence pack ZIP")
    args = parser.parse_args()

    ok = append_task(
        task_id=args.task_id,
        verdict=args.verdict,
        review_run_id=args.review_run_id,
        evidence_pack_path=args.evidence_pack_path,
    )
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
