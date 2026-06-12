"""Test ai_guard with real git fixtures: staged-only commit, full-tree audit, fail-closed."""
import os
import shutil
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
            shutil.rmtree(d, ignore_errors=True)

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
            shutil.rmtree(d, ignore_errors=True)

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
            shutil.rmtree(d, ignore_errors=True)


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
            shutil.rmtree(d, ignore_errors=True)


class TestFilesMode:
    """--files mode must scan only explicitly listed files."""

    def test_files_no_args_passes_zero_checked(self):
        """--files with no file arguments → PASS, 0 file(s) checked."""
        d = tempfile.mkdtemp()
        try:
            repo = make_git_repo(d)
            code, out = run_guard_in(repo, "--files")
            assert code == 0, f"Expected pass, got exit={code}: {out}"
            assert "0 file(s) checked" in out
        finally:
            shutil.rmtree(d, ignore_errors=True)

    def test_files_detects_secret_in_specified_file(self):
        """--files must detect secret pattern in the specified file."""
        d = tempfile.mkdtemp()
        try:
            repo = make_git_repo(d)
            (repo / ".ai" / "policy.yaml").write_text(
                "deny_paths: []\nrestricted_paths: []\n"
                "secret_patterns:\n  - 'sk-[a-zA-Z0-9]{10,}'\n",
                encoding="utf-8")
            (repo / "leak.txt").write_text("api_key=sk-deadbeef1234567890")
            code, out = run_guard_in(repo, "--files", "leak.txt")
            assert code != 0, f"Must block on secret. Got exit={code}: {out}"
            assert "SECRET" in out
        finally:
            shutil.rmtree(d, ignore_errors=True)

    def test_files_does_not_scan_unlisted_file(self):
        """--files must NOT scan files that are not in the argument list."""
        d = tempfile.mkdtemp()
        try:
            repo = make_git_repo(d)
            (repo / ".ai" / "policy.yaml").write_text(
                "deny_paths: []\nrestricted_paths: []\n"
                "secret_patterns:\n  - 'sk-[a-zA-Z0-9]{10,}'\n",
                encoding="utf-8")
            (repo / "clean.txt").write_text("nothing here")
            (repo / "leak.txt").write_text("sk-deadbeef1234567890")
            code, out = run_guard_in(repo, "--files", "clean.txt")
            assert code == 0, f"Must pass when only listing clean file. Got: {out}"
            assert "leak.txt" not in out
        finally:
            shutil.rmtree(d, ignore_errors=True)

    def test_files_deny_path_blocks(self):
        """--files must enforce deny_paths."""
        d = tempfile.mkdtemp()
        try:
            repo = make_git_repo(d)
            (repo / ".ai" / "policy.yaml").write_text(
                "deny_paths:\n  - '*.secret'\n"
                "restricted_paths: []\nsecret_patterns: []\n",
                encoding="utf-8")
            (repo / "evil.secret").write_text("data")
            code, out = run_guard_in(repo, "--files", "evil.secret")
            assert code != 0, f"deny_paths must block. Got exit={code}: {out}"
            assert "DENIED" in out
        finally:
            shutil.rmtree(d, ignore_errors=True)

    def test_files_restricted_path_warns(self):
        """--files must warn on restricted_paths but still pass."""
        d = tempfile.mkdtemp()
        try:
            repo = make_git_repo(d)
            (repo / ".ai" / "policy.yaml").write_text(
                "deny_paths: []\n"
                "restricted_paths:\n  - 'hooks/*'\n"
                "secret_patterns: []\n",
                encoding="utf-8")
            (repo / "hooks").mkdir()
            (repo / "hooks" / "my-hook.ps1").write_text("# hook")
            code, out = run_guard_in(repo, "--files", "hooks/my-hook.ps1")
            assert code == 0, f"Restricted should warn, not block. Got: {out}"
            assert "RESTRICTED" in out
        finally:
            shutil.rmtree(d, ignore_errors=True)

    def test_files_normalizes_backslash(self):
        """--files must normalize backslash paths to forward slash."""
        d = tempfile.mkdtemp()
        try:
            repo = make_git_repo(d)
            (repo / ".ai" / "policy.yaml").write_text(
                "deny_paths:\n  - 'secrets/*'\n"
                "restricted_paths: []\nsecret_patterns: []\n",
                encoding="utf-8")
            (repo / "secrets").mkdir()
            (repo / "secrets" / "key.txt").write_text("data")
            code, out = run_guard_in(repo, "--files", "secrets\\key.txt")
            assert code != 0, f"Backslash path must be normalized and caught. Got: {out}"
            assert "DENIED" in out
        finally:
            shutil.rmtree(d, ignore_errors=True)


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

    def test_no_silent_size_limit_in_scan_secrets(self):
        """scan_secrets must NOT silently skip files above a size threshold."""
        code = AI_GUARD.read_text(encoding="utf-8")
        assert "1_000_000" not in code, (
            "scan_secrets must not have a hardcoded file size limit; use streaming reads instead"
        )


class TestLargeFileSecretScan:
    """Large files (>1MB) must be scanned via streaming, not silently skipped."""

    def test_large_file_secret_at_end_detected(self):
        """Secret hidden at the end of a >1MB file must be detected."""
        d = tempfile.mkdtemp()
        try:
            repo = make_git_repo(d)
            (repo / ".ai" / "policy.yaml").write_text(
                "deny_paths: []\nrestricted_paths: []\n"
                "secret_patterns:\n  - 'sk-[a-zA-Z0-9]{10,}'\n",
                encoding="utf-8")
            # Build >1MB file with secret at the very end
            with open(str(repo / "big.log"), "w", encoding="utf-8") as fh:
                for i in range(25000):
                    fh.write(f"line_{i:05d}_padding_filler_nothing_here_xyz\n")
                fh.write("api_key=sk-deadbeef1234567890\n")
            assert (repo / "big.log").stat().st_size > 1_000_000
            code, out = run_guard_in(repo, "--files", "big.log")
            assert code != 0, f"Must detect secret in large file. Got exit={code}: {out[:500]}"
            assert "SECRET" in out
        finally:
            shutil.rmtree(d, ignore_errors=True)

    def test_large_file_without_secret_passes(self):
        """Large file without secrets must pass cleanly."""
        d = tempfile.mkdtemp()
        try:
            repo = make_git_repo(d)
            (repo / ".ai" / "policy.yaml").write_text(
                "deny_paths: []\nrestricted_paths: []\n"
                "secret_patterns:\n  - 'sk-[a-zA-Z0-9]{10,}'\n",
                encoding="utf-8")
            with open(str(repo / "big.log"), "w", encoding="utf-8") as fh:
                for i in range(25000):
                    fh.write(f"line_{i:05d}_safe_content_no_secrets_here_abc\n")
            assert (repo / "big.log").stat().st_size > 1_000_000
            code, out = run_guard_in(repo, "--files", "big.log")
            assert code == 0, f"Large clean file must pass. Got exit={code}: {out[:500]}"
        finally:
            shutil.rmtree(d, ignore_errors=True)


class TestAllowPathsOverride:
    """allow_paths in policy.yaml must override deny_paths for known false positives."""

    def test_deny_paths_blocks_secret_named_file(self):
        """File matching deny_paths without allow_paths override must be BLOCKED."""
        d = tempfile.mkdtemp()
        try:
            repo = make_git_repo(d)
            (repo / ".ai" / "policy.yaml").write_text(
                "deny_paths:\n  - '*secret*'\n  - '**/*secret*'\n"
                "restricted_paths: []\nsecret_patterns: []\n",
                encoding="utf-8")
            (repo / "secret-scan-output.txt").write_text("scan results")
            code, out = run_guard_in(repo, "--files", "secret-scan-output.txt")
            assert code == 1, f"Deny-listed file must block. Got exit={code}: {out[:500]}"
            assert "DENIED" in out
        finally:
            shutil.rmtree(d, ignore_errors=True)

    def test_allow_paths_overrides_deny_for_specific_path(self):
        """File matching deny_paths BUT covered by allow_paths must PASS."""
        d = tempfile.mkdtemp()
        try:
            repo = make_git_repo(d)
            (repo / ".ai" / "policy.yaml").write_text(
                "deny_paths:\n  - '**/*secret*'\n"
                "allow_paths:\n  - '_evidence/**/secret-scan-output.txt'\n"
                "restricted_paths: []\nsecret_patterns: []\n",
                encoding="utf-8")
            # Create file in allowed path
            ev_dir = repo / "_evidence" / "test-pack"
            ev_dir.mkdir(parents=True)
            (ev_dir / "secret-scan-output.txt").write_text("scan results")
            code, out = run_guard_in(
                repo, "--files", "_evidence/test-pack/secret-scan-output.txt")
            assert code == 0, f"allow_paths must override deny. Got exit={code}: {out[:500]}"
        finally:
            shutil.rmtree(d, ignore_errors=True)

    def test_allow_paths_does_not_override_for_unmatched_path(self):
        """File matching deny_paths but NOT in allow_paths scope must still BLOCK."""
        d = tempfile.mkdtemp()
        try:
            repo = make_git_repo(d)
            (repo / ".ai" / "policy.yaml").write_text(
                "deny_paths:\n  - '*secret*'\n  - '**/*secret*'\n"
                "allow_paths:\n  - '_evidence/**/secret-scan-output.txt'\n"
                "restricted_paths: []\nsecret_patterns: []\n",
                encoding="utf-8")
            # File outside allow_paths scope
            (repo / "random-secret-scan.txt").write_text("scan")
            code, out = run_guard_in(repo, "--files", "random-secret-scan.txt")
            assert code == 1, f"Out-of-scope file must still block. Got exit={code}: {out[:500]}"
        finally:
            shutil.rmtree(d, ignore_errors=True)


class TestFilesFromEnvVar:
    """--files with no args must read file list from AI_GUARD_FILE_LIST env var."""

    def test_files_mode_reads_from_env_var(self):
        """When --files has no positional args, AI_GUARD_FILE_LIST env var is used."""
        d = tempfile.mkdtemp()
        try:
            repo = make_git_repo(d)
            (repo / "clean.txt").write_text("no secrets")
            env = os.environ.copy()
            env["AI_GUARD_FILE_LIST"] = "clean.txt\n"
            result = subprocess.run(
                [sys.executable, str(AI_GUARD), "--root", str(repo), "--files"],
                capture_output=True, text=True, cwd=str(repo), env=env,
            )
            assert result.returncode == 0, (
                f"Env var file list must work. Got exit={result.returncode}: "
                f"{result.stdout[:500]}")
            assert "PASS" in result.stdout
        finally:
            shutil.rmtree(d, ignore_errors=True)

    def test_files_mode_env_var_blocks_denied_file(self):
        """Env var file list must still enforce deny_paths."""
        d = tempfile.mkdtemp()
        try:
            repo = make_git_repo(d)
            (repo / ".ai" / "policy.yaml").write_text(
                "deny_paths:\n  - '*secret*'\n  - '**/*secret*'\n"
                "restricted_paths: []\nsecret_patterns: []\n",
                encoding="utf-8")
            (repo / "secret-data.txt").write_text("sensitive")
            env = os.environ.copy()
            env["AI_GUARD_FILE_LIST"] = "secret-data.txt\n"
            result = subprocess.run(
                [sys.executable, str(AI_GUARD), "--root", str(repo), "--files"],
                capture_output=True, text=True, cwd=str(repo), env=env,
            )
            assert result.returncode == 1, (
                f"Env var must still enforce deny. Got exit={result.returncode}: "
                f"{result.stdout[:500]}")
        finally:
            shutil.rmtree(d, ignore_errors=True)
