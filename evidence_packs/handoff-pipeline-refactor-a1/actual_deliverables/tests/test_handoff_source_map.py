import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from handoff_source_map import build_source_map


def test_source_map_outputs_claim_bindings_with_priority(tmp_path):
    source = tmp_path / "_reports/PAPER_PROJECT_INDEX.json"
    source.parent.mkdir(parents=True)
    source.write_text('{"overall_status":"in_progress"}', encoding="utf-8")

    result = build_source_map(
        repo_root=tmp_path,
        claims=[{
            "claim_id": "paper_status",
            "claim": "Paper workflow is active in bounded, local, privacy-gated mode.",
            "source_layer": "P0",
            "source_path": "_reports/PAPER_PROJECT_INDEX.json"
        }]
    )

    assert result["source_priority"][0]["layer"] == "P0"
    assert result["claims"][0]["source_layer"] == "P0"
    assert result["claims"][0]["sha256"]
    assert result["claims"][0]["bound"] is True


def test_source_map_marks_missing_source_unbound(tmp_path):
    result = build_source_map(
        repo_root=tmp_path,
        claims=[{
            "claim_id": "missing",
            "claim": "Missing claim",
            "source_layer": "P0",
            "source_path": "missing.txt"
        }]
    )

    assert result["claims"][0]["bound"] is False
    assert result["claims"][0]["sha256"] is None
