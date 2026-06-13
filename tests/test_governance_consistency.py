"""Governance Consistency Tests -- GOVERNANCE-READINESS-CONSOLIDATION-A1.

Validates that governance artifacts are internally consistent:
- Capability inventory passport counts match summary
- Verify matrix VM-004 reflects mode-based capability state
- Risk register RR-001 status matches passport data
- All 44 TaskSpecs have status values within the expanded schema enum
  (status-field parity only, NOT full JSON Schema validation)
- Minimum capability set requirements met for local governance mode
- No conflicting PASS/GAP claims across governance documents
"""

import json
import re
import sys
from pathlib import Path

import pytest
import yaml

REPO = Path(__file__).resolve().parent.parent
AI_DIR = REPO / ".ai"
TASKS_DIR = AI_DIR / "tasks"
DOCS_DIR = REPO / "docs" / "agent-runtime"
SCHEMAS_DIR = REPO / "schemas" / "agent-runtime"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _read_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _read_md(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _parse_passport_entries(inventory_md: str) -> list[dict]:
    """Extract passport fields from capability inventory markdown."""
    entries = []
    current = {}
    for line in inventory_md.split("\n"):
        if line.startswith("## ") and ". " in line:
            if current.get("id"):
                entries.append(current)
            m = re.match(r"## (\d+)\. (.+)", line)
            if m:
                current = {"id": f"CAP-{int(m.group(1)):03d}", "name": m.group(2).strip()}
            else:
                current = {}
        elif current:
            for field, key in [
                ("Passport verified_status", "status"),
                ("Passport usable_for_gate0", "usable_for_gate0"),
                ("Passport dependency_type", "dependency_type"),
            ]:
                if f"**{field}**:" in line:
                    val = line.split(f"**{field}**:", 1)[1].strip()
                    current[key] = val
    if current.get("id"):
        entries.append(current)
    return entries


# ---------------------------------------------------------------------------
# Test: Capability passport counts match summary
# ---------------------------------------------------------------------------


class TestCapabilityPassportConsistency:
    """Passport entries must match the summary table."""

    def _load_inventory(self):
        path = DOCS_DIR / "capability-inventory.md"
        return _read_md(path), _parse_passport_entries(_read_md(path))

    def test_passport_status_counts_match(self):
        md, entries = self._load_inventory()
        counts = {}
        for e in entries:
            s = e.get("status", "unknown")
            counts[s] = counts.get(s, 0) + 1

        # Extract summary table counts
        for line in md.split("\n"):
            if line.startswith("| verified |"):
                m = re.search(r"\| verified \| (\d+) \|", line)
                if m:
                    assert counts.get("verified", 0) == int(m.group(1)), (
                        f"Summary says verified={m.group(1)}, actual={counts.get('verified', 0)}"
                    )
            elif line.startswith("| degraded |"):
                m = re.search(r"\| degraded \| (\d+) \|", line)
                if m:
                    assert counts.get("degraded", 0) == int(m.group(1))
            elif line.startswith("| stale |"):
                m = re.search(r"\| stale \| (\d+) \|", line)
                if m:
                    assert counts.get("stale", 0) == int(m.group(1))
            elif line.startswith("| unknown |"):
                m = re.search(r"\| unknown \| (\d+) \|", line)
                if m:
                    assert counts.get("unknown", 0) == int(m.group(1))

    def test_no_verified_uninstalled_externals(self):
        """External deps that are NOT installed must not be verified.
        This is the RR-001 check: previously 8 external caps claimed verified
        but were not installed in codex runtime."""
        _, entries = self._load_inventory()
        for e in entries:
            if e.get("dependency_type") == "external_dependency":
                if e.get("status") == "verified":
                    # Only CAP-021 (codex-security, confirmed installed),
                    # CAP-029 (verified 2026-06-10), and CAP-030 (CDP Write Adapter,
                    # verified 2026-06-13) should be verified
                    assert e["id"] in ("CAP-021", "CAP-029", "CAP-030"), (
                        f"{e['id']} ({e['name']}) is external_dependency with verified "
                        f"status but not confirmed installed (RR-001)"
                    )


# ---------------------------------------------------------------------------
# Test: Verify matrix VM-004 matches capability state
# ---------------------------------------------------------------------------


class TestVerifyMatrixConsistency:
    """VM-004 verdict must reflect mode-based capability state."""

    def test_vm004_reflects_mode_based_result(self):
        vm = _read_yaml(AI_DIR / "verify-matrix.yaml")
        vm004 = None
        for item in vm["verifications"]:
            if item["id"] == "VM-004":
                vm004 = item
                break
        assert vm004 is not None, "VM-004 not found in verify-matrix.yaml"

        # VM-004 should be partial: local_governance PASS, controlled_pilot GAP
        assert vm004["result"] == "partial", (
            f"VM-004 result should be 'partial' (mode-based), got '{vm004['result']}'"
        )
        detail = vm004.get("result_detail", {})
        lg = detail.get("local_governance", {})
        assert lg.get("status") == "pass", "VM-004 local_governance should be pass"
        assert lg.get("passport_verified_in_set") == 12
        cp = detail.get("controlled_pilot", {})
        assert cp.get("status") == "gap", "VM-004 controlled_pilot should be gap"
        assert cp.get("passport_verified_in_set") == 13, (
            "Controlled pilot should have 13 passport-verified "
            "(12 Mode 1 + CAP-029; CAP-014 is degraded)"
        )
        assert cp.get("human_authorized") is False

    def test_vm004_references_rr001(self):
        vm = _read_yaml(AI_DIR / "verify-matrix.yaml")
        vm004 = next(v for v in vm["verifications"] if v["id"] == "VM-004")
        assert "RR-001" in vm004.get("evidence", ""), (
            "VM-004 evidence should reference RR-001"
        )


# ---------------------------------------------------------------------------
# Test: Risk register RR-001 consistency
# ---------------------------------------------------------------------------


class TestRiskRegisterConsistency:
    """RR-001 status must match actual passport correction state."""

    def test_rr001_is_mitigated(self):
        rr = _read_yaml(AI_DIR / "risk-register.yaml")
        rr001 = next(r for r in rr["risks"] if r["id"] == "RR-001")
        assert rr001["status"] == "mitigated", (
            f"RR-001 should be 'mitigated' (passport corrected), got '{rr001['status']}'"
        )

    def test_rr001_has_mitigation_date(self):
        rr = _read_yaml(AI_DIR / "risk-register.yaml")
        rr001 = next(r for r in rr["risks"] if r["id"] == "RR-001")
        assert "mitigated_at" in rr001, "RR-001 must have mitigated_at field"


# ---------------------------------------------------------------------------
# Test: TaskSpec schema parity
# ---------------------------------------------------------------------------


class TestTaskSpecSchemaParity:
    """All 44 TaskSpecs must have status values within the expanded schema enum.
    This checks status-field parity only, NOT full JSON Schema validation."""

    ALLOWED_STATUSES = [
        "draft", "ready", "in_progress", "completed", "closed",
        "deferred", "rejected", "accepted_with_limitation",
        "pending_human_decision",
    ]

    def test_schema_has_9_statuses(self):
        schema = json.loads(
            (SCHEMAS_DIR / "task-spec.schema.json").read_text(encoding="utf-8-sig")
        )
        enum_values = schema["properties"]["status"]["enum"]
        assert len(enum_values) == 9, (
            f"Schema status enum should have 9 values, got {len(enum_values)}: {enum_values}"
        )
        for s in self.ALLOWED_STATUSES:
            assert s in enum_values, f"Schema missing status: {s}"

    def test_all_taskspecs_have_valid_status(self):
        schema = json.loads(
            (SCHEMAS_DIR / "task-spec.schema.json").read_text(encoding="utf-8-sig")
        )
        enum_values = set(schema["properties"]["status"]["enum"])
        invalid = []
        for yf in sorted(TASKS_DIR.glob("*.yaml")):
            data = _read_yaml(yf)
            if data and "status" in data:
                if data["status"] not in enum_values:
                    invalid.append((yf.name, data["status"]))
        assert not invalid, (
            f"{len(invalid)} TaskSpec(s) have status not in schema: {invalid}"
        )

    def test_taskspec_count_is_44(self):
        count = len(list(TASKS_DIR.glob("*.yaml")))
        assert count == 44, f"Expected 44 TaskSpec files, got {count}"

    def test_no_complete_status_remain(self):
        """'complete' was unified to 'completed'. Verify zero residual."""
        for yf in sorted(TASKS_DIR.glob("*.yaml")):
            data = _read_yaml(yf)
            if data and "status" in data:
                assert data["status"] != "complete", (
                    f"{yf.name} still has status 'complete' (should be 'completed')"
                )


# ---------------------------------------------------------------------------
# Test: Minimum capability set coverage
# ---------------------------------------------------------------------------


class TestMinimumCapabilitySet:
    """Local governance mode required capabilities must all be verified."""

    LOCAL_GOVERNANCE_REQUIRED = [
        "CAP-002", "CAP-003", "CAP-004", "CAP-005",
        "CAP-006", "CAP-007", "CAP-010", "CAP-015",
        "CAP-016", "CAP-018", "CAP-019", "CAP-028",
    ]

    def test_local_governance_all_verified(self):
        inventory_md = _read_md(DOCS_DIR / "capability-inventory.md")
        entries = _parse_passport_entries(inventory_md)
        by_id = {e["id"]: e for e in entries}
        failures = []
        for cap_id in self.LOCAL_GOVERNANCE_REQUIRED:
            entry = by_id.get(cap_id)
            if not entry:
                failures.append(f"{cap_id}: not found in inventory")
            elif entry.get("status") != "verified":
                failures.append(
                    f"{cap_id}: status={entry.get('status')}, expected verified"
                )
        assert not failures, (
            f"Local governance required capabilities not all verified:\n"
            + "\n".join(failures)
        )

    def test_minimum_capability_set_doc_exists(self):
        path = DOCS_DIR / "minimum-capability-set.md"
        assert path.exists(), "docs/agent-runtime/minimum-capability-set.md not found"
        content = _read_md(path)
        assert "Local Governance" in content
        assert "Controlled Pilot" in content
        assert "VM-004" in content


# ---------------------------------------------------------------------------
# Test: Cross-document consistency (no conflicting PASS/GAP)
# ---------------------------------------------------------------------------


class TestCrossDocumentConsistency:
    """Governance documents must not contain conflicting claims."""

    def test_closure_report_gate0_no_false_pass(self):
        """Closure report GATE0 verdict table should not claim PASS for
        items that are actually GAP."""
        report = _read_md(REPO / "_reports" / "THREE-STEP-CLOSURE-REPORT.md")
        # Find the GATE0 verdict table
        in_table = False
        for line in report.split("\n"):
            if "| Gate |" in line:
                in_table = True
                continue
            if in_table and line.startswith("|"):
                cols = [c.strip() for c in line.split("|")]
                if len(cols) >= 4:
                    gate_name = cols[1]
                    status = cols[2]
                    # If status is PASS, verify notes don't say GAP
                    if status == "PASS" and "GAP" in cols[3]:
                        pytest.fail(
                            f"Contradictory: gate '{gate_name}' marked PASS "
                            f"but notes contain GAP: {cols[3]}"
                        )
            elif in_table and not line.startswith("|"):
                in_table = False

    def test_risk_register_open_count_matches_claim(self):
        """Report's claim about open risks must match actual risk register."""
        rr = _read_yaml(AI_DIR / "risk-register.yaml")
        open_risks = [r for r in rr["risks"] if r["status"] == "open"]
        report = _read_md(REPO / "_reports" / "THREE-STEP-CLOSURE-REPORT.md")

        # Report should mention the correct number of open risks
        expected_text = f"{len(open_risks)} open tracked risks"
        assert expected_text in report, (
            f"Report should say '{expected_text}' but doesn't. "
            f"Open risks: {[r['id'] for r in open_risks]}"
        )
