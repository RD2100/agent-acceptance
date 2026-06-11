import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from handoff_compiler import compile_handoff_draft


def test_compiler_generates_draft_and_paste_block_from_synthetic_view(tmp_path):
    reports = tmp_path / "_reports/handoff-pipeline-refactor-a1"
    result = compile_handoff_draft(
        repo_root=tmp_path,
        output_dir=reports,
        project_view={
            "paper_status": "active_bounded_privacy_gated",
            "current_task": "HANDOFF-PIPELINE-REFACTOR-A1",
            "next_tasks": ["Submit evidence pack to GPT review"],
        },
    )

    draft = Path(result["draft_path"])
    paste = Path(result["paste_block_path"])
    assert draft.exists()
    assert paste.exists()
    assert result["approval_status"] == "draft_only"
    assert "P0" in draft.read_text(encoding="utf-8")
    assert "approved" not in result["approval_status"].replace("draft_only", "")


def test_compiler_preserves_accepted_with_limitation_and_human_required(tmp_path):
    reports = tmp_path / "_reports/handoff-pipeline-refactor-a1"
    result = compile_handoff_draft(
        repo_root=tmp_path,
        output_dir=reports,
        project_view={
            "closed_modules": [{"id": "M3", "verdict": "accepted_with_limitation"}],
            "human_required_modules": [{"id": "M9", "status": "human_required"}],
        },
    )
    text = Path(result["draft_path"]).read_text(encoding="utf-8")

    assert "accepted_with_limitation" in text
    assert "human_required" in text
    assert "M9" in text
    assert "resolved" not in text


def test_compiler_blocks_raw_paper_text_fields(tmp_path):
    reports = tmp_path / "_reports/handoff-pipeline-refactor-a1"
    result = compile_handoff_draft(
        repo_root=tmp_path,
        output_dir=reports,
        project_view={"raw_paper_text": "ACTUAL PAPER CONTENT"},
    )

    assert result["safety_pass"] is False
    assert not Path(result["draft_path"]).exists()


def test_minimax_m3_observation_schema_covers_required_dimensions():
    schema_path = Path(__file__).parent.parent / "schemas/minimax_m3_observation.schema.json"
    schema = __import__("json").loads(schema_path.read_text(encoding="utf-8"))
    required_dimensions = schema["properties"]["dimensions"]["required"]

    assert required_dimensions == [
        "Evidence-First",
        "Stale identification",
        "Safety boundary",
        "Task planning",
        "Repair quality",
        "Loop control",
        "Command discipline",
        "Honesty",
    ]
