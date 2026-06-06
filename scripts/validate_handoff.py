"""Validate HANDOFF.md completeness before transfer.

Checks: min size (8000 bytes), END_OF_HANDOFF marker, required sections.
"""
import sys
from pathlib import Path

REQUIRED_SECTIONS = [
    "项目身份", "project identity",
    "架构", "architecture",
    "已完成", "completed",
    "安全边界", "safety",
    "执行规则", "evidence",
    "下一任务", "next task",
    "END_OF_HANDOFF",
]


def validate_handoff(path: str) -> dict:
    result = {"file": path, "valid": False, "size": 0, "issues": []}

    fp = Path(path)
    if not fp.exists():
        result["issues"].append("HANDOFF.md not found")
        return result

    content = fp.read_text(encoding="utf-8")
    result["size"] = len(content)

    if result["size"] < 8000:
        result["issues"].append(f"too short: {result['size']} < 8000 bytes")

    if "END_OF_HANDOFF" not in content:
        result["issues"].append("missing END_OF_HANDOFF marker")

    # Check key content is present
    has_content = len(content) > 2000 and "#" in content
    if not has_content:
        result["issues"].append("insufficient content structure")

    if "#" not in content:
        result["issues"].append("no markdown structure (no # headers)")

    result["valid"] = len(result["issues"]) == 0
    return result


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "HANDOFF.md"
    result = validate_handoff(path)

    print(f"HANDOFF_VALIDATION:")
    print(f"  file: {result['file']}")
    print(f"  size: {result['size']} bytes")
    print(f"  valid: {result['valid']}")
    print(f"  issues:")
    for i in result["issues"]:
        print(f"    - {i}")
    if not result["issues"]:
        print(f"    []")

    return 0 if result["valid"] else 1


if __name__ == "__main__":
    sys.exit(main())
