"""Test ai_guard with real git fixtures: staged-only commit, full-tree audit, fail-closed."""
import os
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
AI_GUARD = REPO_ROOT / "tools" / "ai_guard.py"


def make_git_repo(tmpdir):
    """Create a minimal git repo with .ai/policy.yaml and return its path."""
    r = Path(tmpdir) / "repo"
    r.mkdir()
    subprocess.run(["git", "init", str(r)], capture_output=True, check=True)
    subprocess.run(["git", "-C", str(r), "config", "user.email", "test@test"], capture_output=True)
    subprocess.run(["git", "-C", str(r), "config", "user.name", "Test"], capture_output=True)
    # Create minimal policy
    ai_dir = r / ".ai"
    ai_dir.mkdir()
    (ai_dir / "policy.yaml").write_text("deny_paths: []\nrestricted_paths: []\nsecret_patterns: []\n", encoding="utf-8")
    # Initial commit so HEAD exists
    (r / "README.md").write_text("# test\n")
    subprocess.run(["git", "-C", str(r), "add", "README.md"], capture_output=True)
    subprocess.run(["git", "-C", str(r), "commit", "-m", "init"], capture_output=True)
    return r


def run_guard_in(repo, *args):
    """Run ai_guard in the given repo (passes --root for correct policy lookup)."""
    result = subprocess.run(
        [sys.executable, str(AI_GUARD), "--root", str(repo)] + list(args),
        capture_output=True, text=True, cwd=str(repo),
    )
    return result.returncode, result.stdout


class TestTaskModeStagedOnly:
    """Task mode must scan ONLY staged files — no full working tree."""

    def test_unstaged_forbidden_does_not_block_clean_staged_commit(self):
        """Unstaged file with forbidden marker must NOT block a clean staged commit."""
        d = tempfile.mkdtemp()
        try:
            repo = make_git_repo(d)
            # Create a clean file and stage it
            (repo / "good.txt").write_text("clean content")
            subprocess.run(["git", "-C", str(repo), "add", "good.txt"], capture_output=True)
            # Create a dirty file with a secret but do NOT stage it
            (repo / "dirty.txt").write_text("api_key=sk-deadbeef1234567890")
            # Create a task spec allowing good.txt
            tasks_dir = repo / ".ai" / "tasks"
            tasks_dir.mkdir(parents=True)
            (tasks_dir / "test.yaml").write_text(
                "task_id: test\nwrite_set:\n  - good.txt\n", encoding="utf-8")
            # Run task mode
            code, out = run_guard_in(repo, "task", str(tasks_dir / "test.yaml"))
            # Must not flag the unstaged dirty.txt
            assert "dirty.txt" not in out or "SCOPE" not in out, (
                f"Task mode flagged unstaged file: {out}")
            # Must pass (no staged violations)
            assert code == 0, f"Expected pass, got exit={code}: {out}"
        finally:
            subprocess.run(["rm", "-rf", d])

    def test_staged_forbidden_marker_fails_closed(self):
        """Staged file with forbidden content must BLOCK."""
        d = tempfile.mkdtemp()
        try:
            repo = make_git_repo(d)
            # Override policy with deny_paths
            (repo / ".ai" / "policy.yaml").write_text(
                "deny_paths:\n  - '*.secret'\nrestricted_paths: []\nsecret_patterns:\n  - 'sk-[a-zA-Z0-9]{10,}'\n",
                encoding="utf-8")
            # Create a forbidden file and STAGE it
            (repo / "evil.secret").write_text("sk-badsecret123456")
            subprocess.run(["git", "-C", str(repo), "add", "evil.secret"], capture_output=True)
            tasks_dir = repo / ".ai" / "tasks"
            tasks_dir.mkdir(parents=True)
            (tasks_dir / "test.yaml").write_text("task_id: test\nwrite_set:\n  - evil.secret\n", encoding="utf-8")
            code, out = run_guard_in(repo, "task", str(tasks_dir / "test.yaml"))
            assert code != 0, f"Staged forbidden file must fail closed. Got exit={code}"
            assert "BLOCKED" in out or "error" in out.lower(), f"Must block: {out}"
        finally:
            subprocess.run(["rm", "-rf", d])

    def test_task_mode_ignores_unstaged_secret(self):
        """Task mode must NOT scan unstaged files for secrets."""
        d = tempfile.mkdtemp()
        try:
            repo = make_git_repo(d)
            (repo / ".ai" / "policy.yaml").write_text(
                "deny_paths: []\nrestricted_paths: []\nsecret_patterns:\n  - 'sk-[a-zA-Z0-9]{10,}'\n",
                encoding="utf-8")
            (repo / "good.txt").write_text("clean")
            subprocess.run(["git", "-C", str(repo), "add", "good.txt"], capture_output=True)
            # Unstaged secret file
            (repo / "leak.txt").write_text("sk-mysecretkey123456")
            tasks_dir = repo / ".ai" / "tasks"
            tasks_dir.mkdir(parents=True)
            (tasks_dir / "test.yaml").write_text("task_id: test\nwrite_set:\n  - good.txt\n", encoding="utf-8")
            code, out = run_guard_in(repo, "task", str(tasks_dir / "test.yaml"))
            assert code == 0, f"Unstaged secret must not block in task mode. Got: {out}"
        finally:
            subprocess.run(["rm", "-rf", d])


class TestAuditModeFull:
    """Audit mode must scan entire working tree."""

    def test_audit_mode_scans_working_tree_secrets(self):
        """Audit mode must detect secrets in modified tracked files (uses git diff base)."""
        d = tempfile.mkdtemp()
        try:
            repo = make_git_repo(d)
            (repo / ".ai" / "policy.yaml").write_text(
                "deny_paths: []\nrestricted_paths: []\nsecret_patterns:\n  - 'sk-[a-zA-Z0-9]{10,}'\n",
                encoding="utf-8")
            # Create a tracked file and commit it
            (repo / "leak.txt").write_text("clean baseline")
            subprocess.run(["git", "-C", str(repo), "add", "leak.txt"], capture_output=True)
            subprocess.run(["git", "-C", str(repo), "commit", "-m", "baseline"], capture_output=True)
            # Modify the tracked file with a secret (unstaged modification)
            (repo / "leak.txt").write_text("sk-mysecretkey123456")
            code, out = run_guard_in(repo, "audit")
            # Audit mode uses git diff, which catches unstaged modifications to tracked files
            assert code != 0 or "SECRET" in out, (
                f"Audit must flag modified tracked secret. Got exit={code}: {out[:500]}")
        finally:
            subprocess.run(["rm", "-rf", d])


class TestFailClosed:
    """Guard must stay fail-closed."""

    def test_guard_has_blocked_exit(self):
        code = AI_GUARD.read_text(encoding="utf-8")
        assert "sys.exit(1)" in code

    def test_guard_has_staged_mode(self):
        code = AI_GUARD.read_text(encoding="utf-8")
        assert '"staged"' in code or "'staged'" in code

    def test_guard_has_audit_mode(self):
        code = AI_GUARD.read_text(encoding="utf-8")
        assert '"audit"' in code or "'audit'" in code
