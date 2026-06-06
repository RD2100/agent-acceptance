"""Validate PROJECT_HISTORY.md structure and required markers."""
import sys
from pathlib import Path

REQUIRED_SECTIONS = [
    "项目定位", "架构", "已完成", "安全边界", "当前状态", "下一步"
]
REQUIRED_MARKER = "END_OF_PROJECT_HISTORY"


def validate(path: str) -> int:
    p = Path(path)
    if not p.exists():
        print(f"FAIL: {path} not found")
        return 1

    text = p.read_text(encoding="utf-8")
    errors = 0

    if not text.strip().endswith(REQUIRED_MARKER):
        print(f"FAIL: {path} missing END_OF_PROJECT_HISTORY")
        errors += 1
    else:
        print(f"PASS: {path} has END_OF_PROJECT_HISTORY")

    for section in REQUIRED_SECTIONS:
        if section not in text:
            print(f"FAIL: {path} missing section: {section}")
            errors += 1

    if errors == 0:
        # all other sections present
        for section in REQUIRED_SECTIONS:
            if section in text:
                print(f"PASS: {path} has section: {section}")

    size = len(text)
    print(f"  size: {size} chars")
    if size < 5000:
        print(f"WARN: {path} is short ({size} chars), may need more detail")
    else:
        print(f"PASS: {path} size sufficient ({size} chars)")

    return errors


if __name__ == "__main__":
    errors = 0
    for arg in sys.argv[1:]:
        errors += validate(arg)
    sys.exit(min(errors, 1))
