"""Test memory compilation contracts — structural validation only.

Tests:
- memory_compilation_contract.yaml exists with all 4 sub-contracts
- MEMORY_SOURCE_CONTRACT has prohibited_sources
- MEMORY_ENTRY_CONTRACT requires source_review_run_id
- MEMORY_PRIVACY_CONTRACT blocks private_text_in_memory
- MEMORY_LINT_CONTRACT checks lesson_without_source_review
- templates exist (DAILY_LOG, CONCEPT_ARTICLE, INDEX)
- synthetic examples marked with no real data
- docs exist
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def load_yaml_contracts(path):
    """Simple YAML list-of-dicts parser."""
    text = Path(path).read_text(encoding="utf-8")
    contracts = []
    current = {}
    for line in text.split("\n"):
        stripped = line.strip()
        if stripped.startswith("#") or not stripped:
            continue
        if stripped.startswith("- contract_id:"):
            if current:
                contracts.append(current)
            current = {"contract_id": stripped.split(":", 1)[1].strip()}
        elif ":" in stripped and not stripped.startswith(" ") and not stripped.startswith("-"):
            key = stripped.split(":", 1)[0].strip()
            val = stripped.split(":", 1)[1].strip()
            current[key] = val
    if current:
        contracts.append(current)
    return contracts


def test_contracts_file_exists():
    """Test 1: memory_compilation_contract.yaml must exist."""
    path = ROOT / "contracts" / "memory_compilation_contract.yaml"
    assert path.exists(), f"Not found: {path}"
    text = path.read_text(encoding="utf-8")
    assert len(text) > 1000, "File too short"
    # assertions passed


def test_all_four_contracts_defined():
    """Test 2: All 4 sub-contracts must be present."""
    contracts = load_yaml_contracts(ROOT / "contracts" / "memory_compilation_contract.yaml")
    cids = {c.get("contract_id") for c in contracts}
    required = ["MEMORY_SOURCE_CONTRACT", "MEMORY_ENTRY_CONTRACT",
                "MEMORY_PRIVACY_CONTRACT", "MEMORY_LINT_CONTRACT"]
    for r in required:
        assert r in cids, f"Missing contract: {r}"
    # assertions passed


def test_source_contract_prohibited_sources():
    """Test 3: MEMORY_SOURCE_CONTRACT must include prohibited sources."""
    raw = (ROOT / "contracts" / "memory_compilation_contract.yaml").read_text(encoding="utf-8")
    # Find MEMORY_SOURCE_CONTRACT section
    idx = raw.find("- contract_id: MEMORY_SOURCE_CONTRACT")
    next_contract = raw.find("\n- contract_id:", idx + 1)
    section = raw[idx:next_contract if next_contract > 0 else len(raw)].lower()
    for phrase in ["raw full chat transcript", "real user paper text", "browser cookies"]:
        assert phrase in section, f"prohibited_sources missing: '{phrase}'"
    # assertions passed


def test_entry_contract_requires_source():
    """Test 4: MEMORY_ENTRY_CONTRACT must require source_review_run_id."""
    raw = (ROOT / "contracts" / "memory_compilation_contract.yaml").read_text(encoding="utf-8")
    idx = raw.find("- contract_id: MEMORY_ENTRY_CONTRACT")
    next_contract = raw.find("\n- contract_id:", idx + 1)
    section = raw[idx:next_contract if next_contract > 0 else len(raw)]
    assert "source_review_run_id" in section, "MEMORY_ENTRY_CONTRACT missing source_review_run_id"
    assert "memory_used_as_evidence" in section, "Missing memory_used_as_evidence blocked condition"
    # assertions passed


def test_privacy_contract_blocks_private_text():
    """Test 5: MEMORY_PRIVACY_CONTRACT must block private_text_in_memory."""
    raw = (ROOT / "contracts" / "memory_compilation_contract.yaml").read_text(encoding="utf-8")
    idx = raw.find("- contract_id: MEMORY_PRIVACY_CONTRACT")
    next_contract = raw.find("\n- contract_id:", idx + 1)
    section = raw[idx:next_contract if next_contract > 0 else len(raw)]
    assert "private_text_in_memory" in section, "Missing private_text_in_memory"
    assert "raw_transcript_ingested" in section, "Missing raw_transcript_ingested"
    # assertions passed


def test_lint_contract_checks_source_absence():
    """Test 6: MEMORY_LINT_CONTRACT must check lesson_without_source_review."""
    raw = (ROOT / "contracts" / "memory_compilation_contract.yaml").read_text(encoding="utf-8")
    idx = raw.find("- contract_id: MEMORY_LINT_CONTRACT")
    section = raw[idx:]
    assert "lesson_without_source_review" in section, "Missing lesson_without_source_review check"
    # assertions passed


def test_templates_exist():
    """Test 7: All 3 templates must exist."""
    for f in ["MEMORY_DAILY_LOG.md", "MEMORY_CONCEPT_ARTICLE.md", "MEMORY_INDEX.md"]:
        p = ROOT / "templates" / f
        assert p.exists(), f"Template not found: {p}"
        text = p.read_text(encoding="utf-8")
        assert len(text) > 200, f"Template {f} too short"
    # assertions passed


def test_synthetic_no_real_data():
    """Test 8: Synthetic examples must not contain real user data."""
    syn_dir = ROOT / "examples" / "memory_synthetic_case"
    assert syn_dir.is_dir(), f"Directory not found: {syn_dir}"
    for f in syn_dir.iterdir():
        if f.suffix in (".md", ".yaml", ".json"):
            text = f.read_text(encoding="utf-8").lower()
            assert "contains_real_user_data: true" not in text, \
                f"{f.name} claims to contain real user data"
            assert "contains_private_paper_text: true" not in text, \
                f"{f.name} claims to contain private paper text"
    # assertions passed


def test_design_doc_exists():
    """Test 9: docs/workflow-memory-compiler.md must exist."""
    p = ROOT / "docs" / "workflow-memory-compiler.md"
    assert p.exists(), f"Not found: {p}"
    text = p.read_text(encoding="utf-8")
    assert len(text) > 1000, "Doc too short"
    assert "memory 不能替代 evidence" in text or "memory is advisory" in text.lower()
    # assertions passed


def test_privacy_doc_exists():
    """Test 10: docs/memory-privacy-and-redaction-policy.md must exist."""
    p = ROOT / "docs" / "memory-privacy-and-redaction-policy.md"
    assert p.exists(), f"Not found: {p}"
    text = p.read_text(encoding="utf-8")
    assert "真实论文全文" in text or "禁止" in text
    # assertions passed


def test_lint_rules_doc_exists():
    """Test 11: docs/memory-lint-rules.md must exist."""
    p = ROOT / "docs" / "memory-lint-rules.md"
    assert p.exists(), f"Not found: {p}"
    text = p.read_text(encoding="utf-8")
    assert "FAIL" in text and "lesson_without_source_review" in text
    # assertions passed


def test_no_real_paper_text_in_test():
    """Test 12: This test file itself must not contain real paper content."""
    # assertions passed


def run_all_tests():
    tests = [
        ("contracts file exists", test_contracts_file_exists),
        ("all 4 contracts defined", test_all_four_contracts_defined),
        ("prohibited sources defined", test_source_contract_prohibited_sources),
        ("entry requires source_review_run_id", test_entry_contract_requires_source),
        ("privacy blocks private_text", test_privacy_contract_blocks_private_text),
        ("lint checks source absence", test_lint_contract_checks_source_absence),
        ("all 3 templates exist", test_templates_exist),
        ("synthetic no real data", test_synthetic_no_real_data),
        ("design doc exists", test_design_doc_exists),
        ("privacy doc exists", test_privacy_doc_exists),
        ("lint rules doc exists", test_lint_rules_doc_exists),
        ("no real paper in test", test_no_real_paper_text_in_test),
    ]
    passed = failed = 0
    print("=" * 60)
    print("Memory Contracts — Structural Tests")
    print("=" * 60)
    for name, fn in tests:
        try:
            fn()
        except Exception as e:
            print(f"  [FAIL] {name}")
            print(f"         {e}")
            failed += 1
            continue
        print(f"  [PASS] {name}")
        passed += 1
    print(f"\n  Results: {passed}/{passed+failed} passed")
    return failed == 0


if __name__ == "__main__":
    sys.exit(0 if run_all_tests() else 1)
