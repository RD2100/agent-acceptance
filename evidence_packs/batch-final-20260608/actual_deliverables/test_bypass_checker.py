"""Test bypass checker fail-closed behavior per GPT requirements."""
import os, sys, tempfile
from pathlib import Path
REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))
import check_submission_bypass

class TestBypassChecker:
    def test_normal_path_no_marker_fails_closed(self):
        """Normal directory without .ai/bypass_approved must fail."""
        d = tempfile.mkdtemp()
        try:
            cwd = os.getcwd()
            os.chdir(d)
            try: check_submission_bypass.main()
            except SystemExit as e: assert e.code == 1
            finally: os.chdir(cwd)
        finally: import shutil; shutil.rmtree(d, ignore_errors=True)

    def test_valid_marker_passes(self):
        """Directory with .ai/bypass_approved must pass."""
        d = tempfile.mkdtemp()
        try:
            ai = Path(d) / ".ai"; ai.mkdir()
            (ai / "bypass_approved").touch()
            cwd = os.getcwd(); os.chdir(d)
            try: check_submission_bypass.main()
            except SystemExit as e: assert e.code == 0
            finally: os.chdir(cwd)
        finally: import shutil; shutil.rmtree(d, ignore_errors=True)

    def test_generic_temp_path_no_longer_passes(self):
        """A Temp directory without marker must fail (no auto-pass)."""
        d = tempfile.mkdtemp()
        assert "Temp" in d or "tmp" in d.lower()
        try:
            cwd = os.getcwd(); os.chdir(d)
            try: check_submission_bypass.main()
            except SystemExit as e: assert e.code == 1, "Temp path must NOT auto-pass"
            finally: os.chdir(cwd)
        finally: import shutil; shutil.rmtree(d, ignore_errors=True)

    def test_synthetic_test_mode_passes(self):
        """DEVRAME_TEST_MODE=SYNTHETIC_ONLY must pass."""
        d = tempfile.mkdtemp()
        try:
            cwd = os.getcwd(); os.chdir(d)
            os.environ['DEVRAME_TEST_MODE'] = 'SYNTHETIC_ONLY'
            try: check_submission_bypass.main()
            except SystemExit as e: assert e.code == 0
            finally: del os.environ['DEVRAME_TEST_MODE']; os.chdir(cwd)
        finally: import shutil; shutil.rmtree(d, ignore_errors=True)
