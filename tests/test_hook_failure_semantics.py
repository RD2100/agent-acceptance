"""Tests for hook failure semantics (EVIDENCE-CAPTURE-HOOK-FAILURE-SEMANTICS-A1).

Validates that latest.json conforms to schema and that the overall_result mapping
follows the rules defined in docs/agent-runtime/hook-failure-semantics.md.
"""
import json
import pytest
from pathlib import Path

SCHEMA_PATH = Path(__file__).resolve().parent.parent / "schemas" / "agent-runtime" / "evidence-capture.schema.json"
HOOK_PATH = Path(__file__).resolve().parent.parent / "hooks" / "pre-commit.governance.ps1"
DOCS_PATH = Path(__file__).resolve().parent.parent / "docs" / "agent-runtime" / "hook-failure-semantics.md"


@pytest.fixture
def schema():
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


# ── Schema conformance ───────────────────────────────────────────────

class TestSchemaConformance:
    """Verify the evidence-capture schema correctly defines all 4 stages."""

    def test_schema_exists(self):
        assert SCHEMA_PATH.exists()

    def test_max_items_is_4(self, schema):
        assert schema["properties"]["stages"]["maxItems"] == 4

    def test_min_items_is_1(self, schema):
        assert schema["properties"]["stages"]["minItems"] == 1

    def test_stage_enum_includes_ai_guard(self, schema):
        enum = schema["properties"]["stages"]["items"]["properties"]["name"]["enum"]
        assert "ai-guard" in enum

    def test_stage_enum_has_all_4(self, schema):
        enum = schema["properties"]["stages"]["items"]["properties"]["name"]["enum"]
        assert set(enum) == {"manifest-regen", "sadp-audit", "ai-guard", "test-governance"}

    def test_overall_result_has_three_values(self, schema):
        enum = schema["properties"]["overall_result"]["enum"]
        assert set(enum) == {"PASS", "PASS_WITH_WARNINGS", "BLOCKED"}

    def test_required_fields(self, schema):
        assert set(schema["required"]) == {"timestamp", "hook_version", "stages", "git_context", "overall_result"}


# ── Hook script assertions ───────────────────────────────────────────

class TestHookScript:
    """Parse hook script text to verify failure semantic rules are implemented."""

    @pytest.fixture
    def hook_text(self):
        return HOOK_PATH.read_text(encoding="utf-8")

    def test_hook_exists(self):
        assert HOOK_PATH.exists()

    def test_version_is_2_2(self, hook_text):
        assert '$HookVersion = "2.2.0"' in hook_text

    def test_ai_guard_has_timeout(self, hook_text):
        assert "aiGuardTimeoutSec" in hook_text
        assert "Wait-Job" in hook_text
        assert "-Timeout" in hook_text

    def test_ai_guard_timeout_value(self, hook_text):
        assert "$aiGuardTimeoutSec = 30" in hook_text

    def test_sadp_audit_is_blocking(self, hook_text):
        # sadp-audit failure triggers exit 1
        assert 'if ($auditExit -ne 0)' in hook_text
        assert 'exit 1' in hook_text

    def test_ai_guard_marked_non_blocking(self, hook_text):
        assert "NON-BLOCKING" in hook_text

    def test_pass_with_warnings_implemented(self, hook_text):
        assert "PASS_WITH_WARNINGS" in hook_text

    def test_console_message_matches_result(self, hook_text):
        # When PASS_WITH_WARNINGS, console shows warning message
        assert 'if ($overallResult -eq "PASS_WITH_WARNINGS")' in hook_text
        assert "with warnings" in hook_text

    def test_overall_result_sadp_audit_check(self, hook_text):
        # The overall_result loop specifically checks sadp-audit for blocking
        assert '"sadp-audit"' in hook_text or "'sadp-audit'" in hook_text

    def test_ai_guard_output_heuristic(self, hook_text):
        # ai_guard uses output-based exit code detection (Start-Job limitation)
        assert "(?i)\\bFAIL\\b" in hook_text or '(?i)\\bFAIL\\b' in hook_text


# ── Failure semantics mapping ────────────────────────────────────────

class TestFailureSemanticsMapping:
    """Verify the documented mapping between stage exit codes and overall_result."""

    @pytest.fixture
    def docs_text(self):
        return DOCS_PATH.read_text(encoding="utf-8")

    def test_docs_exist(self):
        assert DOCS_PATH.exists()

    def test_documents_blocking_stages(self, docs_text):
        assert "Blocking" in docs_text or "BLOCKING" in docs_text
        assert "sadp-audit" in docs_text

    def test_documents_warning_stages(self, docs_text):
        assert "WARNING" in docs_text or "PASS_WITH_WARNINGS" in docs_text

    def test_documents_advisory_stages(self, docs_text):
        assert "Advisory" in docs_text or "ADVISORY" in docs_text or "advisory" in docs_text

    def test_documents_timeout_behavior(self, docs_text):
        assert "30" in docs_text
        assert "timeout" in docs_text.lower()

    def test_documents_anti_patterns(self, docs_text):
        assert "Anti-Pattern" in docs_text or "anti-pattern" in docs_text

    def test_result_formula(self, docs_text):
        # The mapping formula should be present
        assert "BLOCKED" in docs_text
        assert "PASS_WITH_WARNINGS" in docs_text
        assert "PASS" in docs_text


# ── Simulated overall_result logic ───────────────────────────────────

class TestOverallResultLogic:
    """Simulate the hook's overall_result calculation in Python to verify correctness."""

    @staticmethod
    def compute_overall_result(stages):
        """Mirror the PowerShell logic from the hook script."""
        overall_result = "PASS"
        for s in stages:
            if s["exit_code"] != 0:
                if s["name"] == "sadp-audit":
                    overall_result = "BLOCKED"
                    break
                elif s["name"] == "ai-guard":
                    if overall_result == "PASS":
                        overall_result = "PASS_WITH_WARNINGS"
                # manifest-regen and test-governance: advisory only
        return overall_result

    def test_all_pass(self):
        stages = [
            {"name": "manifest-regen", "exit_code": 0},
            {"name": "sadp-audit", "exit_code": 0},
            {"name": "ai-guard", "exit_code": 0},
            {"name": "test-governance", "exit_code": 0},
        ]
        assert self.compute_overall_result(stages) == "PASS"

    def test_sadp_audit_blocks(self):
        stages = [
            {"name": "manifest-regen", "exit_code": 0},
            {"name": "sadp-audit", "exit_code": 1},
            {"name": "ai-guard", "exit_code": 0},
            {"name": "test-governance", "exit_code": 0},
        ]
        assert self.compute_overall_result(stages) == "BLOCKED"

    def test_ai_guard_warns(self):
        stages = [
            {"name": "manifest-regen", "exit_code": 0},
            {"name": "sadp-audit", "exit_code": 0},
            {"name": "ai-guard", "exit_code": 1},
            {"name": "test-governance", "exit_code": 0},
        ]
        assert self.compute_overall_result(stages) == "PASS_WITH_WARNINGS"

    def test_sadp_audit_overrides_ai_guard(self):
        """sadp-audit BLOCKED takes precedence over ai-guard PASS_WITH_WARNINGS."""
        stages = [
            {"name": "manifest-regen", "exit_code": 0},
            {"name": "sadp-audit", "exit_code": 1},
            {"name": "ai-guard", "exit_code": 1},
            {"name": "test-governance", "exit_code": 0},
        ]
        assert self.compute_overall_result(stages) == "BLOCKED"

    def test_test_governance_advisory(self):
        """test-governance failure does not affect overall_result."""
        stages = [
            {"name": "manifest-regen", "exit_code": 0},
            {"name": "sadp-audit", "exit_code": 0},
            {"name": "ai-guard", "exit_code": 0},
            {"name": "test-governance", "exit_code": 1},
        ]
        assert self.compute_overall_result(stages) == "PASS"

    def test_manifest_regen_advisory(self):
        """manifest-regen failure does not affect overall_result."""
        stages = [
            {"name": "manifest-regen", "exit_code": 1},
            {"name": "sadp-audit", "exit_code": 0},
            {"name": "ai-guard", "exit_code": 0},
            {"name": "test-governance", "exit_code": 0},
        ]
        assert self.compute_overall_result(stages) == "PASS"

    def test_multiple_advisory_failures(self):
        """Multiple advisory failures still result in PASS (if sadp-audit passes)."""
        stages = [
            {"name": "manifest-regen", "exit_code": 1},
            {"name": "sadp-audit", "exit_code": 0},
            {"name": "ai-guard", "exit_code": 0},
            {"name": "test-governance", "exit_code": 1},
        ]
        assert self.compute_overall_result(stages) == "PASS"

    def test_ai_guard_plus_advisory_failures(self):
        """ai-guard warning + advisory failures = PASS_WITH_WARNINGS."""
        stages = [
            {"name": "manifest-regen", "exit_code": 1},
            {"name": "sadp-audit", "exit_code": 0},
            {"name": "ai-guard", "exit_code": 1},
            {"name": "test-governance", "exit_code": 1},
        ]
        assert self.compute_overall_result(stages) == "PASS_WITH_WARNINGS"
