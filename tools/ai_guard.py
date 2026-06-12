"""AI Guard - unified rule engine for local and CI governance checks.

Reads .ai/policy.yaml and optional .ai/tasks/<task_id>.yaml.
Used by @go post-execution, pre-commit, pre-push, and GitHub Actions.
"""

import fnmatch
import json
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML required. Install: pip install pyyaml")
    sys.exit(2)


def load_yaml(path):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


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
    """Scan changed files for secret patterns. Paths resolve relative to repo_root.

    Uses streaming line-by-line reads to handle large files without
    loading entire content into memory.
    """
    findings = []
    base = repo_root if repo_root else Path.cwd()
    for file_path in files:
        full_path = base / file_path
        if not full_path.is_file():
            continue
        try:
            with open(str(full_path), "r", encoding="utf-8", errors="ignore") as f:
                for line_number, line in enumerate(f, 1):
                    for pattern in patterns:
                        if re.search(pattern, line):
                            findings.append(f"{file_path}:{line_number}: secret pattern match")
                            break
        except OSError:
            continue
    return findings


def _parse_datetime(value):
    if not isinstance(value, str) or not value.strip():
        raise ValueError("must be a non-empty ISO-8601 string")
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _validate_chain_evidence(chain_path, schema_path, review, repo_root):
    errors = []

    try:
        chain = load_json(str(chain_path))
    except Exception as exc:
        return [f"CHAIN: chain-evidence.json is not valid JSON: {exc}"]

    if not isinstance(chain, dict):
        return ["CHAIN: chain-evidence.json must be a JSON object"]

    try:
        schema = load_json(str(schema_path))
    except Exception as exc:
        return [f"CHAIN: unable to load schema {schema_path}: {exc}"]

    schema_required = schema.get("required", [])
    schema_properties = schema.get("properties", {})
    allowed_extra_fields = {"reviewer_role", "reviewed_at"}
    allowed_fields = set(schema_properties) | allowed_extra_fields

    for field in schema_required:
        if field not in chain:
            errors.append(f"CHAIN: missing required field: {field}")

    unexpected_fields = sorted(set(chain) - allowed_fields)
    if unexpected_fields:
        errors.append(
            "CHAIN: unexpected field(s): " + ", ".join(unexpected_fields)
        )

    for field, rules in schema_properties.items():
        if field not in chain:
            continue
        value = chain[field]
        expected_type = rules.get("type")
        if expected_type == "string":
            if not isinstance(value, str):
                errors.append(f"CHAIN: {field} must be a string")
                continue
            if rules.get("minLength", 0) > len(value):
                errors.append(f"CHAIN: {field} must not be empty")
        elif isinstance(expected_type, list):
            if value is not None and not isinstance(value, str):
                errors.append(f"CHAIN: {field} must be a string or null")

    for field in ("created_at", "reviewed_at", "rerun_verified_at"):
        if field not in chain or chain.get(field) is None:
            continue
        try:
            _parse_datetime(chain[field])
        except ValueError as exc:
            errors.append(f"CHAIN: {field} {exc}")

    if chain.get("run_id") and chain["run_id"] != chain_path.parent.name:
        errors.append(
            "CHAIN: run_id must match evidence directory name "
            f"({chain_path.parent.name})"
        )

    task_file = chain.get("task_file")
    if isinstance(task_file, str) and task_file.strip():
        if not (repo_root / Path(task_file)).is_file():
            errors.append(f"CHAIN: task_file does not exist: {task_file}")

    review_reviewer_id = str(review.get("reviewer_id") or "").strip()
    review_executor_id = str(
        review.get("executor_id") or review.get("coder_id") or ""
    ).strip()
    review_reviewer_role = str(review.get("reviewer_role") or "").strip().lower()

    chain_executor_id = str(chain.get("executor_id") or "").strip()
    chain_reviewer_id = chain.get("reviewer_id")
    chain_reviewer_role = str(chain.get("reviewer_role") or "").strip().lower()

    if review_executor_id and chain_executor_id and review_executor_id != chain_executor_id:
        errors.append("CHAIN: executor_id must match review.yaml")
    if review_reviewer_id and chain_reviewer_id != review_reviewer_id:
        errors.append("CHAIN: reviewer_id must match review.yaml")
    if review_reviewer_role:
        if not chain_reviewer_role:
            errors.append("CHAIN: reviewer_role is required after review")
        elif chain_reviewer_role != review_reviewer_role:
            errors.append("CHAIN: reviewer_role must match review.yaml")
    if chain_reviewer_id is not None and not chain.get("reviewed_at"):
        errors.append("CHAIN: reviewed_at is required when reviewer_id is present")

    created_at = chain.get("created_at")
    reviewed_at = chain.get("reviewed_at")
    if created_at and reviewed_at:
        try:
            if _parse_datetime(reviewed_at) < _parse_datetime(created_at):
                errors.append("CHAIN: reviewed_at must be on or after created_at")
        except ValueError:
            pass

    rerun_verified_at = chain.get("rerun_verified_at")
    rerun_summary = chain.get("rerun_summary")
    if rerun_verified_at and not rerun_summary:
        errors.append("CHAIN: rerun_summary is required when rerun_verified_at is present")
    if rerun_summary and not rerun_verified_at:
        errors.append("CHAIN: rerun_verified_at is required when rerun_summary is present")
    if rerun_verified_at and created_at:
        try:
            if _parse_datetime(rerun_verified_at) < _parse_datetime(created_at):
                errors.append("CHAIN: rerun_verified_at must be on or after created_at")
        except ValueError:
            pass
    return errors


def validate_evidence_dir(evidence_dir, policy, repo_root=None):
    """Validate that a run contains independent reviewer evidence."""
    root = Path(evidence_dir)
    errors = []
    warnings = []
    repo_base = repo_root if repo_root else Path.cwd()

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

    chain_path = root / "chain-evidence.json"
    schema_path = repo_base / "schemas" / "agent-runtime" / "chain-evidence.schema.json"
    if chain_path.is_file():
        errors.extend(
            _validate_chain_evidence(chain_path, schema_path, review, repo_base)
        )

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
    write_out = "--out" in args
    positional = [a for a in args if a != "--out"]
    if not positional:
        print("ERROR: evidence mode requires a run evidence directory")
        sys.exit(2)

    evidence_dir = positional[0]
    repo_root = Path(__file__).resolve().parent.parent
    errors, warnings = validate_evidence_dir(evidence_dir, policy, repo_root=repo_root)
    for warning in warnings:
        print(f"WARNING: {warning}")
    for error in errors:
        print(f"ERROR: {error}")

    evidence_status = "failed" if errors else "pass"

    if write_out:
        out_path = Path(evidence_dir) / "evidence-report.json"
        report = {
            "evidence_status": evidence_status,
            "errors": errors,
            "warnings": warnings,
            "generated_at": datetime.now().isoformat(),
            "producer": "tools/ai_guard.py evidence",
        }
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    if errors:
        print(f"\nAI Guard Evidence: {len(errors)} error(s) - BLOCKED")
        sys.exit(1)

    print("\nAI Guard Evidence: PASS")
    sys.exit(0)


def run_files_mode(args, policy, repo_root):
    """Scan explicitly listed files only (used by pre-commit hook).

    Runs deny_paths, restricted_paths, and secret_patterns checks
    on the provided file list. Does NOT check TaskSpec allow_write.
    """
    deny_paths = policy.get("deny_paths", [])
    restricted_paths = policy.get("restricted_paths", [])
    secret_patterns = policy.get("secret_patterns", [])

    # Normalize: backslash → forward slash, drop empty entries
    files = []
    for f in args:
        normalized = f.replace("\\", "/").strip()
        if normalized:
            files.append(normalized)

    errors = []
    warnings = []

    for path in files:
        if matches(path, deny_paths):
            errors.append(f"DENIED: {path} is on deny list")

    for path in files:
        if matches(path, restricted_paths):
            warnings.append(f"RESTRICTED: {path} requires human review")

    for finding in scan_secrets(files, secret_patterns, repo_root=repo_root):
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

    print(f"\nAI Guard: PASS - {len(files)} file(s) checked, 0 issues")
    sys.exit(0)


def run_diff_mode(mode, args, policy, repo_root):
    deny_paths = policy.get("deny_paths", [])
    restricted_paths = policy.get("restricted_paths", [])
    secret_patterns = policy.get("secret_patterns", [])

    if mode == "staged":
        changed = git_staged_files(repo_root=repo_root)
        allow_write = ["**"]
    elif mode == "task":
        # Commit mode: scan ONLY staged files for all checks.
        # Unstaged dirty baseline must not block a clean staged commit.
        task_file = args[0] if args else None
        if task_file:
            task = load_yaml(task_file)
        else:
            task_path = repo_root / ".ai" / "current-task.yaml"
            task = load_yaml(str(task_path)) if task_path.exists() else {}
        if not isinstance(task, dict):
            task = {}
        changed = git_staged_files(repo_root=repo_root)
        conflict_registry = task.get("conflict_registry", {})
        allow_write = (
            task.get("allow_write")
            or task.get("write_set")
            or conflict_registry.get("write_set")
            or []
        )
    elif mode == "audit":
        # Repo-audit mode: full working-tree scan for deny/restricted/secrets.
        # Does NOT check TaskSpec scope (scope is commit-time concern only).
        base = "origin/main" if _has_remote(repo_root) else "HEAD~1"
        changed = git_changed_files(base, repo_root=repo_root)
        allow_write = ["**"]
    else:
        # Default full mode: full working-tree scan (backward compatible).
        base = "origin/main" if _has_remote(repo_root) else "HEAD~1"
        changed = git_changed_files(base, repo_root=repo_root)
        allow_write = ["**"]

    errors = []
    warnings = []

    for path in changed:
        if matches(path, deny_paths):
            errors.append(f"DENIED: {path} is on deny list")

    for path in changed:
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
    if "--root" in sys.argv:
        idx = sys.argv.index("--root")
        repo_root = Path(sys.argv[idx + 1])
        del sys.argv[idx:idx + 2]
    policy_path = repo_root / ".ai" / "policy.yaml"

    if not policy_path.exists():
        print("ERROR: .ai/policy.yaml not found. Run bootstrap.")
        sys.exit(2)

    policy = load_yaml(str(policy_path))
    mode = sys.argv[1] if len(sys.argv) > 1 else "full"
    args = sys.argv[2:]

    if mode == "--files":
        run_files_mode(args, policy, repo_root)

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
