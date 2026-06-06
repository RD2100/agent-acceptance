"""Update the conversation registry table in PROJECT_HISTORY.md.

Usage:
    python scripts/update_conversation_registry.py --conversation-id 6a23dd8c --status active --messages 25

    python scripts/update_conversation_registry.py --conversation-id 6a23dd8c --status closed
"""

import argparse
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROJECT_HISTORY_PATH = ROOT / "PROJECT_HISTORY.md"
END_MARKER = "END_OF_PROJECT_HISTORY"


def update_registry(conversation_id: str, status: str = "active",
                    messages: int = 0, purpose: str = "") -> bool:
    """Insert or update a conversation row in the registry table."""
    ph = PROJECT_HISTORY_PATH
    if not ph.exists():
        print(f"FAIL: {ph} not found")
        return False

    text = ph.read_text(encoding="utf-8")

    # Remove END_OF_PROJECT_HISTORY
    if text.rstrip().endswith(END_MARKER):
        text = text.rstrip()[: -len(END_MARKER)].rstrip()

    # Find the conversation registry table
    registry_header = "## 对话注册表"
    if registry_header not in text:
        print(f"FAIL: '{registry_header}' not found in PROJECT_HISTORY.md")
        return False

    # Find table start (after header + blank line + header row + separator)
    header_idx = text.index(registry_header)
    after_header = text[header_idx + len(registry_header):]

    # Find the table header row
    table_header_match = re.search(r"\| 对话 ID \| 用途 \| 消息数 \| 状态 \|", after_header)
    if not table_header_match:
        print("FAIL: conversation registry table header not found")
        return False

    table_start_in_after = table_header_match.end()
    # Skip the separator line
    rest = after_header[table_start_in_after:]
    sep_match = re.match(r"\s*\n\|[-| ]+\|\s*\n", rest)
    if sep_match:
        table_body_start = table_start_in_after + sep_match.end()
    else:
        table_body_start = table_start_in_after + 1

    table_body = after_header[table_body_start:]
    # Find end of table (blank line or ## header)
    lines = table_body.split("\n")
    table_end_line = 0
    for i, line in enumerate(lines):
        if line.strip() == "" or line.startswith("## "):
            table_end_line = i
            break
    else:
        table_end_line = len(lines)

    # Look for existing row with this conversation_id
    existing_idx = None
    for i in range(table_end_line):
        if f"| {conversation_id} |" in lines[i]:
            existing_idx = i
            break

    new_row = f"| {conversation_id} | {purpose or '当前活跃' if status == 'active' else status} | ~{messages or '—'} | {status} |"

    if existing_idx is not None:
        lines[existing_idx] = new_row
        print(f"  Updated existing row for conversation {conversation_id}")
    else:
        # Append at end of table (before blank line or next section)
        lines.insert(table_end_line, new_row)
        print(f"  Inserted new row for conversation {conversation_id}")

    # Reconstruct
    new_table_body = "\n".join(lines[:table_end_line + (0 if existing_idx is not None else 1)])
    rest_of_file = "\n".join(lines[table_end_line + (0 if existing_idx is not None else 1):])

    before_table = text[:header_idx + len(registry_header)] + after_header[:table_body_start]
    new_text = before_table + new_table_body + "\n" + rest_of_file

    # Update timestamp
    now_ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    new_text = re.sub(
        r"最后更新: .*",
        f"最后更新: {now_ts}",
        new_text
    )

    # Re-add END_MARKER
    new_text = new_text.rstrip() + "\n" + END_MARKER + "\n"

    ph.write_text(new_text, encoding="utf-8")
    print(f"PASS: updated conversation registry in {ph}")
    return True


def main():
    parser = argparse.ArgumentParser(
        description="Update the conversation registry in PROJECT_HISTORY.md"
    )
    parser.add_argument("--conversation-id", required=True,
                        help="Conversation identifier (e.g. 6a23dd8c)")
    parser.add_argument("--status", required=True,
                        choices=["active", "closed", "handed-off", "blocked"],
                        help="Conversation status")
    parser.add_argument("--messages", type=int, default=0,
                        help="Estimated message count")
    parser.add_argument("--purpose", default="",
                        help="Purpose description (defaults to auto-generated)")
    args = parser.parse_args()

    ok = update_registry(
        conversation_id=args.conversation_id,
        status=args.status,
        messages=args.messages,
        purpose=args.purpose,
    )
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
