"""Test smoke suite structure and imports."""
import sys, json
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
        scripts = ["pre_push_verify", "run_demo", "review_queue", "paper_pilot_preflight"]
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
