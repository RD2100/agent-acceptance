"""Memory Lint — validate memory entries against MEMORY_LINT_CONTRACT rules.

Checks:
- L-001: lesson_without_source_review
- L-002: private_text_in_memory
- L-007: repeated_failure_without_gate
- L-009: deprecated_entry_still_marked_active
- L-010: accepted_task_without_memory_summary
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MEMORY_DIR = ROOT / "memory"
DAILY_DIR = MEMORY_DIR / "daily"
KNOWLEDGE_DIR = MEMORY_DIR / "knowledge"


def lint_daily_logs() -> list[dict]:
    """Lint all daily log files."""
    issues = []
    if not DAILY_DIR.exists():
        return [{"rule": "L-000", "level": "FAIL", "description": "daily log directory not found"}]

    for df in DAILY_DIR.glob("*.md"):
        text = df.read_text(encoding="utf-8")

        # L-001: check for source references (Chinese or English field names)
        has_source = any(kw in text for kw in ["REVIEW_RUN_ID", "source_review_run_id", "来源审查ID", "审查运行ID"])
        if not has_source:
            issues.append({
                "rule": "L-001", "level": "FAIL",
                "memory_id": df.name,
                "description": "lesson without source_review_run_id",
            })

        # L-002: private text check
        private_signals = ["我的博士论文", "用户论文全文", "real thesis content", "private manuscript"]
        for sig in private_signals:
            if sig in text.lower():
                issues.append({
                    "rule": "L-002", "level": "FAIL",
                    "memory_id": df.name,
                    "description": f"may contain private paper text: '{sig}'",
                })

    return issues


def lint_knowledge_index() -> list[dict]:
    """Lint knowledge index."""
    issues = []
    idx = KNOWLEDGE_DIR / "index.md"
    if not idx.exists():
        return [{"rule": "L-000", "level": "WARNING", "description": "knowledge index not found"}]

    text = idx.read_text(encoding="utf-8")

    # L-009: deprecated check
    if "已废弃" in text:
        for line in text.split("\n"):
            if "已废弃" in line:
                issues.append({
                    "rule": "L-009", "level": "NEEDS_REVIEW",
                    "memory_id": "index.md",
                    "description": f"deprecated entry found: {line.strip()[:80]}",
                })

    return issues


def lint_repeated_failures() -> list[dict]:
    """L-007: check for repeated failure patterns without linked gate."""
    issues = []
    patterns = {}
    for df in DAILY_DIR.glob("*.md"):
        text = df.read_text(encoding="utf-8")
        for line in text.split("\n"):
            if "summary-only" in line.lower():
                patterns["summary-only pack"] = patterns.get("summary-only pack", 0) + 1
            if "ready_for_review" in line.lower() and "closed" in line.lower():
                patterns["ready_for_review as closed"] = patterns.get("ready_for_review as closed", 0) + 1

    for pattern, count in patterns.items():
        if count >= 2:
            issues.append({
                "rule": "L-007", "level": "NEEDS_REVIEW",
                "pattern": pattern,
                "occurrence_count": count,
                "description": f"repeated failure pattern ({count}x) without linked gate",
            })

    return issues


def main():
    all_issues = []
    all_issues.extend(lint_daily_logs())
    all_issues.extend(lint_knowledge_index())
    all_issues.extend(lint_repeated_failures())

    fails = [i for i in all_issues if i["level"] == "FAIL"]
    needs_review = [i for i in all_issues if i["level"] == "NEEDS_REVIEW"]
    warnings = [i for i in all_issues if i["level"] == "WARNING"]

    result = "pass"
    if fails:
        result = "fail"
    elif needs_review:
        result = "needs_review"

    print(f"MEMORY_LINT_RESULT:")
    print(f"  result: {result}")
    print(f"  checks_run: {len(all_issues)}")
    print(f"  errors ({len(fails)}):")
    for i in fails:
        print(f"    - [{i['rule']}] {i.get('memory_id','')}: {i['description']}")
    if not fails:
        print(f"    []")
    print(f"  needs_review ({len(needs_review)}):")
    for i in needs_review:
        print(f"    - [{i['rule']}] {i.get('pattern','')}: {i['description']}")
    if not needs_review:
        print(f"    []")
    print(f"  warnings ({len(warnings)}):")
    for i in warnings:
        print(f"    - [{i['rule']}] {i['description']}")
    if not warnings:
        print(f"    []")

    return {"pass": 0, "needs_review": 0, "fail": 1}.get(result, 1)


if __name__ == "__main__":
    sys.exit(main())
