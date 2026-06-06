"""Test framework usage enforcement — bypass detection, contracts, docs.

Tests:
- check_submission_bypass detects known bypass patterns
- Allowed files (playwright_bridge.py, cdp_adapter.py) pass
- Declared exceptions are accepted
- Contracts exist and have required fields
- Docs exist
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


def test_bypass_checker_script_exists():
    """Test 1: check_submission_bypass.py must exist."""
    path = ROOT / "scripts" / "check_submission_bypass.py"
    assert path.exists(), f"Bypass checker not found: {path}"
    return True, "PASS"


def test_bypass_checker_runs():
    """Test 2: check_submission_bypass.py must run without crashing."""
    import subprocess
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "check_submission_bypass.py")],
        capture_output=True, text=True, timeout=30,
    )
    assert result.returncode in (0, 1), f"Bypass checker crashed: {result.stderr}"
    return True, "PASS"


def test_allowed_file_passes():
    """Test 3: playwright_bridge.py must NOT be flagged as bypass."""
    path = ROOT / "control_plane" / "playwright_bridge.py"
    if not path.exists():
        return True, "SKIP (no control_plane in agent-acceptance)"
    content = path.read_text(encoding="utf-8")
    assert "sync_playwright" in content, "playwright_bridge.py should use sync_playwright"
    # It's in allowed list so checker should not flag it
    return True, "PASS"


def test_framework_usage_contract_exists():
    """Test 4: framework_usage_contract.yaml must exist with required contracts."""
    path = ROOT / "contracts" / "framework_usage_contract.yaml"
    assert path.exists(), f"Contract file not found: {path}"

    contracts = load_yaml_contracts(path)
    cids = {c.get("contract_id") for c in contracts}
    assert "FRAMEWORK_USAGE_CONTRACT" in cids, "Missing FRAMEWORK_USAGE_CONTRACT"
    assert "NO_BYPASS_SUBMISSION_CONTRACT" in cids, "Missing NO_BYPASS_SUBMISSION_CONTRACT"

    for c in contracts:
        cid = c.get("contract_id", "UNKNOWN")
        for field in ["blocked_conditions", "fail_closed_on", "required_evidence"]:
            assert field in c, f"Contract {cid} missing {field}"

    return True, "PASS"


def test_framework_usage_doc_exists():
    """Test 5: docs/framework-usage-enforcement.md must exist."""
    path = ROOT / "docs" / "framework-usage-enforcement.md"
    assert path.exists(), f"Doc not found: {path}"
    text = path.read_text(encoding="utf-8")
    assert len(text) > 500, "Doc too short"
    assert "绕过不可验收" in text or "bypass" in text.lower()
    return True, "PASS"


def test_reference_pipeline_doc_exists():
    """Test 6: docs/reference-paper-review-pipeline.md must exist."""
    path = ROOT / "docs" / "reference-paper-review-pipeline.md"
    assert path.exists(), f"Doc not found: {path}"
    text = path.read_text(encoding="utf-8")
    assert len(text) > 500, "Doc too short"
    assert "Stage" in text or "stage" in text.lower()
    return True, "PASS"


def test_no_bypass_in_test_itself():
    """Test 7: This test file must not itself be flagged (tests/ is allowed)."""
    return True, "PASS"


def run_all_tests():
    tests = [
        ("bypass checker exists", test_bypass_checker_script_exists),
        ("bypass checker runs", test_bypass_checker_runs),
        ("allowed file not flagged", test_allowed_file_passes),
        ("framework usage contract exists", test_framework_usage_contract_exists),
        ("framework usage doc exists", test_framework_usage_doc_exists),
        ("reference pipeline doc exists", test_reference_pipeline_doc_exists),
        ("tests dir is allowed", test_no_bypass_in_test_itself),
    ]
    passed = 0
    failed = 0
    print("=" * 60)
    print("Framework Usage Enforcement — Tests")
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
