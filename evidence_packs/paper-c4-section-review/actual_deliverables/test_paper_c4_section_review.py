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

    def test_all_forbidden_fields_blocked(self):
        for field in paper_c4_section_packet_validator.FORBIDDEN_FIELDS:
            v = paper_c4_section_packet_validator.validate(_input({field: "content"}))
            assert not v["valid"], f"{field} must be blocked"

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


class TestResultSchema:
    def test_result_has_required_fields(self):
        r = paper_c4_section_review.review("examples/paper_c4_section_review/SECTION_REVIEW_INPUT.synthetic.yaml")
        for f in ["task_id","input_privacy_mode","safety_status","review_allowed","target_section_name"]:
            assert f in r, f"missing: {f}"
        assert isinstance(r["revision_priorities"], list)
        assert isinstance(r["citation_or_evidence_needs"], list)
