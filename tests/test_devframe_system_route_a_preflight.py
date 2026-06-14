"""Tests for the devframe-system Route A no-op preflight."""

import json
import subprocess
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))

from devframe_system_route_a_preflight import RepoSpec, evaluate_route_a_preflight


def _git(cwd: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(cwd), *args],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def _make_repo_with_upstream(tmp_path: Path, name: str) -> Path:
    repo = tmp_path / name
    repo.mkdir()
    _git(repo, "init")
    _git(repo, "config", "user.email", "route-a@example.invalid")
    _git(repo, "config", "user.name", "Route A Test")
    (repo / "README.md").write_text(f"# {name}\n", encoding="utf-8")
    _git(repo, "add", "README.md")
    _git(repo, "commit", "-m", "init")

    remote = tmp_path / f"{name}.git"
    subprocess.run(["git", "init", "--bare", str(remote)], check=True, capture_output=True)
    _git(repo, "remote", "add", "origin", str(remote))
    branch = _git(repo, "branch", "--show-current")
    _git(repo, "push", "-u", "origin", branch)
    return repo


def test_ready_when_all_repositories_are_clean_and_target_absent(tmp_path):
    repo_a = _make_repo_with_upstream(tmp_path, "repo-a")
    repo_b = _make_repo_with_upstream(tmp_path, "repo-b")

    exit_code, report = evaluate_route_a_preflight(
        repos=[RepoSpec("a", repo_a), RepoSpec("b", repo_b)],
        target_path=tmp_path / "missing-target",
    )

    assert exit_code == 0
    assert report["overall"] == "READY"
    assert report["executed_external_runtime"] is False
    assert report["performed_mutation"] is False
    assert all(
        repo_record["status"] == "passed"
        for repo_record in report["source_repositories"]
    )


def test_dirty_repository_requires_human_gate(tmp_path):
    repo = _make_repo_with_upstream(tmp_path, "dirty-repo")
    (repo / "README.md").write_text("# dirty\n", encoding="utf-8")

    exit_code, report = evaluate_route_a_preflight(
        repos=[RepoSpec("dirty", repo)],
        target_path=tmp_path / "missing-target",
    )

    assert exit_code == 2
    assert report["overall"] == "HUMAN_REQUIRED"
    repo_record = report["source_repositories"][0]
    assert repo_record["status"] == "human_required"
    assert repo_record["dirty"]["tracked_dirty"] == 1
    assert repo_record["dirty"]["staged"] == 0
    assert repo_record["dirty"]["unstaged"] == 1
    assert repo_record["sample_status"] == [" M README.md"]


def test_untracked_repository_file_requires_human_gate(tmp_path):
    repo = _make_repo_with_upstream(tmp_path, "untracked-repo")
    (repo / "scratch.txt").write_text("scratch\n", encoding="utf-8")

    exit_code, report = evaluate_route_a_preflight(
        repos=[RepoSpec("untracked", repo)],
        target_path=tmp_path / "missing-target",
    )

    assert exit_code == 2
    assert report["overall"] == "HUMAN_REQUIRED"
    repo_record = report["source_repositories"][0]
    assert repo_record["dirty"]["untracked"] == 1
    assert repo_record["sample_status"] == ["?? scratch.txt"]


def test_head_mismatch_with_upstream_requires_human_gate(tmp_path):
    repo = _make_repo_with_upstream(tmp_path, "ahead-repo")
    (repo / "new.txt").write_text("new\n", encoding="utf-8")
    _git(repo, "add", "new.txt")
    _git(repo, "commit", "-m", "local ahead")

    exit_code, report = evaluate_route_a_preflight(
        repos=[RepoSpec("ahead", repo)],
        target_path=tmp_path / "missing-target",
    )

    assert exit_code == 2
    assert report["overall"] == "HUMAN_REQUIRED"
    repo_record = report["source_repositories"][0]
    assert repo_record["status"] == "human_required"
    assert repo_record["detail"] == "HEAD does not match upstream head"


def test_missing_repository_blocks(tmp_path):
    exit_code, report = evaluate_route_a_preflight(
        repos=[RepoSpec("missing", tmp_path / "missing")],
        target_path=tmp_path / "missing-target",
    )

    assert exit_code == 1
    assert report["overall"] == "BLOCKED"
    assert report["source_repositories"][0]["detail"] == "repository path does not exist"


def test_existing_target_requires_human_gate(tmp_path):
    repo = _make_repo_with_upstream(tmp_path, "ready-repo")
    target = tmp_path / "devframe-system"
    target.mkdir()

    exit_code, report = evaluate_route_a_preflight(
        repos=[RepoSpec("ready", repo)],
        target_path=target,
    )

    assert exit_code == 2
    assert report["overall"] == "HUMAN_REQUIRED"
    assert report["target"]["status"] == "human_required"
    assert "already exists" in report["target"]["detail"]


def test_cli_writes_json_report(tmp_path):
    repo = _make_repo_with_upstream(tmp_path, "cli-repo")
    output = tmp_path / "report.json"

    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPTS / "devframe_system_route_a_preflight.py"),
            "--repo",
            f"cli={repo}",
            "--target-path",
            str(tmp_path / "missing-target"),
            "--output",
            str(output),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    stdout_report = json.loads(result.stdout)
    file_report = json.loads(output.read_text(encoding="utf-8"))
    assert stdout_report == file_report
    assert file_report["overall"] == "READY"
    assert file_report["executed_external_runtime"] is False
