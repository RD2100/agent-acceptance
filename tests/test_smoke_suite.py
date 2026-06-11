"""Test smoke suite structure and imports."""
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))

class TestSmokeSuite:
    def test_smoke_suite_importable(self):
        import smoke_suite
        assert hasattr(smoke_suite, "main")

    def test_smoke_check_count(self):
        import smoke_suite
        assert len(smoke_suite.RESULTS) >= 0  # results list exists

    def test_all_scripts_in_smoke_importable(self):
        scripts = [
            "pre_push_verify",
            "run_demo",
            "review_queue",
            "paper_pilot_preflight",
            "multi_agent_gate0_preflight",
        ]
        for s in scripts:
            mod = __import__(s)
            assert mod is not None

    def test_ci_matrix_importable(self):
        import ci_matrix
        assert hasattr(ci_matrix, "main")

    def test_test_impact_map_importable(self):
        import test_impact_map
        assert hasattr(test_impact_map, "recommend")

    def test_multi_repo_smoke_file_exists(self):
        assert (REPO / "scripts" / "multi_repo_smoke.py").exists()

    def test_external_runtime_presence_check_is_not_execution(self, tmp_path):
        import smoke_suite

        result = smoke_suite.external_runtime_presence_check("external_runtime", tmp_path)

        assert result["passed"] is True
        assert result["scope"] == "presence_only"
        assert result["executed"] is False
        assert result["human_gate_required_for_execution"] is True

    def test_pre_push_external_runtime_status_is_not_execution(self, tmp_path):
        import pre_push_verify

        result = pre_push_verify.external_runtime_presence_status(tmp_path)

        assert result["passed"] is True
        assert result["scope"] == "presence_only"
        assert result["executed"] is False
        assert result["human_gate_required_for_execution"] is True

    def test_run_demo_external_runtime_step_is_presence_only(self, tmp_path):
        import run_demo

        cmd = run_demo.external_runtime_presence_command(tmp_path)

        assert cmd[:2] == [sys.executable, "-c"]
        assert "scope=presence_only" in cmd[2]
        assert "executed=false" in cmd[2]
        assert "human_gate_required_for_execution=true" in cmd[2]
        assert repr(str(tmp_path)) in cmd[2]
