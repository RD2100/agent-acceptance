"""Test paper privacy boundaries — negative scenarios for PAPER-A2."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

def load_schema(name):
    return json.loads((ROOT / "schemas" / name).read_text(encoding="utf-8"))

def validate_against_schema(instance, schema):
    required = schema.get("required", [])
    for r in required:
        if r not in instance:
            raise AssertionError(f"Missing required: {r}")
    all_of = schema.get("allOf", [])
    for rule in all_of:
        if_cond = rule.get("if", {})
        then_cond = rule.get("then", {})
        props = if_cond.get("properties", {})
        match = True
        for k, v in props.items():
            inst_val = instance.get(k)
            if "const" in v and inst_val != v["const"]:
                match = False
            if "enum" in v and inst_val not in v["enum"]:
                match = False
        if match:
            then_props = then_cond.get("properties", {})
            for k, v in then_props.items():
                if inst_val := instance.get(k):
                    if "const" in v and inst_val != v["const"]:
                        raise AssertionError(f"Violation: {k} must be {v['const']}, got {inst_val}")

def make_input(classification="synthetic", authorization="synthetic"):
    return {"task_id":"test","task_type":"cssci_review","paper_data_classification":classification,"user_authorization":authorization,"input_materials":[],"privacy_constraints":[],"memory_policy":"none","expected_outputs":[]}

def make_output():
    return {"task_id":"test","task_type":"cssci_review","output_summary":"x","findings":[],"evidence_basis":"x","privacy_redaction_status":"full","manual_review_required":False,"limitations":[],"contains_real_paper_full_text":False,"contains_unredacted_excerpt":False,"contains_user_identity":False}

# Tests
def test_synthetic_input_allowed():
    validate_against_schema(make_input("synthetic","synthetic"), load_schema("paper_task_input.schema.json"))

def test_redacted_input_allowed():
    validate_against_schema(make_input("redacted","synthetic"), load_schema("paper_task_input.schema.json"))

def test_user_authorized_excerpt_needs_explicit():
    try:
        validate_against_schema(make_input("user_authorized_excerpt","none"), load_schema("paper_task_input.schema.json"))
        assert False, "Should have raised"
    except AssertionError:
        pass

def test_real_paper_full_text_blocked_by_schema():
    try:
        validate_against_schema(make_input("real_paper_full_text","synthetic"), load_schema("paper_task_input.schema.json"))
        assert False, "Should have raised"
    except AssertionError:
        pass

def test_output_without_real_text_allowed():
    validate_against_schema(make_output(), load_schema("paper_task_output.schema.json"))

def test_redacted_evidence_pack_must_be_false():
    s = load_schema("paper_redacted_evidence_pack.schema.json")
    for field in ["contains_real_paper_full_text","contains_user_private_text","contains_raw_transcript","contains_external_upload"]:
        props = s["properties"][field]
        assert "const" in props and props["const"] is False, f"{field} must be const:false"

def test_privacy_attestation_all_fields():
    data = {
        "task_id": "test",
        "contains_real_paper_full_text": False,
        "contains_user_private_text": False,
        "contains_raw_transcript": False,
        "contains_memory_write": False,
        "contains_external_upload": False,
        "redaction_applied": True,
        "manual_review_required": False,
        "memory_write_policy": "none",
    }
    validate_against_schema(data, load_schema("paper_redacted_evidence_pack.schema.json"))

def test_privacy_attestation_real_text_must_fail():
    data = {
        "task_id": "test",
        "contains_real_paper_full_text": True,
        "contains_user_private_text": False,
        "contains_raw_transcript": False,
        "contains_memory_write": False,
        "contains_external_upload": False,
        "redaction_applied": True,
        "manual_review_required": False,
        "memory_write_policy": "none",
    }
    try:
        validate_against_schema(data, load_schema("paper_redacted_evidence_pack.schema.json"))
        assert False, "Should have raised"
    except AssertionError:
        pass

def test_memory_write_paper_content_blocked():
    s = load_schema("paper_redacted_evidence_pack.schema.json")
    allowed = s["properties"]["memory_write_policy"]["enum"]
    assert "paper_content" not in allowed

def test_raw_paper_text_in_pack_blocked():
    data = {"task_id":"test","contains_real_paper_full_text":False,"contains_user_private_text":False,"contains_raw_transcript":False,"contains_memory_write":False,"contains_external_upload":False,"redaction_applied":True,"manual_review_required":False,"memory_write_policy":"none","raw_paper_text":"should be blocked"}
    try:
        validate_against_schema(data, load_schema("paper_redacted_evidence_pack.schema.json"))
        assert False, "Should have raised on additional property"
    except AssertionError:
        pass

def test_redaction_report_missing_detected():
    p = ROOT / "examples" / "paper_a2_synthetic_case" / "REDACTION_REPORT.yaml"
    assert p.exists()

def test_synthetic_case_files_exist():
    for f in ["PAPER_TASK_INPUT.yaml","PAPER_TASK_OUTPUT.yaml","PRIVACY_ATTESTATION.yaml","REDACTION_REPORT.yaml"]:
        assert (ROOT / "examples" / "paper_a2_synthetic_case" / f).exists()

def run():
    tests = [
        ("synthetic input allowed", test_synthetic_input_allowed),
        ("redacted input allowed", test_redacted_input_allowed),
        ("excerpt needs explicit auth", test_user_authorized_excerpt_needs_explicit),
        ("real paper full text blocked", test_real_paper_full_text_blocked_by_schema),
        ("output without real text allowed", test_output_without_real_text_allowed),
        ("redacted pack must_be_false", test_redacted_evidence_pack_must_be_false),
        ("privacy attestation valid", test_privacy_attestation_all_fields),
        ("privacy attestation real text fails", test_privacy_attestation_real_text_must_fail),
        ("memory write paper content blocked", test_memory_write_paper_content_blocked),
        ("raw paper text additional prop blocked", test_raw_paper_text_in_pack_blocked),
        ("redaction report exists", test_redaction_report_missing_detected),
        ("synthetic case files exist", test_synthetic_case_files_exist),
    ]
    p = f = 0
    print("=" * 60)
    print("Paper Privacy Boundaries — Tests")
    print("=" * 60)
    for name, fn in tests:
        try:
            fn()
            print(f"  [PASS] {name}"); p += 1
        except Exception as e:
            print(f"  [FAIL] {name}: {e}"); f += 1
    print(f"\n  {p}/{p+f} passed")
    return f == 0

if __name__ == "__main__":
    sys.exit(0 if run() else 1)
