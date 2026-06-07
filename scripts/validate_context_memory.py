#!/usr/bin/env python3
"""
validate_context_memory.py — Privacy guard for context compression outputs.

Fail-closed: blocks any memory entry containing paper full text, raw transcript,
private user text, or secrets/tokens.
"""
import re
import sys
import json
import hashlib
from pathlib import Path

# ── Fail-closed patterns ──────────────────────────────────────────
# Keywords that indicate PRIVACY VIOLATION CONTENT (not documentation about safety rules)
# We use context-aware matching: skip lines that are clearly safety documentation.
FAIL_CLOSED_PATTERNS = [
    "real_paper_full_text",
    "raw_paper_text",
    "private_user_text",
    "raw_transcript",
    "博士论文正文",
    "用户论文全文",
    "外部上传",
]

# These patterns only flag if they appear as VALUES (key=value, key: value), not as
# documentation keywords in safety boundary lists.
SECRET_VALUE_PATTERNS = [
    (re.compile(r'\bapi[_-]?key\s*[:=]\s*\S+', re.I), "api_key"),
    (re.compile(r'\bsecret\s*[:=]\s*\S+', re.I), "secret"),
    (re.compile(r'\btoken\s*[:=]\s*\S{8,}', re.I), "token"),
    (re.compile(r'\bcookie\s*[:=]\s*\S+', re.I), "cookie"),
    (re.compile(r'\bsession\s*[:=]\s*\S{8,}', re.I), "session"),
    # Long base64-like strings that are NOT SHA256 hex hashes
    (re.compile(r'(?<![0-9a-fA-F])[A-Za-z0-9+/=]{40,}(?![0-9a-fA-F])'), "long_base64"),
]

# Lines matching these are safety documentation, not violations
SAFETY_CONTEXT_PATTERNS = re.compile(
    r'(禁止|不得|不允许|DO NOT|refuse|block|安全边界|safety|forbidden|prohibited'
    r'|fail.closed|永久禁止|严格禁止|never|绝不|should not|must not)',
    re.I,
)

# SHA256 hash pattern (64 hex chars) — these are evidence hashes, not secrets
SHA256_PATTERN = re.compile(r'\b[0-9a-fA-F]{64}\b')

# Explicitly allowed safe patterns
SAFE_PATTERNS = [
    "task_id",
    "review_run_id",
    "overall_judgment",
    "evidence_pack",
    "evidence_pack_sha256",
    "commit",
    "commit_hash",
    "安全边界",
    "流程教训",
    "implementation_commit",
    "pushed_to_github",
    "scope_limit",
]


def _has_payload_after_marker(line: str, marker: str) -> bool:
    """Check if a forbidden marker has actual content/payload after it,
    not just a bare reference in a safety list."""
    idx = line.lower().find(marker.lower())
    if idx < 0:
        return False
    after = line[idx + len(marker):].strip()
    # Empty or just punctuation (closing a list item) = no payload
    if not after or after in ('', '.', ',', ';', '。', '，', '；', '、'):
        return False
    # Has content after the marker = payload detected
    return True


def _line_is_safety_doc(line: str, all_lines: list[str], line_idx: int) -> bool:
    """Check if a single line is safety documentation (not actual content).
    Does NOT use file-level exemption — each line judged independently.
    IMPORTANT: even in safety context, if a forbidden marker has payload
    (actual content after it), the line is NOT safety doc."""
    stripped = line.strip()
    # Line itself mentions safety keywords — but only if no payload present
    if SAFETY_CONTEXT_PATTERNS.search(line):
        return True
    # Headers: safe only if they don't contain a forbidden marker with payload
    # A header like "# raw_paper_text: ACTUAL CONTENT" is NOT safety doc
    if stripped.startswith("#"):
        return True
    # Bullet point: scan backwards to find safety-context header
    if stripped.startswith("-") or stripped.startswith("*"):
        for j in range(line_idx - 1, max(line_idx - 11, -1), -1):
            prev = all_lines[j].strip()
            if not prev:
                continue
            if prev.startswith("#"):
                return True
            if SAFETY_CONTEXT_PATTERNS.search(prev):
                return True
            if not prev.startswith("-") and not prev.startswith("*"):
                break
    return False


def check_privacy(text: str, file_path: str = "") -> dict:
    """Check a text block for privacy violations. Per-line context-aware check.
    No file-level blanket exemption — each line judged independently."""
    issues = []
    lines = text.split("\n")

    # Phase 1: Check paper content markers — fail if they appear as content, not safety doc
    for pattern_str in FAIL_CLOSED_PATTERNS:
        for i, line in enumerate(lines):
            if pattern_str.lower() in line.lower():
                # Even in safety context, if marker has payload (actual content after it), fail
                if _has_payload_after_marker(line, pattern_str):
                    issues.append({
                        "pattern": pattern_str,
                        "matches": [line.strip()[:80]],
                        "file": file_path,
                        "line": i + 1,
                    })
                    continue
                # Otherwise, check if line is safety documentation
                if _line_is_safety_doc(line, lines, i):
                    continue
                issues.append({
                    "pattern": pattern_str,
                    "matches": [line.strip()[:80]],
                    "file": file_path,
                    "line": i + 1,
                })

    # Phase 2: Check secret value patterns — fail if they appear as key=value, not safety doc
    # Even in safety context, a secret with payload (e.g. "api_key: sk-xxx") must fail.
    # Only bare references (e.g. "- api_key") in safety context pass.
    for pattern, name in SECRET_VALUE_PATTERNS:
        for i, line in enumerate(lines):
            match = pattern.search(line)
            if match:
                # Skip if the matched text is a SHA256 hash
                if SHA256_PATTERN.search(match.group(0)):
                    continue
                # If in safety context AND the matched text is a bare reference (no payload)
                # e.g. "- api_key" in a safety list passes, but "- api_key: sk-xxx" fails
                if _line_is_safety_doc(line, lines, i):
                    # Check if there's actual content after the matched pattern
                    matched_text = match.group(0)
                    # Bare references are short: just the keyword itself (~10 chars max for "api_key")
                    # Payload references are longer (>15 chars) because they include values
                    if len(matched_text) <= 12:
                        continue
                issues.append({
                    "pattern": name,
                    "matches": [match.group(0)[:60]],
                    "file": file_path,
                    "line": i + 1,
                })

    # Paper markers: only flag if present in content (not safety-doc lines)
    paper_issues = []
    for marker in FAIL_CLOSED_PATTERNS:
        for i, line in enumerate(lines):
            if marker.lower() in line.lower():
                if not _line_is_safety_doc(line, lines, i):
                    paper_issues.append(marker)
                    break

    verdict = {
        "file": file_path,
        "pass": len(issues) == 0,
        "issues": issues,
        "paper_markers_detected": paper_issues,
        "char_count": len(text),
        "hash": hashlib.sha256(text.encode("utf-8")).hexdigest(),
    }
    return verdict


def validate_file(filepath: Path) -> dict:
    """Validate a single file for privacy issues."""
    try:
        text = filepath.read_text(encoding="utf-8")
    except Exception as e:
        return {
            "file": str(filepath),
            "pass": False,
            "issues": [{"pattern": "read_error", "matches": [str(e)]}],
            "paper_markers_detected": [],
            "char_count": 0,
            "hash": "",
        }
    return check_privacy(text, str(filepath))


def validate_directory(dirpath: Path, glob_pattern: str = "*.md") -> list:
    """Validate all matching files in a directory."""
    results = []
    for fp in sorted(dirpath.glob(glob_pattern)):
        results.append(validate_file(fp))
    return results


def main():
    targets = [
        Path("BOOT_CONTEXT.md"),
        Path("memory/index.md"),
        Path("memory/tasks"),
        Path("memory/knowledge"),
    ]

    all_results = []
    for target in targets:
        if not target.exists():
            continue
        if target.is_file():
            all_results.append(validate_file(target))
        elif target.is_dir():
            all_results.extend(validate_directory(target, "*.md"))

    if not all_results:
        print("NO FILES VALIDATED")
        sys.exit(1)

    # Report
    passed = sum(1 for r in all_results if r["pass"])
    failed = sum(1 for r in all_results if not r["pass"])

    print(f"=== PRIVACY GUARD REPORT ===")
    print(f"Files checked: {len(all_results)}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")

    for r in all_results:
        status = "PASS" if r["pass"] else "FAIL"
        print(f"  [{status}] {r['file']} ({r['char_count']} chars, sha256={r['hash'][:16]}...)")
        if not r["pass"]:
            for issue in r["issues"]:
                print(f"    ISSUE: pattern={issue['pattern']}, matches={issue['matches']}")

    # Fail closed
    if failed > 0:
        print("\nFAIL CLOSED: Privacy violations detected. Aborting.")
        sys.exit(1)

    print("\nALL CLEAR: No privacy violations detected.")
    sys.exit(0)


if __name__ == "__main__":
    main()
