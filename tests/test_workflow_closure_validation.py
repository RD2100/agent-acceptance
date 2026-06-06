"""Test enhanced workflow closure validation — SD-01/02/03 R2 coverage."""

import sys
import zipfile
import tempfile
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from scripts.validate_workflow_closure import validate_evidence_pack


def make_zip(files: dict) -> Path:
    tmp = Path(tempfile.gettempdir()) / f"test_{hash(str(files))}.zip"
    tmp.unlink(missing_ok=True)
    with zipfile.ZipFile(str(tmp), "w", zipfile.ZIP_DEFLATED) as zf:
        for name, content in files.items():
            zf.writestr(name, content)
    return tmp


def test_sd01_summary_only_fails():
    zp = make_zip({
        "GPT_REVIEW_PROMPT.md": "x", "CLOSURE_REPORT.md": "x",
        "SAFETY_ATTESTATION.md": "x", "PACK_MANIFEST.md": "| path | role | sha256 |\n|---|---|---|\n",
    })
    result = validate_evidence_pack(str(zp))
    assert result["summary_only_pack"]
    assert result["result"] == "fail"
    zp.unlink()


def test_sd01_deliverables_passes():
    h = hashlib.sha256(b"c").hexdigest()
    m = f"| path | role | sha256 |\n|---|---|---|\n| contracts/test.yaml | c | {h} |\n| PACK_MANIFEST.md | m | self |\n"
    zp = make_zip({"PACK_MANIFEST.md": m, "contracts/test.yaml": "c"})
    result = validate_evidence_pack(str(zp))
    assert not result["summary_only_pack"]
    assert result["result"] == "pass"
    zp.unlink()


def test_sd01_hash_mismatch_fails():
    m = "| path | role | sha256 |\n|---|---|---|\n| contracts/test.yaml | c | deadbeef |\n| PACK_MANIFEST.md | m | self |\n"
    zp = make_zip({"PACK_MANIFEST.md": m, "contracts/test.yaml": "actual content"})
    result = validate_evidence_pack(str(zp))
    assert not result["hashes_verified"]
    assert result["result"] == "fail"
    zp.unlink()


def test_sd02_closed_without_gpt_review_fails():
    m = "| path | role | sha256 |\n|---|---|---|\n| contracts/test.yaml | c | abc |\n| CLOSURE_REPORT.md | r | ghi |\n| PACK_MANIFEST.md | m | self |\n"
    zp = make_zip({"PACK_MANIFEST.md": m, "contracts/test.yaml": "c",
        "CLOSURE_REPORT.md": "final_status: closed\ntask_status: executed"})
    result = validate_evidence_pack(str(zp))
    assert any("closed" in i.lower() and "gpt" in i.lower() for i in result["blocking_issues"])
    zp.unlink()


def test_sd02_ready_as_closed_fails():
    m = "| path | role | sha256 |\n|---|---|---|\n| contracts/test.yaml | c | abc |\n| CLOSURE_REPORT.md | r | ghi |\n| PACK_MANIFEST.md | m | self |\n"
    zp = make_zip({"PACK_MANIFEST.md": m, "contracts/test.yaml": "c",
        "CLOSURE_REPORT.md": "task_status: ready_for_review\nfinal_status: closed"})
    result = validate_evidence_pack(str(zp))
    assert any("ready_for_review" in i.lower() and "closed" in i.lower() for i in result["blocking_issues"])
    zp.unlink()


def test_sd02_closed_without_ledger_fails():
    m = "| path | role | sha256 |\n|---|---|---|\n| contracts/test.yaml | c | abc |\n| CLOSURE_REPORT.md | r | ghi |\n| PACK_MANIFEST.md | m | self |\n"
    zp = make_zip({"PACK_MANIFEST.md": m, "contracts/test.yaml": "c",
        "CLOSURE_REPORT.md": "final_status: closed\ngpt_review_result: accepted"})
    result = validate_evidence_pack(str(zp))
    assert any("ledger" in i.lower() for i in result["blocking_issues"])
    zp.unlink()


def test_sd03_governance_self_close_fails():
    m = "| path | role | sha256 |\n|---|---|---|\n| contracts/test.yaml | c | abc |\n| CLOSURE_REPORT.md | r | ghi |\n| PACK_MANIFEST.md | m | self |\n"
    zp = make_zip({"PACK_MANIFEST.md": m, "contracts/test.yaml": "c",
        "CLOSURE_REPORT.md": "final_status: closed\ntask_status: executed"})
    result = validate_evidence_pack(str(zp))
    assert any("governance" in i.lower() and "self" in i.lower() for i in result["blocking_issues"])
    zp.unlink()


def test_sd03_retroactive_missing_prior_fails():
    m = "| path | role | sha256 |\n|---|---|---|\n| contracts/test.yaml | c | abc |\n| CLOSURE_REPORT.md | r | ghi |\n| PACK_MANIFEST.md | m | self |\n"
    zp = make_zip({"PACK_MANIFEST.md": m, "contracts/test.yaml": "c",
        "CLOSURE_REPORT.md": "retroactive_review: true\ncorrected_status: accepted"})
    result = validate_evidence_pack(str(zp))
    assert any("prior_status" in i.lower() for i in result["blocking_issues"])
    zp.unlink()


def test_sd03_retroactive_missing_corrected_fails():
    m = f"| path | role | sha256 |\n|---|---|---|\n| contracts/test.yaml | c | {hashlib.sha256(b'c').hexdigest()} |\n| CLOSURE_REPORT.md | r | {hashlib.sha256(b'r').hexdigest()} |\n| PACK_MANIFEST.md | m | self |\n"
    zp = make_zip({"PACK_MANIFEST.md": m, "contracts/test.yaml": "c",
        "CLOSURE_REPORT.md": "retroactive_review: true\nprior_status: ready_for_review\nreason_for_retroactive_review: was never submitted"})
    result = validate_evidence_pack(str(zp))
    assert any("corrected_status" in i.lower() for i in result["blocking_issues"])
    zp.unlink()


def test_sd03_retroactive_missing_reason_fails():
    m = f"| path | role | sha256 |\n|---|---|---|\n| contracts/test.yaml | c | {hashlib.sha256(b'c').hexdigest()} |\n| CLOSURE_REPORT.md | r | {hashlib.sha256(b'r').hexdigest()} |\n| PACK_MANIFEST.md | m | self |\n"
    zp = make_zip({"PACK_MANIFEST.md": m, "contracts/test.yaml": "c",
        "CLOSURE_REPORT.md": "retroactive_review: true\nprior_status: ready_for_review\ncorrected_status: accepted"})
    result = validate_evidence_pack(str(zp))
    assert any("reason_for_retroactive" in i.lower() for i in result["blocking_issues"])
    zp.unlink()


def test_sd02_gpt_review_wrong_reviewer_fails():
    """SD-02: GPT_REVIEW_RESULT with reviewer_type=agent must fail."""
    hc = hashlib.sha256(b'c').hexdigest(); hr = hashlib.sha256(b'GRF').hexdigest()
    m = f"| path | role | sha256 |\n|---|---|---|\n| contracts/test.yaml | c | {hc} |\n| GPT_REVIEW_RESULT.yaml | g | {hr} |\n| CLOSURE_REPORT.md | r | {hashlib.sha256(b'r').hexdigest()} |\n| PACK_MANIFEST.md | m | self |\n"
    zp = make_zip({"PACK_MANIFEST.md": m, "contracts/test.yaml": "c",
        "GPT_REVIEW_RESULT.yaml": "overall_judgment: accepted\nreviewer_type: agent",
        "CLOSURE_REPORT.md": "final_status: closed"})
    result = validate_evidence_pack(str(zp))
    assert any("invalid" in i.lower() or "无效" in i.lower() or "reviewer" in i.lower() for i in result["blocking_issues"])
    zp.unlink()


def test_sd02_empty_ledger_fails():
    """SD-02: empty WORKFLOW_AUDIT_LEDGER must fail."""
    hc = hashlib.sha256(b'c').hexdigest(); hg = hashlib.sha256(b'GRF-accepted').hexdigest()
    m = f"| path | role | sha256 |\n|---|---|---|\n| contracts/test.yaml | c | {hc} |\n| GPT_REVIEW_RESULT.yaml | g | {hg} |\n| WORKFLOW_AUDIT_LEDGER.yaml | l | {hashlib.sha256(b'ledger').hexdigest()} |\n| CLOSURE_REPORT.md | r | {hashlib.sha256(b'r').hexdigest()} |\n| PACK_MANIFEST.md | m | self |\n"
    zp = make_zip({"PACK_MANIFEST.md": m, "contracts/test.yaml": "c",
        "GPT_REVIEW_RESULT.yaml": "overall_judgment: accepted\nreviewer_type: gpt\nREVIEW_RUN_ID: test-001",
        "WORKFLOW_AUDIT_LEDGER.yaml": "# empty ledger",
        "CLOSURE_REPORT.md": "final_status: closed"})
    result = validate_evidence_pack(str(zp))
    assert any("ledger" in i.lower() and ("无" in i or "invalid" in i.lower() or "无效" in i.lower() or "内容" in i.lower()) for i in result["blocking_issues"])
    zp.unlink()


def test_manifest_zip_mismatch_fails():
    m = "| path | role | sha256 |\n|---|---|---|\n| contracts/test.yaml | c | abc |\n| docs/missing.md | d | xyz |\n| PACK_MANIFEST.md | m | self |\n"
    zp = make_zip({"PACK_MANIFEST.md": m, "contracts/test.yaml": "c"})
    result = validate_evidence_pack(str(zp))
    assert not result["manifest_valid"]
    zp.unlink()


def run_all_tests():
    tests = [
        ("SD-01 summary-only fails", test_sd01_summary_only_fails),
        ("SD-01 deliverables passes", test_sd01_deliverables_passes),
        ("SD-01 hash mismatch fails", test_sd01_hash_mismatch_fails),
        ("SD-02 closed without GPT review fails", test_sd02_closed_without_gpt_review_fails),
        ("SD-02 ready as closed fails", test_sd02_ready_as_closed_fails),
        ("SD-02 closed without ledger fails", test_sd02_closed_without_ledger_fails),
        ("SD-03 governance self-close fails", test_sd03_governance_self_close_fails),
        ("SD-03 retroactive missing prior fails", test_sd03_retroactive_missing_prior_fails),
        ("SD-03 retroactive missing corrected fails", test_sd03_retroactive_missing_corrected_fails),
        ("SD-03 retroactive missing reason fails", test_sd03_retroactive_missing_reason_fails),
        ("SD-02 GPT review wrong reviewer fails", test_sd02_gpt_review_wrong_reviewer_fails),
        ("SD-02 empty ledger fails", test_sd02_empty_ledger_fails),
        ("manifest ZIP mismatch fails", test_manifest_zip_mismatch_fails),
    ]
    passed = failed = 0
    print("=" * 60)
    print("Workflow Closure Validation R2 — Tests")
    print("=" * 60)
    for name, fn in tests:
        try:
            fn()
            print(f"  [PASS] {name}")
            passed += 1
        except Exception as e:
            print(f"  [FAIL] {name}: {e}")
            failed += 1
    print(f"\n  Results: {passed}/{passed+failed} passed")
    return failed == 0


if __name__ == "__main__":
    sys.exit(0 if run_all_tests() else 1)
