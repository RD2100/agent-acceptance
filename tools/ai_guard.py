"""AI Guard - unified rule engine for local and CI governance checks.

Reads .ai/policy.yaml and optional .ai/tasks/<task_id>.yaml.
Used by @go post-execution, pre-commit, pre-push, and GitHub Actions.
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


def git_changed_files(base="HEAD", repo_root=None):
    """Return list of changed files relative to base."""
    cwd = str(repo_root) if repo_root else None
    try:
        result = subprocess.run(
            ["git", "diff", "--name-only", base],
            text=True,
            capture_output=True,
            check=True,
            cwd=cwd,
        )
    except subprocess.CalledProcessError:
        result = subprocess.run(
            ["git", "diff", "--name-only", "HEAD~1"],
            text=True,
            capture_output=True,
            cwd=cwd,
        )
    return [
        line.strip().replace("\\", "/")
        for line in result.stdout.splitlines()
        if line.strip()
    ]


def git_staged_files(repo_root=None):
    """Return list of staged files."""
    cwd = str(repo_root) if repo_root else None
    result = subprocess.run(
        ["git", "diff", "--name-only", "--cached"],
        text=True,
        capture_output=True,
        cwd=cwd,
    )
    return [
        line.strip().replace("\\", "/")
        for line in result.stdout.splitlines()
        if line.strip()
    ]


def matches(path, patterns):
    """Check if path matches any fnmatch pattern."""
    return any(fnmatch.fnmatch(path, pattern) for pattern in patterns)


def scan_secrets(files, patterns, repo_root=None):
    """Scan changed files for secret patterns. Paths resolve relative to repo_root."""
    findings = []
    base = repo_root if repo_root else Path.cwd()
    for file_path in files:
        full_path = base / file_path
        if not full_path.is_file():
            continue
        if full_path.stat().st_size > 1_000_000:
            continue
        try:
            with open(str(full_path), "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
        except OSError:
            continue
        for line_number, line in enumerate(content.splitlines(), 1):
            for pattern in patterns:
                if re.search(pattern, line):
                    findings.append(f"{file_path}:{line_number}: secret pattern match")
                    break
    return findings


def validate_evidence_dir(evidence_dir, policy):
    """Validate that a run contains independent reviewer evidence."""
    root = Path(evidence_dir)
    errors = []
    warnings = []

    if not root.exists() or not root.is_dir():
        return [f"EVIDENCE: directory not found: {evidence_dir}"], warnings

    for rel_path in policy.get("required_evidence_files", []):
        path = root / rel_path
        if not path.is_file():
            errors.append(f"EVIDENCE: missing required file: {rel_path}")
        elif path.stat().st_size == 0:
            errors.append(f"EVIDENCE: required file is empty: {rel_path}")

    review_yaml_path = root / "review.yaml"
    if not review_yaml_path.is_file():
        return errors, warnings

    try:
        review = load_yaml(str(review_yaml_path)) or {}
    except Exception as exc:
        errors.append(f"REVIEW: review.yaml is not valid YAML: {exc}")
        return errors, warnings

    reviewer = review.get("reviewer", {})
    reviewer_role = str(
        review.get("reviewer_role") or reviewer.get("role") or ""
    ).strip().lower()
    forbidden_roles = {
        str(role).strip().lower()
        for role in policy.get("reviewer_forbidden_roles", [])
    }

    if not reviewer_role:
        errors.append("REVIEW: reviewer_role is required")
    elif reviewer_role in forbidden_roles:
        errors.append(f"REVIEW: reviewer_role must not be {reviewer_role}")

    reviewer_type = str(review.get("reviewer_type") or "").strip().lower()
    if reviewer_type and reviewer_type not in {"ai", "human"}:
        errors.append("REVIEW: reviewer_type must be ai or human")

    reviewer_id = str(review.get("reviewer_id") or reviewer.get("id") or "").strip()
    executor_id = str(review.get("executor_id") or review.get("coder_id") or "").strip()
    if not reviewer_id:
        errors.append("REVIEW: reviewer_id is required")
    if not executor_id:
        errors.append("REVIEW: executor_id is required")
    if reviewer_id and executor_id and reviewer_id == executor_id:
        errors.append("REVIEW: reviewer_id must differ from executor_id")

    verdict = str(review.get("verdict", "")).strip().lower()
    if verdict not in {"pass", "blocked", "fail", "escalate"}:
        errors.append("REVIEW: verdict must be pass, blocked, fail, or escalate")

    findings = review.get("findings", []) or []
    blocking_severities = {
        str(severity).strip().upper()
        for severity in policy.get("blocking_finding_severities", [])
    }
    unresolved = []
    for finding in findings:
        if not isinstance(finding, dict):
            continue
        severity = str(finding.get("severity", "")).strip().upper()
        status = str(finding.get("status", "")).strip().lower()
        if severity in blocking_severities and status not in {"resolved", "false_positive"}:
            unresolved.append(finding.get("id") or finding.get("title") or severity)

    if verdict == "pass" and unresolved:
        errors.append(
            "REVIEW: pass verdict is invalid with unresolved P0/P1 findings: "
            + ", ".join(str(item) for item in unresolved)
        )

    required_inputs = {
        "diff.patch",
        "test-output.md",
        "safety-report.json",
        "chain-evidence.json",
    }
    reviewed_inputs = {
        str(item).replace("\\", "/")
        for item in (review.get("reviewed_inputs", []) or [])
    }
    missing_inputs = sorted(required_inputs - reviewed_inputs)
    if missing_inputs:
        errors.append(
            "REVIEW: review.yaml must list reviewed_inputs: "
            + ", ".join(missing_inputs)
        )

    return errors, warnings


def run_evidence_mode(args, policy):
    if not args:
        print("ERROR: evidence mode requires a run evidence directory")
        sys.exit(2)

    errors, warnings = validate_evidence_dir(args[0], policy)
    for warning in warnings:
        print(f"WARNING: {warning}")
    for error in errors:
        print(f"ERROR: {error}")

    if errors:
        print(f"\nAI Guard Evidence: {len(errors)} error(s) - BLOCKED")
        sys.exit(1)

    print("\nAI Guard Evidence: PASS")
    sys.exit(0)


def run_diff_mode(mode, args, policy, repo_root):
    deny_paths = policy.get("deny_paths", [])
    restricted_paths = policy.get("restricted_paths", [])
    secret_patterns = policy.get("secret_patterns", [])

    if mode == "staged":
        changed = git_staged_files(repo_root=repo_root)
        allow_write = ["**"]
    elif mode == "task":
        task_file = args[0] if args else None
        if task_file:
            task = load_yaml(task_file)
        else:
            task_path = repo_root / ".ai" / "current-task.yaml"
            task = load_yaml(str(task_path)) if task_path.exists() else {}
        if not isinstance(task, dict):
            task = {}
        changed = git_changed_files(repo_root=repo_root)
        conflict_registry = task.get("conflict_registry", {})
        allow_write = (
            task.get("allow_write")
            or task.get("write_set")
            or conflict_registry.get("write_set")
            or []
        )
    else:
        base = "origin/main" if _has_remote(repo_root) else "HEAD~1"
        changed = git_changed_files(base, repo_root=repo_root)
        allow_write = ["**"]

    errors = []
    warnings = []

    for path in changed:
        if matches(path, deny_paths):
            errors.append(f"DENIED: {path} is on deny list")
            continue
        if mode == "task" and not matches(path, allow_write):
            errors.append(f"SCOPE: {path} outside TaskSpec allow_write")

    for path in changed:
        if matches(path, restricted_paths):
            warnings.append(f"RESTRICTED: {path} requires human review")

    for finding in scan_secrets(changed, secret_patterns, repo_root=repo_root):
        errors.append(f"SECRET: {finding}")

    for warning in warnings:
        print(f"WARNING: {warning}")
    for error in errors:
        print(f"ERROR: {error}")

    if errors:
        print(f"\nAI Guard: {len(errors)} error(s), {len(warnings)} warning(s) - BLOCKED")
        sys.exit(1)
    if warnings:
        print(f"\nAI Guard: 0 errors, {len(warnings)} warning(s) - PASS with warnings")
        sys.exit(0)

    print(f"\nAI Guard: PASS - {len(changed)} file(s) checked, 0 issues")
    sys.exit(0)


def main():
    repo_root = Path(__file__).resolve().parent.parent
    policy_path = repo_root / ".ai" / "policy.yaml"

    if not policy_path.exists():
        print("ERROR: .ai/policy.yaml not found. Run bootstrap.")
        sys.exit(2)

    policy = load_yaml(str(policy_path))
    mode = sys.argv[1] if len(sys.argv) > 1 else "full"
    args = sys.argv[2:]

    if mode == "evidence":
        run_evidence_mode(args, policy)

    run_diff_mode(mode, args, policy, repo_root)


def _has_remote(repo_root=None):
    cwd = str(repo_root) if repo_root else None
    result = subprocess.run(
        ["git", "remote"], text=True, capture_output=True, cwd=cwd
    )
    return bool(result.stdout.strip())


if __name__ == "__main__":
    main()
