"""Create and finalize @go run evidence packages."""

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None


def utc_now():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def run_command(command, cwd):
    return subprocess.run(
        command,
        cwd=str(cwd),
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
    )


def write_text(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def cmd_init(args, repo_root):
    run_dir = Path(args.run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)

    diff = run_command(
        ["git", "diff", "--binary", "HEAD", "--", ".", ":(exclude)runs/**"],
        repo_root,
    )
    write_text(run_dir / "diff.patch", diff.stdout or "\n")

    if not (run_dir / "test-output.md").exists():
        write_text(
            run_dir / "test-output.md",
            "# Test Output\n\nNo test output captured yet. Tester must replace this file.\n",
        )

    chain = {
        "run_id": args.run_id,
        "task_file": args.task,
        "executor_id": args.executor_id,
        "reviewer_id": None,
        "created_at": utc_now(),
        "producer": "tools/go_evidence.py init",
    }
    write_json(run_dir / "chain-evidence.json", chain)
    print(f"Evidence initialized: {run_dir}")


def cmd_guard(args, repo_root):
    run_dir = Path(args.run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)

    command = ["python", "tools/ai_guard.py", "task"]
    if args.task:
        command.append(args.task)

    result = run_command(command, repo_root)
    payload = {
        "generated_at": utc_now(),
        "producer": "tools/go_evidence.py guard",
        "command": " ".join(command),
        "exit_code": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
    }
    write_json(run_dir / "safety-report.json", payload)
    print(result.stdout, end="")
    print(result.stderr, end="", file=sys.stderr)
    return result.returncode


def cmd_finalize(args, repo_root):
    run_dir = Path(args.run_dir)
    review_yaml = run_dir / "review.yaml"
    chain_path = run_dir / "chain-evidence.json"
    if yaml and review_yaml.is_file() and chain_path.is_file():
        try:
            review = yaml.safe_load(review_yaml.read_text(encoding="utf-8")) or {}
            chain = json.loads(chain_path.read_text(encoding="utf-8"))
            chain["reviewer_id"] = review.get("reviewer_id")
            chain["reviewer_role"] = review.get("reviewer_role")
            chain["reviewed_at"] = utc_now()
            write_json(chain_path, chain)
        except Exception:
            pass

    write_text(
        run_dir / "final-report.md",
        "# Final Report\n\nFinalization in progress; this file will be replaced by the deterministic finalizer.\n",
    )
    command = ["python", "tools/ai_guard.py", "evidence", str(run_dir)]
    result = run_command(command, repo_root)

    status = "passed" if result.returncode == 0 else "blocked"
    report = [
        "# Final Report",
        "",
        f"- Generated at: {utc_now()}",
        f"- Status: {status}",
        f"- Evidence directory: {run_dir}",
        f"- Command: {' '.join(command)}",
        "",
        "## Output",
        "",
        "```text",
        result.stdout.strip(),
        result.stderr.strip(),
        "```",
        "",
    ]
    write_text(run_dir / "final-report.md", "\n".join(report))
    print(result.stdout, end="")
    print(result.stderr, end="", file=sys.stderr)
    return result.returncode


def main():
    parser = argparse.ArgumentParser(description="Create @go evidence packages")
    parser.add_argument("--repo-root", default=".", help="Repository root")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init")
    init_parser.add_argument("run_dir")
    init_parser.add_argument("--run-id", required=True)
    init_parser.add_argument("--task", required=True)
    init_parser.add_argument("--executor-id", required=True)

    guard_parser = subparsers.add_parser("guard")
    guard_parser.add_argument("run_dir")
    guard_parser.add_argument("--task")

    finalize_parser = subparsers.add_parser("finalize")
    finalize_parser.add_argument("run_dir")

    args = parser.parse_args()
    repo_root = Path(args.repo_root).resolve()

    if args.command == "init":
        cmd_init(args, repo_root)
        return 0
    if args.command == "guard":
        return cmd_guard(args, repo_root)
    if args.command == "finalize":
        return cmd_finalize(args, repo_root)
    return 2


if __name__ == "__main__":
    sys.exit(main())
