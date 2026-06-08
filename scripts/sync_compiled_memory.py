#!/usr/bin/env python3
"""
sync_compiled_memory.py — Bridge between claude-memory-compiler output and agent-acceptance memory/.
Syncs structural summaries only, never raw transcripts or private content.
"""
import json, sys, re
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
COMPILER_DIR = REPO / ".claude" / "skills" / "claude-memory-compiler"
MEMORY_DIR = REPO / "memory"

# Forbidden patterns — never sync these
FORBIDDEN = [r"raw_paper_text", r"private_user_text", r"raw_transcript",
             r"api_key", r"secret", r"博士论文正文", r"用户论文全文"]


def sync() -> dict:
    result = {"synced_files": [], "skipped": [], "timestamp": datetime.now(timezone.utc).isoformat()}

    # Sync daily logs → memory/daily/
    daily_src = COMPILER_DIR / "daily"
    if daily_src.is_dir():
        dest = MEMORY_DIR / "daily"
        dest.mkdir(parents=True, exist_ok=True)
        for f in daily_src.glob("*.md"):
            content = f.read_text(encoding="utf-8", errors="replace")
            if _is_safe(content):
                (dest / f.name).write_text(_sanitize(content), encoding="utf-8")
                result["synced_files"].append(f"daily/{f.name}")
            else:
                result["skipped"].append(f"daily/{f.name} (forbidden content)")

    # Sync knowledge articles → memory/knowledge/
    know_src = COMPILER_DIR / "knowledge"
    if know_src.is_dir():
        dest = MEMORY_DIR / "knowledge"
        dest.mkdir(parents=True, exist_ok=True)
        for f in know_src.glob("*.md"):
            if f.name == "index.md":
                continue  # Don't overwrite existing index
            content = f.read_text(encoding="utf-8", errors="replace")
            if _is_safe(content):
                (dest / f.name).write_text(_sanitize(content), encoding="utf-8")
                result["synced_files"].append(f"knowledge/{f.name}")

    # Update memory/index.md with compiler entries
    idx_path = COMPILER_DIR / "index.md"
    if idx_path.exists():
        _append_to_memory_index(idx_path)

    result["synced_count"] = len(result["synced_files"])
    return result


def _is_safe(content: str) -> bool:
    for pattern in FORBIDDEN:
        if re.search(pattern, content, re.IGNORECASE):
            return False
    return True


def _sanitize(content: str) -> str:
    """Strip raw markers."""
    for pattern in FORBIDDEN:
        content = re.sub(pattern, "[REDACTED]", content, flags=re.IGNORECASE)
    return content


def _append_to_memory_index(compiler_index: Path):
    """Append compiler entries to memory/index.md without overwriting."""
    mi = MEMORY_DIR / "index.md"
    existing = mi.read_text(encoding="utf-8") if mi.exists() else "# Memory Index\n"
    ci = compiler_index.read_text(encoding="utf-8", errors="replace")

    marker = "## Compiler Sync"
    if marker in existing:
        existing = existing[:existing.index(marker)]

    new_entries = f"\n{marker}\n> Last compiler sync: {datetime.now(timezone.utc).isoformat()}\n\n{ci[:2000]}"
    mi.write_text(existing + new_entries, encoding="utf-8")


def main():
    result = sync()
    print(json.dumps(result, indent=2, ensure_ascii=False))
    sys.exit(0)


if __name__ == "__main__":
    main()
