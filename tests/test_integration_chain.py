"""Integration tests for the full verification chain."""
import subprocess, sys, json
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

def run_script(name):
    r = subprocess.run([sys.executable, f"scripts/{name}.py"], capture_output=True, text=True, cwd=str(REPO), timeout=120)
    return r.returncode

class TestVerificationChain:
    def test_smoke_suite_importable(self):
        sys.path.insert(0, str(REPO / "scripts"))
        import smoke_suite
        assert hasattr(smoke_suite, "main")

    def test_pre_push_verify_importable(self):
        sys.path.insert(0, str(REPO / "scripts"))
        import pre_push_verify
        assert hasattr(pre_push_verify, "main")

    def test_run_demo_importable(self):
        sys.path.insert(0, str(REPO / "scripts"))
        import run_demo
        assert hasattr(run_demo, "main")

    def test_paper_pilot_preflight_passes(self):
        assert run_script("paper_pilot_preflight") == 0

    def test_paper_go_nogo_runs(self):
        r = subprocess.run([sys.executable, "scripts/paper_go_nogo.py"], capture_output=True, text=True, cwd=str(REPO))
        assert r.returncode in (0, 1)  # may be GO or NOGO depending on auth state

    def test_paper_auth_gate_runs(self):
        r = subprocess.run([sys.executable, "scripts/paper_auth_gate.py"], capture_output=True, text=True, cwd=str(REPO))
        assert r.returncode in (0, 1)  # may pass or block depending on auth state

    def test_task_validator_all_pass(self):
        assert run_script("validate_taskspec") == 0
