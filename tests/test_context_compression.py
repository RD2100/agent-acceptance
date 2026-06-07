"""Test context compression pipeline stages."""
import sys
import os
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
import compress_project_context as cc


class TestSegment:
    """Stage 1: Segment — split input by task_id boundaries."""

    def test_segment_project_history_produces_segments(self):
        """PROJECT_HISTORY.md should produce multiple segments."""
        ph_path = Path(__file__).parent.parent / "PROJECT_HISTORY.md"
        if not ph_path.exists():
            return  # skip if fixture not available
        segments = cc.segment_project_history(str(ph_path))
        assert len(segments) >= 2, f"Expected >= 2 segments, got {len(segments)}"
        task_ids = {s["task_id"] for s in segments}
        assert "GROUP-01" in task_ids or "PAPER-A1" in task_ids, f"No known task_id in {task_ids}"

    def test_segment_audit_ledger_produces_segments(self):
        """WORKFLOW_AUDIT_LEDGER.yaml should produce segments."""
        al_path = Path(__file__).parent.parent / "docs" / "WORKFLOW_AUDIT_LEDGER.yaml"
        if not al_path.exists():
            return
        segments = cc.segment_audit_ledger(str(al_path))
        assert len(segments) >= 1, f"Expected >= 1 segment, got {len(segments)}"


class TestClassify:
    """Stage 2: Classify — tag segments by content type."""

    def test_accepted_entry_tagged_decision(self):
        """Entry with 'overall_judgment: accepted' gets 'decision' tag."""
        seg = {"task_id": "TEST-01", "raw_text": "overall_judgment: accepted"}
        result = cc.classify(seg)
        assert "decision" in result["tags"]

    def test_blocked_entry_tagged_blocker(self):
        """Entry with 'blocked' gets 'blocker' tag."""
        seg = {"task_id": "TEST-02", "raw_text": "status: blocked by GPT"}
        result = cc.classify(seg)
        assert "blocker" in result["tags"]

    def test_superseded_entry_tagged_superseded(self):
        """Entry with 'superseded' gets 'superseded' tag."""
        seg = {"task_id": "TEST-03", "raw_text": "status: superseded by GROUP-02"}
        result = cc.classify(seg)
        assert "superseded" in result["tags"]

    def test_empty_entry_tagged_noise(self):
        """Entry with no recognizable content gets 'noise' tag."""
        seg = {"task_id": "TEST-04", "raw_text": "lorem ipsum dolor sit amet"}
        result = cc.classify(seg)
        assert "noise" in result["tags"]


class TestDeduplicate:
    """Stage 3: Deduplicate — merge same-task segments."""

    def test_same_task_id_merged(self):
        """Segments with same task_id are merged into one."""
        segments = [
            {"task_id": "TEST-01", "source": "a.txt", "raw_text": "first", "char_count": 5, "tags": ["decision"]},
            {"task_id": "TEST-01", "source": "b.txt", "raw_text": "second longer text", "char_count": 18, "tags": ["fix"]},
        ]
        result = cc.deduplicate(segments)
        assert len(result) == 1
        assert result[0]["task_id"] == "TEST-01"
        assert result[0]["source_count"] == 2

    def test_different_task_ids_kept_separate(self):
        """Segments with different task_ids are kept separate."""
        segments = [
            {"task_id": "TEST-01", "source": "a.txt", "raw_text": "a", "char_count": 1, "tags": ["decision"]},
            {"task_id": "TEST-02", "source": "b.txt", "raw_text": "b", "char_count": 1, "tags": ["blocker"]},
        ]
        result = cc.deduplicate(segments)
        assert len(result) == 2


class TestSupersede:
    """Stage 4: Supersede — collapse blocked→accepted chains."""

    def test_superseded_entry_keeps_summary(self):
        """Superseded entries are preserved with root cause + final fix."""
        entries = [{
            "task_id": "TEST-01",
            "tags": ["superseded"],
            "raw_text": "blocked: reason X. required_fixes: do Y. overall_judgment: accepted",
        }]
        result = cc.supersede(entries)
        assert len(result) == 1
        assert "ROOT_CAUSE" in result[0]["raw_text"] or "FINAL_FIX" in result[0]["raw_text"]


class TestPrivacyFilter:
    """Stage 5: Privacy filter — block forbidden content."""

    def test_safe_entry_passes(self):
        """Entry with only task metadata passes."""
        entries = [{"task_id": "TEST-01", "raw_text": "task_id: TEST, verdict: accepted"}]
        result = cc.privacy_filter(entries)
        assert len(result) == 1

    def test_raw_paper_entry_blocked(self):
        """Entry containing raw_paper_text is blocked."""
        entries = [{"task_id": "TEST-02", "raw_text": "This has raw_paper_text content"}]
        result = cc.privacy_filter(entries)
        assert len(result) == 0, f"Should block paper content, got {len(result)} entries"

    def test_private_user_text_blocked(self):
        """Entry containing private_user_text is blocked."""
        entries = [{"task_id": "TEST-03", "raw_text": "private_user_text was here"}]
        result = cc.privacy_filter(entries)
        assert len(result) == 0


class TestPipelineIntegration:
    """Full pipeline integration tests."""

    def test_pipeline_runs_with_temp_dir(self):
        """Pipeline should run and produce output files with temp dirs."""
        with tempfile.TemporaryDirectory() as tmp:
            task_dir = os.path.join(tmp, "memory", "tasks")
            know_dir = os.path.join(tmp, "memory", "knowledge")
            idx_path = os.path.join(tmp, "memory", "index.md")
            os.makedirs(task_dir, exist_ok=True)
            os.makedirs(know_dir, exist_ok=True)

            result = cc.run_pipeline(
                project_history=str(Path(__file__).parent.parent / "PROJECT_HISTORY.md"),
                audit_ledger=str(Path(__file__).parent.parent / "docs" / "WORKFLOW_AUDIT_LEDGER.yaml"),
                task_memory_dir=task_dir,
                knowledge_dir=know_dir,
                index_path=idx_path,
            )

            assert result["pipeline"] == "COMPLETE"
            assert result["segments_in"] > 0
            assert result["privacy_safe"] > 0
            assert os.path.exists(idx_path)
            assert len(os.listdir(task_dir)) > 0
