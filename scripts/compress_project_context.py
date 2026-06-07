#!/usr/bin/env python3
"""
compress_project_context.py — Compress PROJECT_HISTORY, audit ledger, and GPT review
results into compact memory entries.

Pipeline: segment → classify → deduplicate → supersede → privacy_filter → emit.

Deterministic/rule-based. No external API calls. No paper content ingestion.
"""
import hashlib
import json
import re
import sys
import yaml
from datetime import datetime, timezone
from pathlib import Path

# ── Privacy filter (fail-closed) ───────────────────────────────────
FORBIDDEN_PATTERNS = [
    re.compile(r"real_paper_full_text", re.I),
    re.compile(r"raw_paper_text", re.I),
    re.compile(r"private_user_text", re.I),
    re.compile(r"raw_transcript", re.I),
    re.compile(r"cookie", re.I),
    re.compile(r"\bapi[_-]?key\b", re.I),
    re.compile(r"\bsecret\b", re.I),
    re.compile(r"\btoken\b", re.I),
    re.compile(r"博士论文正文"),
    re.compile(r"用户论文全文"),
    re.compile(r"外部上传"),
]


def privacy_ok(text: str) -> bool:
    """Fail-closed: return False if any forbidden pattern matches."""
    for pat in FORBIDDEN_PATTERNS:
        if pat.search(text):
            return False
    return True


# ── Stage 1: Segment ────────────────────────────────────────────────
def segment_project_history(path: str, max_depth: int = 1500) -> list[dict]:
    """Split PROJECT_HISTORY.md into segments by task binding sections."""
    text = Path(path).read_text(encoding="utf-8")
    segments = []

    # Find GROUP-## or PAPER-XX or TASK-XX binding sections
    section_pattern = re.compile(
        r"(##\s+(GROUP-\d+|PAPER-[A-Z0-9-]+|WorkQueue|CONTEXT-COMPRESSION-[A-Z0-9-]+)\s+Acceptance\s+Binding.*?)(?=##\s+(GROUP-|PAPER-|WorkQueue|CONTEXT-)|$)",
        re.DOTALL,
    )
    for match in section_pattern.finditer(text):
        full_section = match.group(0)
        task_id_match = re.search(r"(GROUP-\d+|PAPER-[A-Z0-9-]+|WorkQueue|CONTEXT-COMPRESSION-[A-Z0-9-]+)", match.group(2) or "")
        task_id = task_id_match.group(0) if task_id_match else "unknown"

        segments.append({
            "task_id": task_id,
            "source": path,
            "raw_text": full_section.strip()[:max_depth],
            "char_count": len(full_section),
        })

    # Also extract the task table (lines 30-60 approx)
    table_area = "\n".join(text.split("\n")[29:60])
    segments.append({
        "task_id": "TASK-TABLE",
        "source": path,
        "raw_text": table_area[:max_depth],
        "char_count": len(table_area),
    })

    return segments


def segment_audit_ledger(path: str) -> list[dict]:
    """Extract task entries from WORKFLOW_AUDIT_LEDGER.yaml."""
    try:
        data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    except Exception:
        return []

    segments = []
    tasks = data.get("tasks", []) if isinstance(data, dict) else []
    for entry in tasks:
        if isinstance(entry, dict) and "task_id" in entry:
            segments.append({
                "task_id": entry["task_id"],
                "source": path,
                "raw_text": json.dumps(entry, ensure_ascii=False, default=str),
                "char_count": len(json.dumps(entry, ensure_ascii=False, default=str)),
            })
    return segments


# ── Stage 2: Classify ────────────────────────────────────────────────
def classify(segment: dict) -> dict:
    """Tag segment: decision / blocker / fix / lesson / noise / superseded."""
    text = segment.get("raw_text", "")
    tags = []

    if re.search(r"overall_judgment.*accepted", text, re.I):
        tags.append("decision")
    if re.search(r"blocked|blocker|blocking", text, re.I):
        tags.append("blocker")
    if re.search(r"fix|fixed|修复|resolved", text, re.I):
        tags.append("fix")
    if re.search(r"lesson|教训|learned|SD-0", text, re.I):
        tags.append("lesson")
    if re.search(r"superseded", text, re.I):
        tags.append("superseded")
    if re.search(r"whole_dirty_tree|scope_note|excluded", text, re.I):
        tags.append("scope_note")

    if not tags:
        tags.append("noise")

    segment["tags"] = tags
    return segment


# ── Stage 3: Deduplicate ─────────────────────────────────────────────
def deduplicate(segments: list[dict]) -> list[dict]:
    """Merge segments with same task_id into one lifecycle entry."""
    by_task: dict[str, list[dict]] = {}
    for seg in segments:
        tid = seg.get("task_id", "unknown")
        by_task.setdefault(tid, []).append(seg)

    merged = []
    for tid, segs in by_task.items():
        all_tags = sorted(set(t for s in segs for t in s.get("tags", [])))
        best_text = max(segs, key=lambda s: len(s.get("raw_text", "")))

        merged.append({
            "task_id": tid,
            "source_count": len(segs),
            "sources": list(set(s["source"] for s in segs)),
            "tags": all_tags,
            "raw_text": best_text["raw_text"],
            "char_count": best_text["char_count"],
        })
    return merged


# ── Stage 4: Supersede ───────────────────────────────────────────────
def supersede(entries: list[dict]) -> list[dict]:
    """When blocked was superseded by accepted, keep only final accepted state + root cause."""
    result = []
    for entry in entries:
        tags = entry.get("tags", [])
        if "superseded" in tags:
            # Extract root cause + final fix, drop intermediate noise
            text = entry["raw_text"]
            root_cause = ""
            final_fix = ""
            rc_match = re.search(r"(blocking_issues|blocked).*?(?=required_fixes|accept)", text, re.DOTALL | re.I)
            if rc_match:
                root_cause = rc_match.group(0)[:200]
            fx_match = re.search(r"(required_fixes|fix|修复).*", text, re.DOTALL | re.I)
            if fx_match:
                final_fix = fx_match.group(0)[:200]
            entry["raw_text"] = f"ROOT_CAUSE: {root_cause}\nFINAL_FIX: {final_fix}"
            entry["char_count"] = len(entry["raw_text"])
        result.append(entry)
    return result


# ── Stage 5: Privacy filter ──────────────────────────────────────────
def privacy_filter(entries: list[dict]) -> list[dict]:
    """Remove entries containing forbidden content. Fail-closed."""
    safe = []
    for entry in entries:
        if privacy_ok(entry.get("raw_text", "")):
            entry["privacy_checked"] = True
            safe.append(entry)
        else:
            print(f"PRIVACY BLOCK: task_id={entry.get('task_id')} — forbidden content detected, excluded")
    return safe


# ── Stage 6: Emit ────────────────────────────────────────────────────
def emit_task_memory(entry: dict, output_dir: str) -> str:
    """Write a task lifecycle memory file."""
    tid = entry.get("task_id", "unknown").replace("/", "-")
    status = "accepted" if "decision" in entry.get("tags", []) else "unknown"

    content = f"""# {tid}

> task_id: {tid}
> status: {status}
> review_run_id: {entry.get('review_run_id', 'see evidence pack')}
> compressed_at: {datetime.now(timezone.utc).isoformat()}

## Key Information

{entry.get('raw_text', '')[:600]}

## Tags

{', '.join(entry.get('tags', []))}

## Sources

""" + "\n".join(f"- {s}" for s in entry.get("sources", []))

    filepath = Path(output_dir) / f"{tid}.md"
    filepath.parent.mkdir(parents=True, exist_ok=True)
    filepath.write_text(content, encoding="utf-8")
    return str(filepath)


def emit_knowledge(topic: str, content: str, output_dir: str) -> str:
    """Write a knowledge file."""
    slug = topic.lower().replace(" ", "_").replace("/", "-")
    filepath = Path(output_dir) / f"{slug}.md"
    filepath.parent.mkdir(parents=True, exist_ok=True)
    filepath.write_text(content, encoding="utf-8")
    return str(filepath)


def emit_index(entries: list[dict], knowledge_files: list[str], output_path: str) -> str:
    """Write memory/index.md."""
    now = datetime.now(timezone.utc).isoformat()
    lines = [
        "# Memory Index",
        "",
        f"> Last updated: {now}",
        f"> Entry count: {len(entries) + len(knowledge_files)}",
        "> Generated by: compress_project_context.py",
        "",
        "## Task Lifecycle Memories",
        "",
        "| Task ID | Status | Tags |",
        "|---------|--------|------|",
    ]
    for entry in entries:
        tid = entry.get("task_id", "unknown")
        status = "accepted" if "decision" in entry.get("tags", []) else "unknown"
        tags = ", ".join(entry.get("tags", [])[:3])
        lines.append(f"| {tid} | {status} | {tags} |")

    lines.extend([
        "",
        "## Knowledge Files",
        "",
    ])
    for kf in knowledge_files:
        lines.append(f"- {kf}")

    content = "\n".join(lines)
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    Path(output_path).write_text(content, encoding="utf-8")
    return output_path


# ── Main Pipeline ────────────────────────────────────────────────────
def run_pipeline(
    project_history: str = "PROJECT_HISTORY.md",
    audit_ledger: str = "docs/WORKFLOW_AUDIT_LEDGER.yaml",
    task_memory_dir: str = "memory/tasks",
    knowledge_dir: str = "memory/knowledge",
    index_path: str = "memory/index.md",
) -> dict:
    """Execute the full compression pipeline."""

    # Segment
    segments = segment_project_history(project_history)
    segments += segment_audit_ledger(audit_ledger)
    print(f"SEGMENT: {len(segments)} segments")

    # Classify
    segments = [classify(s) for s in segments]
    tag_counts = {}
    for s in segments:
        for t in s.get("tags", []):
            tag_counts[t] = tag_counts.get(t, 0) + 1
    print(f"CLASSIFY: tags={tag_counts}")

    # Deduplicate
    merged = deduplicate(segments)
    print(f"DEDUP: {len(segments)} → {len(merged)} merged")

    # Supersede
    superseded = supersede(merged)

    # Privacy filter
    safe = privacy_filter(superseded)
    print(f"PRIVACY: {len(superseded)} → {len(safe)} safe")

    # Emit task memories
    task_files = []
    for entry in safe:
        fp = emit_task_memory(entry, task_memory_dir)
        task_files.append(fp)
    print(f"EMIT TASKS: {len(task_files)} files")

    # Knowledge files (pre-built)
    knowledge_files = [
        "memory/knowledge/evidence_first.md",
        "memory/knowledge/dirty_worktree_split.md",
        "memory/knowledge/gpt_review_gate.md",
        "memory/knowledge/paper_privacy.md",
        "memory/knowledge/workqueue.md",
        "memory/knowledge/context_compression.md",
    ]

    # Emit index
    emit_index(safe, knowledge_files, index_path)

    return {
        "pipeline": "COMPLETE",
        "segments_in": len(segments),
        "merged": len(merged),
        "privacy_safe": len(safe),
        "task_memories": len(task_files),
        "knowledge_files": len(knowledge_files),
        "index_path": index_path,
    }


def main():
    result = run_pipeline()
    print(json.dumps(result, indent=2, ensure_ascii=False))
    sys.exit(0 if result["privacy_safe"] > 0 else 1)


if __name__ == "__main__":
    main()
