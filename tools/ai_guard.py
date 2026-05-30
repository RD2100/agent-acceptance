"""AI Guard — Unified rule engine for local + CI governance checks.

Reads .ai/policy.yaml and optional .ai/tasks/<task_id>.yaml.
Used by: @go post-execution, pre-commit, pre-push, GitHub Actions.
"""

import fnmatch
import os
import re
import subprocess
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML required. Install: pip install pyyaml")
    sys.exit(2)


def load_yaml(path):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def git_changed_files(base="HEAD"):
    """Return list of changed files relative to base."""
    try:
        result = subprocess.run(
            ["git", "diff", "--name-only", base],
            text=True,
            capture_output=True,
            check=True,
        )
    except subprocess.CalledProcessError:
        # May fail in shallow clones; try diff against HEAD~1
        result = subprocess.run(
            ["git", "diff", "--name-only", "HEAD~1"],
            text=True,
            capture_output=True,
        )
    return [
        line.strip().replace("\\", "/")
        for line in result.stdout.splitlines()
        if line.strip()
    ]


def git_staged_files():
    """Return list of staged files."""
    result = subprocess.run(
        ["git", "diff", "--name-only", "--cached"],
        text=True,
        capture_output=True,
    )
    return [
        line.strip().replace("\\", "/")
        for line in result.stdout.splitlines()
        if line.strip()
    ]


def matches(path, patterns):
    """Check if path matches any fnmatch pattern."""
    return any(fnmatch.fnmatch(path, p) for p in patterns)


def scan_secrets(files, patterns):
    """Scan changed files for secret patterns."""
    findings = []
    for fpath in files:
        if not os.path.isfile(fpath):
            continue
        # Skip binary and large files
        if os.path.getsize(fpath) > 1_000_000:
            continue
        try:
            with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
        except OSError:
            continue
        for i, line in enumerate(content.splitlines(), 1):
            for pat in patterns:
                if re.search(pat, line):
                    findings.append(f"{fpath}:{i}: secret pattern match")
                    break
    return findings


def main():
    repo_root = Path(__file__).resolve().parent.parent
    policy_path = repo_root / ".ai" / "policy.yaml"

    if not policy_path.exists():
        print("ERROR: .ai/policy.yaml not found. Run bootstrap.")
        sys.exit(2)

    policy = load_yaml(str(policy_path))
    deny_paths = policy.get("deny_paths", [])
    restricted_paths = policy.get("restricted_paths", [])
    secret_patterns = policy.get("secret_patterns", [])

    # Determine mode: staged (pre-commit), post-exec (task), or full (CI)
    mode = sys.argv[1] if len(sys.argv) > 1 else "full"

    if mode == "staged":
        changed = git_staged_files()
    elif mode == "task":
        # Read task allow_write from .ai/current-task.yaml or argv
        task_file = sys.argv[2] if len(sys.argv) > 2 else None
        if task_file:
            task = load_yaml(task_file)
        else:
            task_path = repo_root / ".ai" / "current-task.yaml"
            task = load_yaml(str(task_path)) if task_path.exists() else {}
        changed = git_changed_files()
        allow_write = task.get("allow_write", [])
    else:
        changed = git_changed_files("origin/main") if _has_remote() else git_changed_files("HEAD~1")
        allow_write = ["**"]  # CI full mode: everything allowed unless denied

    errors = []
    warnings = []

    # 1. Deny path check
    for path in changed:
        if matches(path, deny_paths):
            errors.append(f"DENIED: {path} is on deny list")
            continue
        if mode == "task" and not matches(path, allow_write):
            errors.append(f"SCOPE: {path} outside TaskSpec allow_write")

    # 2. Restricted path check
    for path in changed:
        if matches(path, restricted_paths):
            warnings.append(f"RESTRICTED: {path} requires human review")

    # 3. Secret scan
    secret_findings = scan_secrets(changed, secret_patterns)
    for f in secret_findings:
        errors.append(f"SECRET: {f}")

    # Output
    for w in warnings:
        print(f"WARNING: {w}")
    for e in errors:
        print(f"ERROR: {e}")

    if errors:
        print(f"\nAI Guard: {len(errors)} error(s), {len(warnings)} warning(s) — BLOCKED")
        sys.exit(1)
    elif warnings:
        print(f"\nAI Guard: 0 errors, {len(warnings)} warning(s) — PASS with warnings")
        sys.exit(0)
    else:
        print(f"\nAI Guard: PASS — {len(changed)} file(s) checked, 0 issues")
        sys.exit(0)


def _has_remote():
    result = subprocess.run(
        ["git", "remote"], text=True, capture_output=True
    )
    return bool(result.stdout.strip())


if __name__ == "__main__":
    main()