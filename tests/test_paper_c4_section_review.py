"""Test bounded section review runner — positive and negative paths."""
import json, sys, tempfile, yaml
from pathlib import Path
REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))
import paper_c4_section_review, paper_c4_section_packet_validator

def _input(extras=None):
    d = {"task_id":"TEST","paper_project_type":"dissertation","target_section_name":"Methods","privacy_mode":"synthetic_only","argument_outline":"1) a\n2) b\n3) c","known_problems":"none"}
    if extras: d.update(extras)
    return d

class TestPositive:
    def test_synthetic_passes(self):
        r = paper_c4_section_review.review("examples/paper_c4_section_review/SECTION_REVIEW_INPUT.synthetic.yaml")
        assert r["review_allowed"]

    def test_sanitized_with_auth_passes(self):
        r = paper_c4_section_review.review("examples/paper_c4_section_review/SECTION_REVIEW_INPUT.sanitized.yaml")
        assert r["review_allowed"]

    def test_generates_diagnosis_and_priorities(self):
        r = paper_c4_section_review.review("examples/paper_c4_section_review/SECTION_REVIEW_INPUT.synthetic.yaml")
        assert len(r["diagnosis"]) > 10
        assert len(r["revision_priorities"]) >= 2

class TestNegative:
    def test_real_paper_full_text_blocked(self):
        v = paper_c4_section_packet_validator.validate(_input({"real_paper_full_text":"content"}))
        assert not v["valid"]

    def test_raw_paper_text_blocked(self):
        v = paper_c4_section_packet_validator.validate(_input({"raw_paper_text":"text"}))
        assert not v["valid"]

    def test_unknown_privacy_mode_blocked(self):
        v = paper_c4_section_packet_validator.validate(_input({"privacy_mode":"real_paper"}))
        assert not v["valid"]

    def test_sanitized_without_auth_blocked(self):
        v = paper_c4_section_packet_validator.validate(_input({"privacy_mode":"sanitized_section"}))
        assert not v["valid"]

    def test_missing_file_blocked(self):
        r = paper_c4_section_review.review("/nonexistent/input.yaml")
        assert not r["review_allowed"]
        assert r["safety_status"] == "BLOCKED"
