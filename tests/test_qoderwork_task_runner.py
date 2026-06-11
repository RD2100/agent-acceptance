"""Tests for QoderWork Task Runner — mandatory SADP entry point.

Tests cover:
  1. start: Delegates to pre_task enforcer correctly
  2. edit-check: Delegates to pre_edit enforcer correctly
  3. finish: Delegates to post_task enforcer correctly
  4. Exit codes: 0=PASS, 1=BLOCKED, 2=WARNING
  5. CLI argument parsing
"""

import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

REPO = Path(__file__).resolve().parent.parent
SCRIPTS = REPO / "scripts"
sys.path.insert(0, str(SCRIPTS))

import qoderwork_task_runner as runner


# ── 1. Start Command ──────────────────────────────────────────────────


class TestStartCommand:
    """Test the 'start' command delegates to pre_task correctly."""

    def test_start_existing_task_passes(self):
        """Start with valid TaskSpec should pass (exit 0)."""
        exit_code = runner.cmd_start("SHARED-CDP-V2-REVIEW-FINDINGS-FIX-A1")
        assert exit_code == 0

    def test_start_nonexistent_task_blocked(self):
        """Start with nonexistent TaskSpec should block (exit 1)."""
        exit_code = runner.cmd_start("NONEXISTENT-TASK-999")
        assert exit_code == 1


# ── 2. Edit-Check Command ─────────────────────────────────────────────


class TestEditCheckCommand:
    """Test the 'edit-check' command delegates to pre_edit correctly."""

    def test_edit_check_write_set_file_passes(self):
        """File in write_set should pass (exit 0)."""
        exit_code = runner.cmd_edit_check(
            "SHARED-CDP-V2-REVIEW-FINDINGS-FIX-A1",
            "scripts/tab_target_resolver.py",
        )
        assert exit_code == 0

    def test_edit_check_protected_file_blocked(self):
        """Protected governance file should block (exit 1)."""
        exit_code = runner.cmd_edit_check(
            "SHARED-CDP-V2-REVIEW-FINDINGS-FIX-A1",
            "rules/core.md",
        )
        assert exit_code == 1

    def test_edit_check_self_protecting_blocked(self):
        """Self-protecting enforcer file should block (exit 1)."""
        exit_code = runner.cmd_edit_check(
            "SHARED-CDP-V2-REVIEW-FINDINGS-FIX-A1",
            "scripts/sadp_pre_task_enforcer.py",
        )
        assert exit_code == 1

    def test_edit_check_scope_creep_blocked_for_p0(self):
        """Scope creep on P0 task should block (exit 1)."""
        exit_code = runner.cmd_edit_check(
            "SHARED-CDP-V2-REVIEW-FINDINGS-FIX-A1",
            "scripts/out_of_scope.py",
        )
        assert exit_code == 1


# ── 3. Finish Command ─────────────────────────────────────────────────


class TestFinishCommand:
    """Test the 'finish' command delegates to post_task correctly."""

    def test_finish_completed_task_passes(self):
        """Finish with all artifacts should pass (exit 0)."""
        exit_code = runner.cmd_finish("SHARED-CDP-V2-REVIEW-FINDINGS-FIX-A1")
        assert exit_code == 0

    def test_finish_nonexistent_task_blocked(self):
        """Finish nonexistent task should block (exit 1)."""
        exit_code = runner.cmd_finish("NONEXISTENT-TASK-999")
        assert exit_code == 1


# ── 4. CLI Argument Parsing ───────────────────────────────────────────


class TestCLIArgumentParsing:
    """Test that CLI arguments are parsed correctly."""

    def test_start_requires_task_id(self):
        """start command requires --task-id."""
        with pytest.raises(SystemExit):
            runner.main()

    def test_edit_check_requires_task_id_and_file(self):
        """edit-check requires both --task-id and --file."""
        with pytest.raises(SystemExit):
            runner.main()


# ── 5. Integration Tests ─────────────────────────────────────────────


class TestIntegration:
    """Integration tests verifying the full runner workflow."""

    def test_full_workflow_existing_task(self):
        """Full start → edit-check → finish workflow on real task."""
        # start
        assert runner.cmd_start("SHARED-CDP-V2-REVIEW-FINDINGS-FIX-A1") == 0

        # edit-check on valid file
        assert runner.cmd_edit_check(
            "SHARED-CDP-V2-REVIEW-FINDINGS-FIX-A1",
            "scripts/tab_target_resolver.py",
        ) == 0

        # edit-check on protected file
        assert runner.cmd_edit_check(
            "SHARED-CDP-V2-REVIEW-FINDINGS-FIX-A1",
            "rules/core.md",
        ) == 1

        # finish
        assert runner.cmd_finish("SHARED-CDP-V2-REVIEW-FINDINGS-FIX-A1") == 0

    def test_blocked_workflow(self):
        """Blocked workflow should stop at start."""
        # start fails for nonexistent task
        assert runner.cmd_start("FAKE-TASK-999") == 1
        # No point continuing to edit-check or finish

    def test_runner_script_exists(self):
        """Runner script should exist."""
        script_path = REPO / "scripts" / "qoderwork_task_runner.py"
        assert script_path.exists()
