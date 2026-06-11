"""Tests for SADP Pre-Task Enforcer — validates enforcement at task boundaries.

Tests cover:
  1. pre_task: TaskSpec validation (Gate 0, Conflict Registry, acceptance gates)
  2. pre_edit: File write_set membership and protected file blocking
  3. post_task: ExecutionReport and evidence artifact verification
  4. Edge cases: missing TaskSpec, protected files, scope creep
"""

import json
import re
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

REPO = Path(__file__).resolve().parent.parent
SCRIPTS = REPO / "scripts"
sys.path.insert(0, str(SCRIPTS))

import sadp_pre_task_enforcer as enforcer


# ── Fixtures ──────────────────────────────────────────────────────────


@pytest.fixture
def valid_taskspec_content():
    """A minimal valid TaskSpec with Gate 0 + Conflict Registry."""
    return """# TaskSpec: Test Task

- **ID**: test-task-001
- **Batch**: test-batch
- **Risk**: low
- **Priority**: P1
- **Goal**: Test goal
- **Context**: Test context
- **Allowed Files**:
  - scripts/foo.py (new)
- **Forbidden**:
  - Do not modify core rules

- **Gate 0 Ledger**:
  ```yaml
  gate_0:
    triggered: true
    trigger_reason: "test"
    inventory_evidence:
      queried_sources:
        - capability-inventory.md
      matched_capabilities:
        - none
      compared_against_request:
        - "test requirement"
    rules_checked:
      - core-008
    lessons_checked:
      - LL-009
    sufficiency_decision: existing_sufficient
    decision: reuse
  ```

- **Conflict Registry**:
  ```yaml
  conflict_registry:
    read_set:
      - scripts/bar.py
    write_set:
      - scripts/foo.py
    protected_files_touched: false
    conflict_level: low
  ```

- **Acceptance Gates**:
  1. foo.py exists
  2. Tests pass

- **Expected Output**: test output
- **Rollback**: delete foo.py
- **Report To**: this session
"""


@pytest.fixture
def invalid_taskspec_no_gate0():
    """TaskSpec missing Gate 0 Ledger."""
    return """# TaskSpec: Invalid Task

- **ID**: invalid-task-001
- **Batch**: test-batch
- **Risk**: low
- **Priority**: P1
- **Goal**: Test goal

- **Conflict Registry**:
  ```yaml
  conflict_registry:
    read_set:
      - scripts/bar.py
    write_set:
      - scripts/foo.py
    protected_files_touched: false
    conflict_level: low
  ```

- **Acceptance Gates**:
  1. Tests pass
"""


@pytest.fixture
def invalid_taskspec_no_cr():
    """TaskSpec missing Conflict Registry."""
    return """# TaskSpec: Invalid Task

- **ID**: invalid-task-002
- **Batch**: test-batch
- **Risk**: low
- **Priority**: P1
- **Goal**: Test goal

- **Gate 0 Ledger**:
  ```yaml
  gate_0:
    triggered: true
    trigger_reason: "test"
    inventory_evidence:
      queried_sources:
        - capability-inventory.md
      matched_capabilities:
        - none
      compared_against_request:
        - "test requirement"
    sufficiency_decision: existing_sufficient
    decision: reuse
  ```

- **Acceptance Gates**:
  1. Tests pass
"""


# ── 1. TaskSpec Parsing ──────────────────────────────────────────────


class TestTaskSpecParsing:
    """Test TaskSpec parsing functions."""

    def test_find_taskspec_existing(self):
        """Should find the real SHARED-CDP-V2-REVIEW-FINDINGS-FIX-A1 TaskSpec."""
        path = enforcer.find_taskspec("SHARED-CDP-V2-REVIEW-FINDINGS-FIX-A1")
        assert path is not None
        assert path.exists()

    def test_find_taskspec_nonexistent(self):
        """Should return None for nonexistent TaskSpec."""
        path = enforcer.find_taskspec("NONEXISTENT-TASK-999")
        assert path is None

    def test_parse_gate0_valid(self, valid_taskspec_content, tmp_path):
        """Should parse valid Gate 0 block."""
        taskspec = tmp_path / "task-test.md"
        taskspec.write_text(valid_taskspec_content)
        gate0 = enforcer.parse_taskspec_gate0(taskspec)
        assert gate0["has_inventory_evidence"] is True
        assert gate0["has_queried_sources"] is True
        assert gate0["has_matched_capabilities"] is True
        assert gate0["has_sufficiency_decision"] is True
        assert gate0["has_decision"] is True

    def test_parse_gate0_missing(self, invalid_taskspec_no_gate0, tmp_path):
        """Should return empty dict when no gate_0 block."""
        taskspec = tmp_path / "task-invalid.md"
        taskspec.write_text(invalid_taskspec_no_gate0)
        gate0 = enforcer.parse_taskspec_gate0(taskspec)
        assert gate0 == {} or not gate0.get("has_inventory_evidence")

    def test_parse_conflict_registry(self, valid_taskspec_content, tmp_path):
        """Should parse conflict registry with write_set."""
        taskspec = tmp_path / "task-test.md"
        taskspec.write_text(valid_taskspec_content)
        cr = enforcer.parse_taskspec_conflict_registry(taskspec)
        assert cr["has_read_set"] is True
        assert cr["has_write_set"] is True
        assert cr["has_conflict_level"] is True
        assert "scripts/foo.py" in cr["write_set"]

    def test_parse_acceptance_gates(self, valid_taskspec_content, tmp_path):
        """Should parse acceptance gates list."""
        taskspec = tmp_path / "task-test.md"
        taskspec.write_text(valid_taskspec_content)
        gates = enforcer.parse_taskspec_acceptance_gates(taskspec)
        assert len(gates) == 2
        assert "foo.py exists" in gates[0]

    def test_parse_gate0_new_delta_requires_justification(self, tmp_path):
        """new_delta_required without delta_justification should be flagged."""
        content = """
- **Gate 0 Ledger**:
  ```yaml
  gate_0:
    triggered: true
    trigger_reason: "test"
    inventory_evidence:
      queried_sources:
        - capability-inventory.md
      matched_capabilities:
        - none
      compared_against_request:
        - "test requirement"
    sufficiency_decision: new_delta_required
    decision: build_delta
  ```
"""
        taskspec = tmp_path / "task-delta.md"
        taskspec.write_text(content)
        gate0 = enforcer.parse_taskspec_gate0(taskspec)
        assert gate0["sufficiency_decision_value"] == "new_delta_required"
        assert gate0["has_delta_justification"] is False


# ── 2. Pre-Task Enforcement ─────────────────────────────────────────


class TestPreTaskEnforcement:
    """Test pre_task enforcement checks."""

    def test_existing_taskspec_passes(self):
        """Real TaskSpec should pass pre_task validation."""
        exit_code, messages = enforcer.check_pre_task("SHARED-CDP-V2-REVIEW-FINDINGS-FIX-A1")
        assert exit_code == 0
        assert any("PASS" in m for m in messages)

    def test_nonexistent_taskspec_blocked(self):
        """Nonexistent TaskSpec should BLOCK."""
        exit_code, messages = enforcer.check_pre_task("NONEXISTENT-TASK-999")
        assert exit_code == 1
        assert any("BLOCKED" in m for m in messages)

    def test_missing_gate0_blocked(self, invalid_taskspec_no_gate0, tmp_path):
        """TaskSpec without Gate 0 should BLOCK."""
        # Create a temporary TaskSpec file in the tasks dir
        taskspec = tmp_path / "task-no-gate0.md"
        taskspec.write_text(invalid_taskspec_no_gate0.replace("invalid-task-001", "test-no-gate0"))
        
        with patch.object(enforcer, "TASKS_DIR", tmp_path):
            exit_code, messages = enforcer.check_pre_task("test-no-gate0")
            assert exit_code == 1

    def test_missing_cr_blocked(self, invalid_taskspec_no_cr, tmp_path):
        """TaskSpec without Conflict Registry should BLOCK."""
        taskspec = tmp_path / "task-no-cr.md"
        taskspec.write_text(invalid_taskspec_no_cr.replace("invalid-task-002", "test-no-cr"))
        
        with patch.object(enforcer, "TASKS_DIR", tmp_path):
            exit_code, messages = enforcer.check_pre_task("test-no-cr")
            assert exit_code == 1

    def test_protected_file_in_write_set_blocked(self, tmp_path):
        """TaskSpec with protected file in write_set should BLOCK."""
        content = """# TaskSpec: Protected Test

- **ID**: test-protected-001
- **Batch**: test
- **Risk**: high
- **Priority**: P0
- **Goal**: Test

- **Gate 0 Ledger**:
  ```yaml
  gate_0:
    triggered: true
    trigger_reason: "test"
    inventory_evidence:
      queried_sources:
        - capability-inventory.md
      matched_capabilities:
        - none
      compared_against_request:
        - "test"
    sufficiency_decision: existing_sufficient
    decision: reuse
  ```

- **Conflict Registry**:
  ```yaml
  conflict_registry:
    read_set:
      - rules/core.md
    write_set:
      - rules/core.md
    protected_files_touched: true
    conflict_level: high
  ```

- **Acceptance Gates**:
  1. Tests pass
"""
        taskspec = tmp_path / "task-protected.md"
        taskspec.write_text(content)

        with patch.object(enforcer, "TASKS_DIR", tmp_path):
            exit_code, messages = enforcer.check_pre_task("test-protected-001")
            assert exit_code == 1
            assert any("Protected" in m for m in messages)


# ── 3. Pre-Edit Enforcement ──────────────────────────────────────────


class TestPreEditEnforcement:
    """Test pre_edit enforcement checks."""

    def test_protected_file_blocked(self):
        """Protected governance file should BLOCK."""
        exit_code, messages = enforcer.check_pre_edit("rules/core.md")
        assert exit_code == 1
        assert any("BLOCKED" in m for m in messages)

    def test_self_protecting_file_blocked(self):
        """Self-protecting enforcer file should BLOCK with HUMAN_REQUIRED."""
        exit_code, messages = enforcer.check_pre_edit("scripts/sadp_pre_task_enforcer.py")
        assert exit_code == 1
        assert any("self-protecting" in m or "HUMAN_REQUIRED" in m for m in messages)

    def test_sadp_audit_self_protecting(self):
        """sadp-audit.ps1 is both protected and self-protecting."""
        exit_code, messages = enforcer.check_pre_edit("scripts/sadp-audit.ps1")
        assert exit_code == 1

    def test_sadp_policy_protected(self):
        """SADP_POLICY.json should be protected."""
        exit_code, messages = enforcer.check_pre_edit(".sadp/SADP_POLICY.json")
        assert exit_code == 1

    def test_non_protected_file_passes(self):
        """Non-protected file without task_id should PASS with advisory."""
        exit_code, messages = enforcer.check_pre_edit("scripts/foo.py")
        assert exit_code == 2  # WARNING (advisory)
        assert any("not a protected" in m for m in messages)

    def test_file_in_write_set_passes(self):
        """File in TaskSpec write_set should PASS."""
        exit_code, messages = enforcer.check_pre_edit(
            "scripts/tab_target_resolver.py",
            "SHARED-CDP-V2-REVIEW-FINDINGS-FIX-A1",
        )
        assert exit_code == 0
        assert any("in TaskSpec write_set" in m for m in messages)

    def test_file_not_in_write_set_warns(self):
        """File not in write_set should WARNING (P0 task uses policy)."""
        exit_code, messages = enforcer.check_pre_edit(
            "scripts/unrelated_file.py",
            "SHARED-CDP-V2-REVIEW-FINDINGS-FIX-A1",
        )
        # P0 task — should be BLOCKED per policy
        assert exit_code == 1  # BLOCKED for P0
        assert any("BLOCKED" in m or "scope creep" in m for m in messages)

    def test_p0_scope_creep_blocked(self):
        """P0 task scope creep should be BLOCKED."""
        exit_code, messages = enforcer.check_pre_edit(
            "scripts/out_of_scope.py",
            "SHARED-CDP-V2-REVIEW-FINDINGS-FIX-A1",  # This is P0
        )
        assert exit_code == 1
        assert any("BLOCKED" in m for m in messages)

    def test_no_taskspec_for_edit_warn(self):
        """No TaskSpec found should WARNING."""
        exit_code, messages = enforcer.check_pre_edit(
            "scripts/foo.py",
            "NONEXISTENT-TASK-999",
        )
        assert exit_code == 2


# ── 4. Post-Task Enforcement ─────────────────────────────────────────


class TestPostTaskEnforcement:
    """Test post_task enforcement checks."""

    def test_completed_task_passes(self):
        """Completed task with ExecutionReport should PASS."""
        exit_code, messages = enforcer.check_post_task("SHARED-CDP-V2-REVIEW-FINDINGS-FIX-A1")
        assert exit_code == 0
        assert any("ExecutionReport found" in m for m in messages)
        assert any("Reviewer Index exists" in m for m in messages)

    def test_nonexistent_task_blocked(self):
        """Task without TaskSpec should BLOCK."""
        exit_code, messages = enforcer.check_post_task("NONEXISTENT-TASK-999")
        assert exit_code == 1

    def test_missing_execution_report(self, valid_taskspec_content, tmp_path):
        """TaskSpec exists but no ExecutionReport should BLOCK."""
        taskspec = tmp_path / "task-no-er.md"
        taskspec.write_text(valid_taskspec_content.replace("test-task-001", "test-no-er"))

        with patch.object(enforcer, "TASKS_DIR", tmp_path), \
             patch.object(enforcer, "REPO", tmp_path.parent):
            exit_code, messages = enforcer.check_post_task("test-no-er")
            assert exit_code == 1
            assert any("ExecutionReport" in m for m in messages)


# ── 5. Protected Files List ──────────────────────────────────────────


class TestProtectedFiles:
    """Verify the protected files list is correct."""

    def test_core_rules_protected(self):
        assert "rules/core.md" in enforcer.PROTECTED_FILES

    def test_sadp_protocol_protected(self):
        assert "docs/agent-runtime/sub-agent-dispatch-protocol.md" in enforcer.PROTECTED_FILES

    def test_capability_inventory_protected(self):
        assert "docs/agent-runtime/capability-inventory.md" in enforcer.PROTECTED_FILES

    def test_resource_policy_not_protected(self):
        """Resource policy is governance-adjacent, NOT protected."""
        assert ".agent/MULTI_PROJECT_RESOURCE_POLICY.json" not in enforcer.PROTECTED_FILES

    def test_resource_policy_is_adjacent(self):
        """Resource policy should be in governance-adjacent set."""
        assert ".agent/MULTI_PROJECT_RESOURCE_POLICY.json" in enforcer.GOVERNANCE_ADJACENT

    def test_sadp_policy_protected(self):
        """SADP_POLICY.json should be protected (unified policy source)."""
        assert ".sadp/SADP_POLICY.json" in enforcer.PROTECTED_FILES

    def test_trigger_rules_protected(self):
        """TRIGGER_RULES.json should be protected."""
        assert ".sadp/TRIGGER_RULES.json" in enforcer.PROTECTED_FILES

    def test_sadp_audit_protected(self):
        """sadp-audit.ps1 should be protected."""
        assert "scripts/sadp-audit.ps1" in enforcer.PROTECTED_FILES

    def test_enforcer_self_protecting(self):
        """Enforcer script should be self-protecting."""
        assert "scripts/sadp_pre_task_enforcer.py" in enforcer.SELF_PROTECTING_FILES

    def test_audit_self_protecting(self):
        """sadp-audit.ps1 should also be self-protecting."""
        assert "scripts/sadp-audit.ps1" in enforcer.SELF_PROTECTING_FILES

    def test_runner_self_protecting(self):
        """qoderwork_task_runner.py should be self-protecting (R8 fix)."""
        assert "scripts/qoderwork_task_runner.py" in enforcer.SELF_PROTECTING_FILES

    def test_runner_edit_check_blocked(self):
        """Runner file should be BLOCKED by edit-check (HUMAN_REQUIRED)."""
        exit_code, messages = enforcer.check_pre_edit("scripts/qoderwork_task_runner.py")
        assert exit_code == 1
        assert any("self-protecting" in m or "HUMAN_REQUIRED" in m for m in messages)


# ── 7. Policy Loading and Priority Parsing ────────────────────────────


class TestPolicyDrift:
    """Drift tests: ensure enforcer in-code sets match SADP_POLICY.json (R8 fix).

    If these tests fail, the enforcer and the policy file have diverged,
    meaning sadp-audit.ps1 and sadp_pre_task_enforcer.py would enforce
    different rules from the same policy source.
    """

    def test_self_protecting_files_no_drift(self):
        """Enforcer SELF_PROTECTING_FILES must match SADP_POLICY.json."""
        policy = enforcer.load_sadp_policy()
        if not policy:
            pytest.skip("SADP_POLICY.json not found")

        policy_spf = set(policy.get("self_protecting_enforcer_files", []))
        enforcer_spf = enforcer.SELF_PROTECTING_FILES

        assert policy_spf == enforcer_spf, (
            f"Policy drift detected!\n"
            f"  SADP_POLICY.json self_protecting: {sorted(policy_spf)}\n"
            f"  Enforcer SELF_PROTECTING_FILES:   {sorted(enforcer_spf)}\n"
            f"  In policy but not enforcer: {sorted(policy_spf - enforcer_spf)}\n"
            f"  In enforcer but not policy: {sorted(enforcer_spf - policy_spf)}"
        )

    def test_protected_files_no_drift(self):
        """Enforcer PROTECTED_FILES must match SADP_POLICY.json protected_files."""
        policy = enforcer.load_sadp_policy()
        if not policy:
            pytest.skip("SADP_POLICY.json not found")

        policy_pf = set(policy.get("protected_files", []))
        enforcer_pf = enforcer.PROTECTED_FILES

        assert policy_pf == enforcer_pf, (
            f"Policy drift detected!\n"
            f"  SADP_POLICY.json protected: {sorted(policy_pf)}\n"
            f"  Enforcer PROTECTED_FILES:   {sorted(enforcer_pf)}\n"
            f"  In policy but not enforcer: {sorted(policy_pf - enforcer_pf)}\n"
            f"  In enforcer but not policy: {sorted(enforcer_pf - policy_pf)}"
        )

    def test_governance_adjacent_no_drift(self):
        """Enforcer GOVERNANCE_ADJACENT must match SADP_POLICY.json."""
        policy = enforcer.load_sadp_policy()
        if not policy:
            pytest.skip("SADP_POLICY.json not found")

        policy_ga = set(policy.get("governance_adjacent_files", []))
        enforcer_ga = enforcer.GOVERNANCE_ADJACENT

        assert policy_ga == enforcer_ga, (
            f"Policy drift detected!\n"
            f"  SADP_POLICY.json governance_adjacent: {sorted(policy_ga)}\n"
            f"  Enforcer GOVERNANCE_ADJACENT:         {sorted(enforcer_ga)}\n"
            f"  In policy but not enforcer: {sorted(policy_ga - enforcer_ga)}\n"
            f"  In enforcer but not policy: {sorted(enforcer_ga - policy_ga)}"
        )

    def test_scope_creep_policy_loaded(self):
        """Scope creep policy from SADP_POLICY.json should define all priorities."""
        policy = enforcer.load_sadp_policy()
        if not policy:
            pytest.skip("SADP_POLICY.json not found")

        scp = policy.get("pre_edit_policy", {}).get("scope_creep_by_priority", {})
        for priority in ("P0", "P1", "P2", "P3"):
            assert priority in scp, f"Missing scope_creep policy for {priority}"


class TestPolicyLoading:
    """Test SADP policy loading from .sadp/SADP_POLICY.json."""

    def test_load_policy_exists(self):
        """Should load the real SADP_POLICY.json."""
        policy = enforcer.load_sadp_policy()
        assert isinstance(policy, dict)
        # If .sadp/SADP_POLICY.json exists, it should have pre_edit_policy
        if policy:
            assert "pre_edit_policy" in policy or "schema_version" in policy

    def test_load_policy_missing_returns_empty(self, tmp_path):
        """Should return empty dict if policy file missing."""
        with patch.object(enforcer, "SADP_DIR", tmp_path / "nonexistent"):
            policy = enforcer.load_sadp_policy()
            assert policy == {}

    def test_parse_priority_p0(self, tmp_path):
        """Should parse P0 priority from TaskSpec."""
        taskspec = tmp_path / "task-p0.md"
        taskspec.write_text("# TaskSpec\n- **Priority**: P0\n")
        assert enforcer.parse_taskspec_priority(taskspec) == "P0"

    def test_parse_priority_p1(self, tmp_path):
        """Should parse P1 priority from TaskSpec."""
        taskspec = tmp_path / "task-p1.md"
        taskspec.write_text("# TaskSpec\n- **Priority**: P1\n")
        assert enforcer.parse_taskspec_priority(taskspec) == "P1"

    def test_parse_priority_p2(self, tmp_path):
        """Should parse P2 priority from TaskSpec."""
        taskspec = tmp_path / "task-p2.md"
        taskspec.write_text("# TaskSpec\n- **Priority**: P2\n")
        assert enforcer.parse_taskspec_priority(taskspec) == "P2"

    def test_parse_priority_default(self, tmp_path):
        """Should default to P3 if no priority specified."""
        taskspec = tmp_path / "task-no-priority.md"
        taskspec.write_text("# TaskSpec\n- **ID**: test\n")
        assert enforcer.parse_taskspec_priority(taskspec) == "P3"

    def test_real_taskspec_priority(self):
        """Real SHARED-CDP-V2 TaskSpec should be P0."""
        path = enforcer.find_taskspec("SHARED-CDP-V2-REVIEW-FINDINGS-FIX-A1")
        if path:
            priority = enforcer.parse_taskspec_priority(path)
            assert priority == "P0"


# ── 6. ExecutionReport Detection ──────────────────────────────────────


class TestExecutionReportDetection:
    """Test ExecutionReport discovery."""

    def test_find_existing_er(self):
        """Should find the SHARED-CDP-V2 evidence pack ExecutionReport."""
        er = enforcer.find_execution_report("SHARED-CDP-V2-REVIEW-FINDINGS-FIX-A1")
        assert er is not None
        assert er.exists()
        assert "EXECUTION_REPORT" in er.name

    def test_find_nonexistent_er(self):
        """Should return None for nonexistent ExecutionReport."""
        er = enforcer.find_execution_report("NONEXISTENT-TASK-999")
        assert er is None


# -- 8. SADP Audit Policy Smoke Tests (SADP-AUDIT-POLICY-SMOKE-A1) ----


class TestAuditPolicySmoke:
    """Cross-consumer policy consistency: sadp-audit.ps1 <-> SADP_POLICY.json.

    Validates that the PowerShell commit-time audit script's hardcoded
    governance patterns cover the protected files listed in SADP_POLICY.json.
    Catches drift between the two enforcement consumers (Python + PowerShell).
    """

    AUDIT_SCRIPT_PATH = REPO / "scripts" / "sadp-audit.ps1"
    POLICY_PATH = REPO / ".sadp" / "SADP_POLICY.json"

    @classmethod
    def _parse_governance_patterns(cls) -> list[str]:
        """Extract $governancePatterns array from sadp-audit.ps1."""
        content = cls.AUDIT_SCRIPT_PATH.read_text(encoding="utf-8")
        # Match the governancePatterns array: @( ... )
        m = re.search(
            r'\$governancePatterns\s*=\s*@\(\s*\n(.*?)\n\s*\)',
            content, re.DOTALL
        )
        if not m:
            return []
        block = m.group(1)
        # Extract each quoted string
        return re.findall(r'"([^"]+)"', block)

    @classmethod
    def _file_matches_pattern(cls, filepath: str, patterns: list[str]) -> bool:
        """Check if a filepath matches any governance pattern (regex)."""
        normalized = filepath.replace("/", "\\")
        for pat in patterns:
            try:
                if re.search(pat, normalized, re.IGNORECASE):
                    return True
                # Also try with forward slashes
                if re.search(pat, filepath, re.IGNORECASE):
                    return True
            except re.error:
                # If regex fails, try simple substring match
                if pat.replace("\\\\", "\\").replace("\\", "/") in filepath:
                    return True
        return False

    def test_policy_json_valid(self):
        """SADP_POLICY.json must be valid JSON with required top-level keys."""
        assert self.POLICY_PATH.exists(), "SADP_POLICY.json must exist"
        content = self.POLICY_PATH.read_text(encoding="utf-8")
        policy = json.loads(content)  # Will raise if invalid JSON

        required_keys = [
            "protected_files",
            "self_protecting_enforcer_files",
            "governance_adjacent_files",
            "pre_edit_policy",
        ]
        for key in required_keys:
            assert key in policy, f"SADP_POLICY.json missing required key: {key}"

    def test_policy_schema_version(self):
        """SADP_POLICY.json should declare a schema_version."""
        policy = json.loads(self.POLICY_PATH.read_text(encoding="utf-8"))
        assert "schema_version" in policy, "Missing schema_version"
        assert policy["schema_version"] == "1.0.0"

    def test_audit_script_exists(self):
        """sadp-audit.ps1 must exist at scripts/sadp-audit.ps1."""
        assert self.AUDIT_SCRIPT_PATH.exists(), "sadp-audit.ps1 must exist"

    def test_governance_patterns_parseable(self):
        """Should be able to extract governance patterns from sadp-audit.ps1."""
        patterns = self._parse_governance_patterns()
        assert len(patterns) > 0, "No governance patterns found in sadp-audit.ps1"

    def test_agents_md_covered(self):
        """AGENTS.md must be covered by governance patterns."""
        patterns = self._parse_governance_patterns()
        assert self._file_matches_pattern("AGENTS.md", patterns), (
            "AGENTS.md not matched by any governance pattern"
        )

    def test_claude_md_covered(self):
        """CLAUDE.md must be covered by governance patterns."""
        patterns = self._parse_governance_patterns()
        assert self._file_matches_pattern("CLAUDE.md", patterns), (
            "CLAUDE.md not matched by any governance pattern"
        )

    def test_rules_core_covered(self):
        """rules/core.md must be covered by governance patterns."""
        patterns = self._parse_governance_patterns()
        assert self._file_matches_pattern("rules/core.md", patterns), (
            "rules/core.md not matched by any governance pattern"
        )

    def test_sadp_protocol_covered(self):
        """sub-agent-dispatch-protocol.md must be covered."""
        patterns = self._parse_governance_patterns()
        assert self._file_matches_pattern(
            "docs/agent-runtime/sub-agent-dispatch-protocol.md", patterns
        ), "sub-agent-dispatch-protocol.md not matched"

    def test_capability_inventory_covered(self):
        """capability-inventory.md must be covered."""
        patterns = self._parse_governance_patterns()
        assert self._file_matches_pattern(
            "docs/agent-runtime/capability-inventory.md", patterns
        ), "capability-inventory.md not matched"

    def test_lessons_learned_covered(self):
        """docs/agent-runtime/lessons-learned.md must be covered."""
        patterns = self._parse_governance_patterns()
        assert self._file_matches_pattern(
            "docs/agent-runtime/lessons-learned.md", patterns
        ), "lessons-learned.md not matched"

    def test_all_protected_files_coverage_report(self):
        """Report coverage of ALL protected files — fail if any unprotected gap.

        Self-protecting enforcer files (sadp-audit.ps1, etc.) are excluded
        because they are protected by the pre-edit enforcer, not by commit-time
        audit pattern matching.
        """
        policy = json.loads(self.POLICY_PATH.read_text(encoding="utf-8"))
        protected = set(policy.get("protected_files", []))
        self_protecting = set(policy.get("self_protecting_enforcer_files", []))
        patterns = self._parse_governance_patterns()

        # Self-protecting files are guarded by pre-edit enforcer, not patterns
        pattern_protected = protected - self_protecting

        uncovered = []
        for f in sorted(pattern_protected):
            if not self._file_matches_pattern(f, patterns):
                uncovered.append(f)

        # After SADP-AUDIT-DOT-SADP-COVERAGE-A1, .sadp/ files should be covered
        # No known gaps should remain — all uncovered files are real issues
        assert not uncovered, (
            f"Protected files with NO governance pattern coverage:\n"
            f"  {uncovered}\n"
            f"  These files can be modified without triggering SADP audit.\n"
            f"  Add matching patterns to $governancePatterns in sadp-audit.ps1."
        )

    def test_sadp_directory_pattern_coverage(self):
        """.sadp/ directory should be in governance patterns for full coverage.

        After SADP-AUDIT-DOT-SADP-COVERAGE-A1, .sadp\\ pattern should be present
        in sadp-audit.ps1 $governancePatterns, ensuring commit-time audit
        detects changes to .sadp/ policy files.
        """
        patterns = self._parse_governance_patterns()
        has_sadp_pattern = any(
            ".sadp" in p or "sadp" in p.lower()
            for p in patterns
        )
        assert has_sadp_pattern, (
            "No .sadp/ governance pattern in sadp-audit.ps1. "
            "The .sadp/ directory must be covered by commit-time audit."
        )

    def test_policy_pre_task_fields(self):
        """SADP_POLICY.json pre_task_policy should have required fields."""
        policy = json.loads(self.POLICY_PATH.read_text(encoding="utf-8"))
        pre_task = policy.get("pre_task_policy", {})
        required = [
            "require_taskspec",
            "require_gate0",
            "require_conflict_registry",
        ]
        for field in required:
            assert field in pre_task, f"pre_task_policy missing: {field}"
            assert pre_task[field] is True, f"{field} should be true"

    def test_policy_post_task_fields(self):
        """SADP_POLICY.json post_task_policy should have required fields."""
        policy = json.loads(self.POLICY_PATH.read_text(encoding="utf-8"))
        post_task = policy.get("post_task_policy", {})
        assert "require_execution_report" in post_task
        assert post_task["require_execution_report"] is True
