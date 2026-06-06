"""Validate GPT reply completeness before execution.

Checks: min size, required end marker, required YAML fields for review/plan/handoff.
On fail: returns exit code 1 with GPT_REPLY_COMPLETENESS_RESULT.yaml.
"""
import sys
import re
from pathlib import Path

DEFAULTS = {
    "review_min_bytes": 2000,
    "task_plan_min_bytes": 3000,
    "handoff_min_bytes": 8000,
    "require_end_marker": True,
    "end_marker": "END_OF_GPT_RESPONSE",
    "handoff_end_marker": "END_OF_HANDOFF",
}

REQUIRED_REVIEW_FIELDS = [
    "overall_judgment", "blocking_reasons", "required_next_action", "allow_proceed",
]


def check_completeness(path: str, expected_type: str = "review") -> dict:
    """Check if GPT reply at path is complete enough to act on."""
    result = {
        "file": path,
        "expected_type": expected_type,
        "complete": False,
        "file_size": 0,
        "issues": [],
    }

    fp = Path(path)
    if not fp.exists():
        result["issues"].append("GPT_REPLY.txt not found")
        return result

    content = fp.read_text(encoding="utf-8")
    result["file_size"] = len(content)

    # Check minimum size
    min_bytes = {
        "review": DEFAULTS["review_min_bytes"],
        "task_plan": DEFAULTS["task_plan_min_bytes"],
        "handoff": DEFAULTS["handoff_min_bytes"],
    }.get(expected_type, DEFAULTS["review_min_bytes"])

    if result["file_size"] < min_bytes:
        result["issues"].append(f"too short: {result['file_size']} < {min_bytes} bytes")

    # Check end marker
    end_marker = DEFAULTS["end_marker"]
    if expected_type == "handoff":
        end_marker = DEFAULTS["handoff_end_marker"]
    has_end = end_marker in content
    if DEFAULTS["require_end_marker"] and not has_end:
        result["issues"].append(f"missing end marker: {end_marker}")

    # Check required YAML fields for review type
    if expected_type == "review":
        content_lower = content.lower()
        for field in REQUIRED_REVIEW_FIELDS:
            if f"{field}:" not in content_lower and f'"{field}":' not in content_lower:
                result["issues"].append(f"missing required field: {field}")

    # Check for truncation signals
    if content.rstrip().endswith("...") or re.search(r'\btruncat\b', content[-200:].lower()):
        result["issues"].append("appears truncated")

    # Check not just error/placeholder
    lines = [l.strip() for l in content.split("\n") if l.strip()]
    if len(lines) <= 3 and result["file_size"] < 500:
        result["issues"].append("too few lines — likely error/placeholder")

    result["complete"] = len(result["issues"]) == 0
    return result


def main():
    if len(sys.argv) < 2:
        print("Usage: python validate_gpt_reply_completeness.py <GPT_REPLY.txt> [review|task_plan|handoff]")
        return 2

    path = sys.argv[1]
    expected_type = sys.argv[2] if len(sys.argv) > 2 else "review"

    result = check_completeness(path, expected_type)

    # Output result
    print(f"GPT_REPLY_COMPLETENESS_RESULT:")
    print(f"  file: {result['file']}")
    print(f"  type: {result['expected_type']}")
    print(f"  file_size: {result['file_size']} bytes")
    print(f"  complete: {result['complete']}")
    print(f"  issues:")
    for i in result["issues"]:
        print(f"    - {i}")
    if not result["issues"]:
        print(f"    []")

    return 0 if result["complete"] else 1


if __name__ == "__main__":
    sys.exit(main())
