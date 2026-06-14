#!/usr/bin/env python3
"""Read-only Route A preflight for the future devframe-system merge.

The checker never fetches, builds, tests, installs packages, runs runtimes, or
mutates the target/source repositories. It only reads local git metadata and
reports whether the current state can be used as a strict clean baseline.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Sequence


REPO = Path(__file__).resolve().parent.parent
DEFAULT_TARGET = Path(r"D:\devframe-system")


@dataclass(frozen=True)
class RepoSpec:
    project_id: str
    path: Path


DEFAULT_REPOS = [
    RepoSpec("agent-acceptance", Path(r"D:\agent-acceptance")),
    RepoSpec("devframe-control-plane", Path(r"D:\devframe-control-plane")),
    RepoSpec("dev-frame-opencode", Path(r"D:\dev-frame-opencode")),
    RepoSpec("test-frame", Path(r"D:\test-frame")),
]

GitRunner = Callable[[Path, Sequence[str]], subprocess.CompletedProcess[str]]


def _run_git(repo: Path, args: Sequence[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True,
        text=True,
        check=False,
    )


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _completed_ok(result: subprocess.CompletedProcess[str]) -> bool:
    return result.returncode == 0


def _git_text(
    repo: Path, args: Sequence[str], runner: GitRunner
) -> tuple[str | None, str | None]:
    result = runner(repo, args)
    if not _completed_ok(result):
        detail = (result.stderr or result.stdout or "git command failed").strip()
        return None, detail
    return result.stdout.strip(), None


def _git_status_text(repo: Path, runner: GitRunner) -> tuple[str | None, str | None]:
    result = runner(repo, ["status", "--porcelain=v1", "-uall"])
    if not _completed_ok(result):
        detail = (result.stderr or result.stdout or "git status failed").strip()
        return None, detail
    return result.stdout.rstrip("\r\n"), None


def _status_counts(lines: list[str]) -> dict[str, int]:
    staged = 0
    unstaged = 0
    untracked = 0
    tracked_dirty = 0
    for line in lines:
        if line.startswith("??"):
            untracked += 1
            continue
        tracked_dirty += 1
        if len(line) >= 1 and line[0] not in {" ", "?"}:
            staged += 1
        if len(line) >= 2 and line[1] != " ":
            unstaged += 1
    return {
        "tracked_dirty": tracked_dirty,
        "staged": staged,
        "unstaged": unstaged,
        "untracked": untracked,
        "total": len(lines),
    }


def _sample_status(lines: list[str], limit: int = 12) -> list[str]:
    return lines[:limit]


def probe_repo(spec: RepoSpec, runner: GitRunner = _run_git) -> dict:
    repo = spec.path
    record = {
        "project_id": spec.project_id,
        "path": str(repo),
        "exists": repo.exists(),
        "status": "blocked",
        "branch": None,
        "head": None,
        "upstream": None,
        "upstream_head": None,
        "dirty": {
            "tracked_dirty": 0,
            "staged": 0,
            "unstaged": 0,
            "untracked": 0,
            "total": 0,
        },
        "sample_status": [],
        "detail": "",
    }
    if not repo.exists():
        record["detail"] = "repository path does not exist"
        return record

    inside, error = _git_text(repo, ["rev-parse", "--is-inside-work-tree"], runner)
    if error or inside != "true":
        record["detail"] = error or "path is not a git worktree"
        return record

    branch, error = _git_text(repo, ["branch", "--show-current"], runner)
    if error:
        record["detail"] = error
        return record
    record["branch"] = branch

    head, error = _git_text(repo, ["rev-parse", "HEAD"], runner)
    if error:
        record["detail"] = error
        return record
    record["head"] = head

    upstream, error = _git_text(
        repo, ["rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}"], runner
    )
    if error:
        record["status"] = "human_required"
        record["detail"] = "upstream is not configured"
        return record
    record["upstream"] = upstream

    upstream_head, error = _git_text(repo, ["rev-parse", "@{u}"], runner)
    if error:
        record["status"] = "human_required"
        record["detail"] = "upstream head cannot be resolved"
        return record
    record["upstream_head"] = upstream_head

    status_text, error = _git_status_text(repo, runner)
    if error:
        record["detail"] = error
        return record
    status_lines = [line for line in (status_text or "").splitlines() if line.strip()]
    record["dirty"] = _status_counts(status_lines)
    record["sample_status"] = _sample_status(status_lines)

    if status_lines:
        record["status"] = "human_required"
        record["detail"] = "worktree is dirty; cannot freeze current HEAD as baseline"
        return record
    if head != upstream_head:
        record["status"] = "human_required"
        record["detail"] = "HEAD does not match upstream head"
        return record

    record["status"] = "passed"
    record["detail"] = "clean worktree with HEAD equal to upstream"
    return record


def probe_target(target_path: Path) -> dict:
    exists = target_path.exists()
    record = {
        "path": str(target_path),
        "exists": exists,
        "status": "passed",
        "detail": "target path is absent and safe for a future explicit bootstrap",
        "has_git_dir": False,
        "has_gitmodules": False,
        "item_count": 0,
    }
    if not exists:
        return record

    has_git_dir = (target_path / ".git").exists()
    has_gitmodules = (target_path / ".gitmodules").exists()
    item_count = sum(1 for _ in target_path.iterdir()) if target_path.is_dir() else 0
    record.update(
        {
            "has_git_dir": has_git_dir,
            "has_gitmodules": has_gitmodules,
            "item_count": item_count,
        }
    )
    if has_gitmodules:
        record["status"] = "blocked"
        record["detail"] = "target path already contains .gitmodules"
    elif has_git_dir:
        record["status"] = "human_required"
        record["detail"] = "target path is already a git worktree; route approval required"
    else:
        record["status"] = "human_required"
        record["detail"] = "target path already exists; route approval required before bootstrap"
    return record


def evaluate_route_a_preflight(
    repos: list[RepoSpec] | None = None,
    target_path: Path = DEFAULT_TARGET,
    runner: GitRunner = _run_git,
) -> tuple[int, dict]:
    repos = repos or DEFAULT_REPOS
    repo_records = [probe_repo(spec, runner) for spec in repos]
    target_record = probe_target(target_path)

    statuses = [record["status"] for record in repo_records] + [target_record["status"]]
    if "blocked" in statuses:
        overall = "BLOCKED"
        exit_code = 1
    elif "human_required" in statuses:
        overall = "HUMAN_REQUIRED"
        exit_code = 2
    else:
        overall = "READY"
        exit_code = 0

    report = {
        "generated_at": _utc_now(),
        "route": "ROUTE_A_STRICT_CLEAN_BASELINE",
        "overall": overall,
        "executed_external_runtime": False,
        "performed_mutation": False,
        "human_gate_required": overall == "HUMAN_REQUIRED",
        "source_repositories": repo_records,
        "target": target_record,
    }
    return exit_code, report


def _parse_repo(value: str) -> RepoSpec:
    if "=" not in value:
        raise argparse.ArgumentTypeError("--repo must use PROJECT_ID=PATH")
    project_id, raw_path = value.split("=", 1)
    project_id = project_id.strip()
    raw_path = raw_path.strip()
    if not project_id or not raw_path:
        raise argparse.ArgumentTypeError("--repo must use non-empty PROJECT_ID=PATH")
    return RepoSpec(project_id, Path(raw_path))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Read-only Route A preflight for devframe-system."
    )
    parser.add_argument(
        "--repo",
        action="append",
        type=_parse_repo,
        help="Repository to check as PROJECT_ID=PATH. Repeat to override defaults.",
    )
    parser.add_argument(
        "--target-path",
        default=str(DEFAULT_TARGET),
        help="Future devframe-system target path.",
    )
    parser.add_argument("--output", help="Optional path to write JSON report.")
    args = parser.parse_args()

    exit_code, report = evaluate_route_a_preflight(
        repos=args.repo,
        target_path=Path(args.target_path),
    )
    report_json = json.dumps(report, indent=2, ensure_ascii=False)
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(report_json + "\n", encoding="utf-8")
    print(report_json)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
