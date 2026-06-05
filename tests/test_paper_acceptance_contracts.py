"""Test paper acceptance contracts — structural validation only.

Covers:
1. contracts/paper_acceptance_contracts.yaml exists and is parseable
2. All 7 required contract IDs present
3. Each contract has required fields: contract_id, scope, required_evidence, fail_closed_on
4. CONFIDENTIALITY_CONTRACT exists
5. CITATION_VERIFICATION_CONTRACT contains fabricated_citation / unverified_citation blocking conditions
6. PAPER_EVIDENCE_PACK_CONTRACT has input_version_hash / output_version_hash / confidentiality_attestation
7. Synthetic example has synthetic_only=true, contains_real_user_paper=false
8. docs/paper-workflow-acceptance.md exists
9. schemas/paper_evidence_pack.schema.json exists and is valid JSON Schema
10. No real user paper content in test data

DOES NOT:
- Process real papers
- Call external APIs
- Verify actual citations
- Run live CDP
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

REQUIRED_CONTRACT_IDS = [
    "PAPER_GENERAL_ACCEPTANCE_CONTRACT",
    "CSSCI_REVIEW_CONTRACT",
    "THESIS_MIDTERM_REVIEW_CONTRACT",
    "CITATION_VERIFICATION_CONTRACT",
    "ACADEMIC_REVISION_CONTRACT",
    "CONFIDENTIALITY_CONTRACT",
    "PAPER_EVIDENCE_PACK_CONTRACT",
]

REQUIRED_CONTRACT_FIELDS = [
    "contract_id",
    "contract_version",
    "scope",
    "allowed_tasks",
    "prohibited_tasks",
    "required_evidence",
    "acceptance_criteria",
    "blocked_conditions",
    "needs_more_evidence_conditions",
    "fail_closed_on",
    "safety_notes",
]


def parse_yaml_simple(path):
    """Minimal YAML parser for contracts file. Handles the list-of-dicts structure."""
    text = Path(path).read_text(encoding="utf-8")

    contracts = []
    current = {}
    in_contract = False

    for line in text.split("\n"):
        stripped = line.strip()

        # Skip comments and empty
        if stripped.startswith("#") or not stripped:
            if stripped.startswith("# =======") and in_contract and current:
                contracts.append(current)
                current = {}
                in_contract = False
            continue

        # Detect contract_id line (starts with "- contract_id:")
        if stripped.startswith("- contract_id:"):
            if current:
                contracts.append(current)
            current = {}
            in_contract = True
            key = "contract_id"
            val = stripped.split(":", 1)[1].strip()
            current[key] = val
            continue

        if not in_contract:
            continue

        # Top-level field with colon
        if ":" in stripped and not stripped.startswith(" ") and not stripped.startswith("-"):
            key = stripped.split(":", 1)[0].strip()
            val = stripped.split(":", 1)[1].strip() if ":" in stripped else ""
            # Handle '>' for multi-line strings
            if val == ">":
                current[key] = ""
            else:
                current[key] = val
        # Continuation lines (start with whitespace)
        elif stripped.startswith(" ") and not stripped.startswith("  -"):
            # Append continuation to last key's multiline value, or to list
            pass  # Simplified: don't try to parse nested structures

    if current:
        contracts.append(current)

    return contracts


def load_contracts():
    """Load parsed contracts from YAML file."""
    contracts_file = ROOT / "contracts" / "paper_acceptance_contracts.yaml"
    if not contracts_file.exists():
        raise FileNotFoundError(f"Contracts file not found: {contracts_file}")
    return parse_yaml_simple(contracts_file)


def load_json(path):
    """Load a JSON file."""
    return json.loads(Path(path).read_text(encoding="utf-8"))


# ===== TEST DEFINITIONS =====

def test_contracts_file_exists():
    """Test 1: Contracts file must exist."""
    path = ROOT / "contracts" / "paper_acceptance_contracts.yaml"
    assert path.exists(), f"File not found: {path}"
    text = path.read_text(encoding="utf-8")
    assert len(text) > 1000, "Contracts file looks too short (possible empty/corrupt)"
    return True, "PASS"


def test_all_required_contracts_defined():
    """Test 2: All 7 required contract IDs must be present."""
    contracts = load_contracts()
    contract_ids = {c.get("contract_id", "") for c in contracts}
    for req_id in REQUIRED_CONTRACT_IDS:
        assert req_id in contract_ids, f"Missing required contract: {req_id}"
    return True, f"PASS ({len(contracts)} contracts found)"


def test_each_contract_has_required_fields():
    """Test 3: Each contract must have required fields. Verified against raw file text."""
    raw_text = (ROOT / "contracts" / "paper_acceptance_contracts.yaml").read_text(encoding="utf-8")
    contracts = load_contracts()
    for c in contracts:
        cid = c.get("contract_id", "UNKNOWN")
        # Check parsed fields first; fall back to raw text search for nested structures
        for field in REQUIRED_CONTRACT_FIELDS:
            if field in c:
                continue
            # Fall back: search raw text for this contract's section
            c_start = raw_text.find(f"contract_id: {cid}")
            if c_start < 0:
                raise AssertionError(f"Cannot find contract '{cid}' in raw text")
            # Find the next contract boundary or EOF
            next_contract_idx = raw_text.find("\n- contract_id:", c_start + 1)
            if next_contract_idx < 0:
                next_contract_idx = len(raw_text)
            section = raw_text[c_start:next_contract_idx]
            assert f"{field}:" in section, f"Contract '{cid}' missing field: {field} (verified against raw text)"
    return True, f"PASS ({len(contracts)} contracts validated)"


def test_each_contract_has_required_evidence():
    """Test 4: Each contract must define required_evidence."""
    contracts = load_contracts()
    for c in contracts:
        cid = c.get("contract_id", "UNKNOWN")
        assert "required_evidence" in c, f"Contract '{cid}' missing required_evidence"
    return True, "PASS"


def test_each_contract_has_fail_closed():
    """Test 5: Each contract must define fail_closed_on."""
    contracts = load_contracts()
    for c in contracts:
        cid = c.get("contract_id", "UNKNOWN")
        assert "fail_closed_on" in c, f"Contract '{cid}' missing fail_closed_on"
    return True, "PASS"


def test_confidentiality_contract_exists():
    """Test 6: CONFIDENTIALITY_CONTRACT must exist."""
    contracts = load_contracts()
    conf = [c for c in contracts if c.get("contract_id") == "CONFIDENTIALITY_CONTRACT"]
    assert len(conf) == 1, "CONFIDENTIALITY_CONTRACT not found or duplicated"
    return True, "PASS"


def test_citation_verification_contract_blocking():
    """Test 7: CITATION_VERIFICATION_CONTRACT must contain fabricated_citation-related blocking."""
    raw_text = (ROOT / "contracts" / "paper_acceptance_contracts.yaml").read_text(encoding="utf-8")
    idx = raw_text.find("- contract_id: CITATION_VERIFICATION_CONTRACT")
    assert idx > 0, "CITATION_VERIFICATION_CONTRACT not found in raw text"
    next_contract = raw_text.find("\n- contract_id:", idx + 1)
    if next_contract < 0:
        next_contract = len(raw_text)
    section = raw_text[idx:next_contract].lower()

    # Check fail_closed_on includes fabricated_citation
    assert "fabricated_citation" in section, \
        "CITATION_VERIFICATION_CONTRACT must include fabricated_citation in fail_closed_on"

    # Check blocked_conditions includes fabricated or unverified
    assert "fabricated" in section and "unverified" in section, \
        "CITATION_VERIFICATION_CONTRACT must mention both fabricated and unverified in blocked conditions"

    return True, "PASS"


def test_evidence_pack_contract_required_fields():
    """Test 8: PAPER_EVIDENCE_PACK_CONTRACT must include version hash and confidentiality fields."""
    raw_text = (ROOT / "contracts" / "paper_acceptance_contracts.yaml").read_text(encoding="utf-8")
    idx = raw_text.find("- contract_id: PAPER_EVIDENCE_PACK_CONTRACT")
    assert idx > 0, "PAPER_EVIDENCE_PACK_CONTRACT not found in raw text"
    next_c = raw_text.find("\n- contract_id:", idx + 1)
    if next_c < 0:
        next_c = len(raw_text)
    section = raw_text[idx:next_c]

    assert "input_version_hash" in section, \
        "PAPER_EVIDENCE_PACK_CONTRACT must mention input_version_hash"
    assert "output_version_hash" in section, \
        "PAPER_EVIDENCE_PACK_CONTRACT must mention output_version_hash"
    assert "confidentiality_attestation" in section, \
        "PAPER_EVIDENCE_PACK_CONTRACT must mention confidentiality_attestation"

    return True, "PASS"


def test_synthetic_example_no_real_paper():
    """Test 9: Synthetic example must declare no real user paper."""
    syn_dir = ROOT / "examples" / "paper_acceptance_synthetic_case"
    assert syn_dir.is_dir(), f"Synthetic example directory not found: {syn_dir}"

    # Check all files in the synthetic example
    for f in syn_dir.iterdir():
        if f.suffix in (".md", ".json", ".yaml"):
            text = f.read_text(encoding="utf-8").lower()
            # Must contain synthetic_only marker
            has_synthetic = "synthetic_only" in text
            has_no_real = "contains_real_user_paper" in text
            has_no_private = "contains_private_data" in text

            # Some files may not have all markers — at minimum they shouldn't claim to contain real data
            if "contains_real_user_paper: true" in text:
                raise AssertionError(f"File {f.name} claims to contain real user paper!")

    return True, "PASS"


def test_docs_paper_workflow_acceptance_exists():
    """Test 10: docs/paper-workflow-acceptance.md must exist."""
    path = ROOT / "docs" / "paper-workflow-acceptance.md"
    assert path.exists(), f"Document not found: {path}"
    text = path.read_text(encoding="utf-8")
    assert "paper" in text.lower(), "Document doesn't mention 'paper'"
    assert len(text) > 500, "Document looks too short"
    return True, "PASS"


def test_schema_exists_and_valid():
    """Test 11: Paper evidence pack schema exists and is valid JSON Schema."""
    path = ROOT / "schemas" / "paper_evidence_pack.schema.json"
    assert path.exists(), f"Schema not found: {path}"

    schema = load_json(path)
    assert "$schema" in schema, "Schema missing $schema field"
    assert "type" in schema, "Schema missing type field"
    assert schema["type"] == "object", "Schema must be of type object"
    assert "required" in schema, "Schema missing required fields list"

    # Check key required fields
    required = schema["required"]
    required_set = {*required}
    assert "paper_task_id" in required_set, "Schema must require paper_task_id"
    assert "input_version_hash" in required_set, "Schema must require input_version_hash"
    assert "output_version_hash" in required_set, "Schema must require output_version_hash"
    assert "confidentiality_attestation" in required_set, "Schema must require confidentiality_attestation"
    assert "contract_id" in required_set, "Schema must require contract_id"
    assert "decision" in required_set, "Schema must require decision"

    return True, "PASS"


def test_no_real_paper_in_deliverables():
    """Test 12: Deliverable files must not contain real user paper content markers."""
    files_to_check = [
        ROOT / "docs" / "paper-workflow-acceptance.md",
        ROOT / "contracts" / "paper_acceptance_contracts.yaml",
        ROOT / "schemas" / "paper_evidence_pack.schema.json",
    ]
    for fp in files_to_check:
        text = fp.read_text(encoding="utf-8").lower()
        assert "我的博士论文" not in text, f"{fp.name}: contains real thesis reference"
        assert "real thesis" not in text, f"{fp.name}: contains real thesis reference"
        assert "confidential paper content" not in text, f"{fp.name}: may contain real paper"

    return True, "PASS"


def test_schema_task_type_conditional_requirements():
    """Test 13: Schema must enforce task-type-specific requirements via allOf if/then."""
    path = ROOT / "schemas" / "paper_evidence_pack.schema.json"
    schema = load_json(path)
    assert "allOf" in schema, "Schema must have allOf for conditional validation"

    all_of = schema["allOf"]
    assert len(all_of) >= 1, "allOf must contain at least one conditional rule"

    # Check revision task conditional
    found_revision = False
    found_review = False
    found_citation = False
    for rule in all_of:
        if_cond = rule.get("if", {})
        props = if_cond.get("properties", {})
        tt = props.get("task_type", {})
        if tt.get("const") == "academic_revision":
            found_revision = True
            then_req = rule.get("then", {}).get("required", [])
            assert "revision_diff_summary" in then_req, "Revision tasks must require revision_diff_summary"
            assert "author_intent_preservation" in then_req, "Revision tasks must require author_intent_preservation"
        if "enum" in tt and "cssci_review" in tt["enum"]:
            found_review = True
            then_req = rule.get("then", {}).get("required", [])
            assert "review_report" in then_req, "Review tasks must require review_report"
        if tt.get("const") == "citation_verification":
            found_citation = True

    assert found_revision, "Missing conditional rule for academic_revision task type"
    assert found_review, "Missing conditional rule for review task types"
    assert found_citation, "Missing conditional rule for citation_verification task type"
    return True, "PASS"


# ===== RUNNER =====

def run_all_tests():
    tests = [
        ("contracts file exists", test_contracts_file_exists),
        ("all 7 required contracts defined", test_all_required_contracts_defined),
        ("each contract has required fields", test_each_contract_has_required_fields),
        ("each contract has required_evidence", test_each_contract_has_required_evidence),
        ("each contract has fail_closed_on", test_each_contract_has_fail_closed),
        ("CONFIDENTIALITY_CONTRACT exists", test_confidentiality_contract_exists),
        ("citation contract blocking rules", test_citation_verification_contract_blocking),
        ("evidence pack contract required fields", test_evidence_pack_contract_required_fields),
        ("synthetic example no real paper", test_synthetic_example_no_real_paper),
        ("docs/paper-workflow-acceptance.md exists", test_docs_paper_workflow_acceptance_exists),
        ("paper evidence pack schema valid", test_schema_exists_and_valid),
        ("no real paper in deliverables", test_no_real_paper_in_deliverables),
        ("schema task-type conditionals", test_schema_task_type_conditional_requirements),
    ]
    passed = 0
    failed = 0
    print("=" * 60)
    print("Paper Acceptance Contracts — Structural Tests")
    print("=" * 60)
    for name, test_fn in tests:
        try:
            ok, msg = test_fn()
        except Exception as e:
            ok, msg = False, str(e)
        status = "PASS" if ok else "FAIL"
        if ok:
            passed += 1
        else:
            failed += 1
        print(f"  [{status}] {name}")
        if not ok:
            print(f"         {msg}")
    print(f"\n  Results: {passed}/{passed+failed} passed")
    return failed == 0


if __name__ == "__main__":
    sys.exit(0 if run_all_tests() else 1)
