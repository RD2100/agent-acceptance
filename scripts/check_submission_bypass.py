"""Check for unauthorized direct Playwright / ad-hoc submission scripts.

Detects: sync_playwright, connect_over_cdp, submit_to_gpt, live_handoff_transfer
         in non-approved paths.
Allowed locations: control_plane/playwright_bridge.py, control_plane/cdp_adapter.py,
                   control_plane/submission_adapter.py, tests/, declared fixtures.
Exit 0: no bypass detected. Exit 1: bypass found.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

BYPASS_PATTERNS = {
    "sync_playwright": "直接使用 Playwright sync API（应在 playwright_bridge.py 中）",
    "connect_over_cdp": "直接连接 CDP（应在 cdp_adapter.py 或 playwright_bridge.py 中）",
    "submit_to_gpt": "ad-hoc GPT 提交脚本（应使用 submission_adapter）",
    "live_handoff_transfer": "绕过 bridge 的 handoff 传输（逻辑已整合进 playwright_bridge.py）",
}

ALLOWED_PATHS = {
    "control_plane/playwright_bridge.py",
    "control_plane/cdp_adapter.py",
    "control_plane/submission_adapter.py",
    "control_plane/live_handoff_transfer.py",  # historical artifact
}

ALWAYS_ALLOWED_DIRS = {
    "tests",
    ".git",
    "__pycache__",
    ".pytest_cache",
    "archive",
    ".backup",
}

DECLARED_EXCEPTIONS = {
    "docs/submit_proposal_to_gpt.py",
    "evidence_packs/paper-a1-contract-design-v1/submit_to_gpt.py",
    "scripts/check_submission_bypass.py",  # self — contains patterns as detection rules, not usage
    "tests/test_framework_usage.py",  # references patterns in test assertions
}


def should_skip(path: Path) -> bool:
    """Skip non-code files and always-allowed dirs."""
    parts = path.parts
    for d in ALWAYS_ALLOWED_DIRS:
        if d in parts:
            return True
    if path.suffix not in (".py",):
        return True
    return False


def is_allowed(path: Path) -> bool:
    """Check if path is in allowed list."""
    try:
        rel = str(path.relative_to(ROOT)).replace("\\", "/")
    except ValueError:
        return True  # outside repo
    if rel in DECLARED_EXCEPTIONS:
        return True
    for allowed in ALLOWED_PATHS:
        if rel == allowed:
            return True
    # Check if under tests/
    if "tests/" in rel or rel.startswith("tests/"):
        return True
    return False


def find_bypasses():
    """Scan repo for bypass patterns in unauthorized files."""
    found = []

    for py_file in ROOT.rglob("*.py"):
        if should_skip(py_file):
            continue
        if is_allowed(py_file):
            continue

        try:
            content = py_file.read_text(encoding="utf-8")
        except Exception:
            continue

        for pattern, description in BYPASS_PATTERNS.items():
            if pattern in content:
                rel = str(py_file.relative_to(ROOT)).replace("\\", "/")
                found.append({
                    "file": rel,
                    "pattern": pattern,
                    "description": description,
                })

    return found


def main():
    print("=== Submission Bypass Check ===")
    bypasses = find_bypasses()

    if not bypasses:
        print("PASS: No unauthorized submission bypass patterns detected.")
        return 0

    print(f"BLOCKED: {len(bypasses)} bypass pattern(s) detected:")
    for b in bypasses:
        print(f"  - {b['file']}: {b['pattern']} ({b['description']})")
    print()
    print("Fix: move Playwright/CDP usage into approved adapters, or declare as exception.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
