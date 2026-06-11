import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from handoff_safety_scan import scan_files


def test_handoff_safety_scan_passes_safe_draft(tmp_path):
    draft = tmp_path / "HANDOFF_DRAFT.md"
    draft.write_text("# Draft\nPaper workflow is active in bounded, local, privacy-gated mode.\n", encoding="utf-8")

    result = scan_files([draft])

    assert result["pass"] is True
    assert result["files_checked"] == 1
    assert result["issues"] == []


def test_handoff_safety_scan_blocks_raw_paper_text_payload(tmp_path):
    draft = tmp_path / "HANDOFF_DRAFT.md"
    draft.write_text("# Draft\nraw_paper_text: ACTUAL PAPER CONTENT\n", encoding="utf-8")

    result = scan_files([draft])

    assert result["pass"] is False
    assert result["issues"]
    assert result["issues"][0]["pattern"] == "raw_paper_text"
