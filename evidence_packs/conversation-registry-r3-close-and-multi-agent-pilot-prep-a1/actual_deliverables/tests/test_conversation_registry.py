#!/usr/bin/env python3
"""test_conversation_registry.py — Tests for AWSP v1.3.0 conversation registry.

Covers:
1. Scaffold generates CONVERSATION_BINDING.json and CONVERSATION_REGISTRY.schema.json
2. validate_scaffold() checks conversation binding
3. validate_conversation_registry.py standalone validator
"""

import json
import sys
from pathlib import Path
import pytest
from jsonschema import Draft202012Validator

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))

from awsp_scaffold import create_scaffold, validate_scaffold
from validate_conversation_registry import validate_binding


# ---------------------------------------------------------------------------
# Tests: Scaffold generates conversation registry files
# ---------------------------------------------------------------------------

class TestConversationBindingScaffold:
    """Tests for scaffold generation of conversation registry files."""

    def test_scaffold_creates_conversation_binding(self, tmp_path):
        """create_scaffold creates .agent/CONVERSATION_BINDING.json."""
        project = tmp_path / "cb-scaffold-project"
        project.mkdir()
        create_scaffold(str(project))
        binding_path = project / ".agent" / "CONVERSATION_BINDING.json"
        assert binding_path.exists(), "CONVERSATION_BINDING.json not created by scaffold"

    def test_scaffold_creates_registry_schema(self, tmp_path):
        """create_scaffold creates .agent/CONVERSATION_REGISTRY.schema.json."""
        project = tmp_path / "rs-scaffold-project"
        project.mkdir()
        create_scaffold(str(project))
        schema_path = project / ".agent" / "CONVERSATION_REGISTRY.schema.json"
        assert schema_path.exists(), "CONVERSATION_REGISTRY.schema.json not created by scaffold"

    def test_conversation_binding_valid_json(self, tmp_path):
        """Generated CONVERSATION_BINDING.json is valid JSON with schema_version."""
        project = tmp_path / "cb-json-project"
        project.mkdir()
        create_scaffold(str(project))
        binding_path = project / ".agent" / "CONVERSATION_BINDING.json"
        data = json.loads(binding_path.read_text(encoding="utf-8"))
        assert "schema_version" in data, "CONVERSATION_BINDING.json missing schema_version"
        assert data["schema_version"] == "1.0.0"

    def test_registry_schema_valid_json(self, tmp_path):
        """Generated CONVERSATION_REGISTRY.schema.json is valid JSON with schema_version."""
        project = tmp_path / "rs-json-project"
        project.mkdir()
        create_scaffold(str(project))
        schema_path = project / ".agent" / "CONVERSATION_REGISTRY.schema.json"
        data = json.loads(schema_path.read_text(encoding="utf-8"))
        assert "schema_version" in data, "CONVERSATION_REGISTRY.schema.json missing schema_version"
        assert data["schema_version"] == "1.0.0"

    def test_registry_schema_top_level_required_fields(self, tmp_path):
        """Generated schema validates the whole binding file top-level fields."""
        project = tmp_path / "rs-top-level-project"
        project.mkdir()
        create_scaffold(str(project))
        schema_path = project / ".agent" / "CONVERSATION_REGISTRY.schema.json"
        data = json.loads(schema_path.read_text(encoding="utf-8"))
        assert data["type"] == "object"
        for field in [
            "schema_version",
            "awsp_version",
            "project_id",
            "project_root",
            "default_conversation_policy",
            "governance_scope",
            "bindings",
        ]:
            assert field in data["required"]
        assert data["properties"]["bindings"]["type"] == "array"
        assert data["properties"]["bindings"]["items"]["type"] == "object"

    def test_validate_scaffold_passes_with_binding(self, tmp_path):
        """validate_scaffold passes on a fresh scaffold that includes conversation binding."""
        project = tmp_path / "validate-binding-project"
        project.mkdir()
        create_scaffold(str(project))
        result = validate_scaffold(str(project))
        assert result["valid"] is True, (
            f"Fresh scaffold should pass validation, errors: {result['errors']}"
        )

    def test_validate_scaffold_missing_binding_fails(self, tmp_path):
        """Removing CONVERSATION_BINDING.json causes validate_scaffold to fail."""
        project = tmp_path / "no-binding-project"
        project.mkdir()
        create_scaffold(str(project))
        binding_path = project / ".agent" / "CONVERSATION_BINDING.json"
        binding_path.unlink()
        result = validate_scaffold(str(project))
        assert result["valid"] is False
        assert any("CONVERSATION_BINDING.json" in e for e in result["errors"])

    def test_validate_scaffold_missing_registry_schema_fails(self, tmp_path):
        """Removing CONVERSATION_REGISTRY.schema.json causes validate_scaffold to fail."""
        project = tmp_path / "no-schema-project"
        project.mkdir()
        create_scaffold(str(project))
        schema_path = project / ".agent" / "CONVERSATION_REGISTRY.schema.json"
        schema_path.unlink()
        result = validate_scaffold(str(project))
        assert result["valid"] is False
        assert any("CONVERSATION_REGISTRY.schema.json" in e for e in result["errors"])

    def test_binding_has_capture_policy(self, tmp_path):
        """Generated binding has all 4 capture_policy fields set to true."""
        project = tmp_path / "capture-policy-project"
        project.mkdir()
        create_scaffold(str(project))
        binding_path = project / ".agent" / "CONVERSATION_BINDING.json"
        data = json.loads(binding_path.read_text(encoding="utf-8"))
        assert "bindings" in data
        assert len(data["bindings"]) > 0
        capture_policy = data["bindings"][0]["capture_policy"]
        required_fields = [
            "must_match_run_id",
            "must_match_task_id",
            "must_include_end_marker",
            "forbid_last_message_only_capture",
        ]
        for field in required_fields:
            assert field in capture_policy, f"capture_policy missing field: {field}"
            assert capture_policy[field] is True, (
                f"capture_policy.{field} should be true, got {capture_policy[field]}"
            )


# ---------------------------------------------------------------------------
# Tests: Standalone validate_conversation_registry.py validator
# ---------------------------------------------------------------------------

class TestConversationRegistryValidator:
    """Tests for the standalone validate_binding() function."""

    def test_valid_binding_passes(self, tmp_path):
        """create scaffold then validate_binding on the binding file passes."""
        project = tmp_path / "valid-binding-project"
        project.mkdir()
        create_scaffold(str(project))
        binding_path = project / ".agent" / "CONVERSATION_BINDING.json"
        result = validate_binding(str(binding_path))
        assert result["valid"] is True, (
            f"Valid binding should pass, errors: {result.get('errors', [])}"
        )

    def test_missing_file_fails(self, tmp_path):
        """Non-existent binding file path returns valid=False."""
        fake_path = tmp_path / "nonexistent" / "CONVERSATION_BINDING.json"
        result = validate_binding(str(fake_path))
        assert result["valid"] is False
        assert len(result["errors"]) > 0

    def test_invalid_json_fails(self, tmp_path):
        """Corrupt JSON in binding file returns valid=False."""
        binding_path = tmp_path / "CONVERSATION_BINDING.json"
        binding_path.write_text("{not valid json!!!", encoding="utf-8")
        result = validate_binding(str(binding_path))
        assert result["valid"] is False
        assert any("json" in e.lower() or "JSON" in e or "parse" in e.lower()
                    for e in result["errors"])

    def test_missing_schema_version_fails(self, tmp_path):
        """Binding without schema_version field fails validation."""
        project = tmp_path / "no-sv-project"
        project.mkdir()
        create_scaffold(str(project))
        binding_path = project / ".agent" / "CONVERSATION_BINDING.json"
        data = json.loads(binding_path.read_text(encoding="utf-8"))
        del data["schema_version"]
        binding_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        result = validate_binding(str(binding_path))
        assert result["valid"] is False
        assert any("schema_version" in e for e in result["errors"])

    def test_project_root_mismatch_fails(self, tmp_path):
        """Binding with wrong project_root fails validation."""
        project = tmp_path / "root-mismatch-project"
        project.mkdir()
        create_scaffold(str(project))
        binding_path = project / ".agent" / "CONVERSATION_BINDING.json"
        data = json.loads(binding_path.read_text(encoding="utf-8"))
        data["project_root"] = "/wrong/path/to/some/other/project"
        binding_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        result = validate_binding(str(binding_path), project_root=str(project))
        assert result["valid"] is False
        assert any("project_root" in e for e in result["errors"])

    def test_bindings_not_array_fails(self, tmp_path):
        """bindings field that is not a list fails validation."""
        project = tmp_path / "bindings-not-array-project"
        project.mkdir()
        create_scaffold(str(project))
        binding_path = project / ".agent" / "CONVERSATION_BINDING.json"
        data = json.loads(binding_path.read_text(encoding="utf-8"))
        data["bindings"] = {"not": "an array"}
        binding_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        result = validate_binding(str(binding_path))
        assert result["valid"] is False
        assert any("array" in e.lower() or "list" in e.lower() for e in result["errors"])

    def test_active_binding_without_chat_url_fails(self, tmp_path):
        """Active status binding without chat_url or conversation_id fails."""
        project = tmp_path / "active-no-url-project"
        project.mkdir()
        create_scaffold(str(project))
        binding_path = project / ".agent" / "CONVERSATION_BINDING.json"
        data = json.loads(binding_path.read_text(encoding="utf-8"))
        # Change the first binding to active without chat_url or conversation_id
        data["bindings"][0]["binding_status"] = "active"
        data["bindings"][0]["chat_url"] = None
        data["bindings"][0]["conversation_id"] = None
        binding_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        result = validate_binding(str(binding_path))
        assert result["valid"] is False
        assert any("chat_url" in e or "conversation_id" in e for e in result["errors"])

    def test_active_binding_with_placeholder_conversation_id_fails(self, tmp_path):
        """Active status cannot use placeholder conversation metadata."""
        project = tmp_path / "active-placeholder-project"
        project.mkdir()
        create_scaffold(str(project))
        binding_path = project / ".agent" / "CONVERSATION_BINDING.json"
        data = json.loads(binding_path.read_text(encoding="utf-8"))
        data["bindings"][0]["binding_status"] = "active"
        data["bindings"][0]["conversation_id"] = "<REPLACE_WITH_CONVERSATION_ID>"
        data["bindings"][0]["chat_url"] = None
        binding_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        result = validate_binding(str(binding_path))
        assert result["valid"] is False
        assert any("real chat_url" in e for e in result["errors"])

    def test_capture_policy_missing_field_fails(self, tmp_path):
        """capture_policy missing must_match_run_id fails validation."""
        project = tmp_path / "capture-missing-project"
        project.mkdir()
        create_scaffold(str(project))
        binding_path = project / ".agent" / "CONVERSATION_BINDING.json"
        data = json.loads(binding_path.read_text(encoding="utf-8"))
        del data["bindings"][0]["capture_policy"]["must_match_run_id"]
        binding_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        result = validate_binding(str(binding_path))
        assert result["valid"] is False
        assert any("must_match_run_id" in e or "capture_policy" in e
                    for e in result["errors"])

    def test_capture_policy_field_false_fails(self, tmp_path):
        """capture_policy field set to false fails validation (must be true)."""
        project = tmp_path / "capture-false-project"
        project.mkdir()
        create_scaffold(str(project))
        binding_path = project / ".agent" / "CONVERSATION_BINDING.json"
        data = json.loads(binding_path.read_text(encoding="utf-8"))
        data["bindings"][0]["capture_policy"]["must_match_run_id"] = False
        binding_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        result = validate_binding(str(binding_path))
        assert result["valid"] is False
        assert any("must_match_run_id" in e or "capture_policy" in e
                    for e in result["errors"])

    def test_pending_manual_binding_allowed_without_url(self, tmp_path):
        """Pending status binding without chat_url or conversation_id is allowed."""
        project = tmp_path / "pending-ok-project"
        project.mkdir()
        create_scaffold(str(project))
        binding_path = project / ".agent" / "CONVERSATION_BINDING.json"
        data = json.loads(binding_path.read_text(encoding="utf-8"))
        data["bindings"][0]["binding_status"] = "pending_manual_binding"
        data["bindings"][0]["chat_url"] = None
        data["bindings"][0]["conversation_id"] = None
        binding_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        result = validate_binding(str(binding_path))
        assert result["valid"] is True, (
            f"Pending binding without chat_url should pass, "
            f"errors: {result.get('errors', [])}"
        )

    def test_duplicate_agent_id_fails(self, tmp_path):
        """Two bindings with the same agent_id fails validation."""
        project = tmp_path / "dup-agent-project"
        project.mkdir()
        create_scaffold(str(project))
        binding_path = project / ".agent" / "CONVERSATION_BINDING.json"
        data = json.loads(binding_path.read_text(encoding="utf-8"))
        # Duplicate the first binding entry
        import copy
        dup_binding = copy.deepcopy(data["bindings"][0])
        data["bindings"].append(dup_binding)
        binding_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        result = validate_binding(str(binding_path))
        assert result["valid"] is False
        assert any("duplicate" in e.lower() or "agent_id" in e
                    for e in result["errors"])

    def test_invalid_binding_status_fails(self, tmp_path):
        """Unknown binding_status value fails validation."""
        project = tmp_path / "bad-status-project"
        project.mkdir()
        create_scaffold(str(project))
        binding_path = project / ".agent" / "CONVERSATION_BINDING.json"
        data = json.loads(binding_path.read_text(encoding="utf-8"))
        data["bindings"][0]["binding_status"] = "unknown_status_value"
        binding_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        result = validate_binding(str(binding_path))
        assert result["valid"] is False
        assert any("binding_status" in e or "status" in e.lower()
                    for e in result["errors"])


# ---------------------------------------------------------------------------
# Tests: R2 — Role field + Schema-based validation
# ---------------------------------------------------------------------------

class TestR2RoleAndSchemaValidation:
    """R2 tests: role field validation and schema-based validation."""

    def test_missing_role_fails(self, tmp_path):
        """Binding without role field fails validation."""
        project = tmp_path / "no-role-project"
        project.mkdir()
        create_scaffold(str(project))
        binding_path = project / ".agent" / "CONVERSATION_BINDING.json"
        data = json.loads(binding_path.read_text(encoding="utf-8"))
        del data["bindings"][0]["role"]
        binding_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        result = validate_binding(str(binding_path))
        assert result["valid"] is False
        assert any("role" in e for e in result["errors"])

    def test_invalid_role_fails(self, tmp_path):
        """Binding with unknown role value fails validation."""
        project = tmp_path / "bad-role-project"
        project.mkdir()
        create_scaffold(str(project))
        binding_path = project / ".agent" / "CONVERSATION_BINDING.json"
        data = json.loads(binding_path.read_text(encoding="utf-8"))
        data["bindings"][0]["role"] = "superadmin"
        binding_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        result = validate_binding(str(binding_path))
        assert result["valid"] is False
        assert any("role" in e and "superadmin" in e for e in result["errors"])

    def test_valid_roles_pass(self, tmp_path):
        """All four allowed roles pass validation."""
        for role in ["reviewer", "executor", "observer", "orchestrator"]:
            project = tmp_path / f"role-{role}-project"
            project.mkdir()
            create_scaffold(str(project))
            binding_path = project / ".agent" / "CONVERSATION_BINDING.json"
            data = json.loads(binding_path.read_text(encoding="utf-8"))
            data["bindings"][0]["role"] = role
            binding_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
            result = validate_binding(str(binding_path))
            assert result["valid"] is True, (
                f"Role '{role}' should pass, errors: {result.get('errors', [])}"
            )

    def test_schema_file_loaded(self, tmp_path):
        """validate_binding loads and uses CONVERSATION_REGISTRY.schema.json."""
        project = tmp_path / "schema-loaded-project"
        project.mkdir()
        create_scaffold(str(project))
        binding_path = project / ".agent" / "CONVERSATION_BINDING.json"
        result = validate_binding(str(binding_path))
        assert result["details"].get("schema_file_loaded") is True

    def test_schema_required_field_missing_detected_by_binding_check(self, tmp_path):
        """Binding missing role field (also schema-required) fails via per-binding check."""
        project = tmp_path / "schema-req-missing-project"
        project.mkdir()
        create_scaffold(str(project))
        binding_path = project / ".agent" / "CONVERSATION_BINDING.json"
        data = json.loads(binding_path.read_text(encoding="utf-8"))
        # Remove 'role' — which is required both by per-binding and schema
        del data["bindings"][0]["role"]
        binding_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        result = validate_binding(str(binding_path))
        assert result["valid"] is False
        assert any("role" in e for e in result["errors"])

    def test_schema_enum_violation_fails(self, tmp_path):
        """Binding with role not in schema enum fails validation."""
        project = tmp_path / "enum-violation-project"
        project.mkdir()
        create_scaffold(str(project))
        binding_path = project / ".agent" / "CONVERSATION_BINDING.json"
        data = json.loads(binding_path.read_text(encoding="utf-8"))
        data["bindings"][0]["role"] = "admin"
        binding_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        result = validate_binding(str(binding_path))
        assert result["valid"] is False
        # Should be caught by both role check and enum check
        assert any("role" in e for e in result["errors"])

    def test_schema_missing_alongside_binding_fails_closed(self, tmp_path):
        """Missing schema file alongside binding fails closed."""
        project = tmp_path / "no-schema-warn-project"
        project.mkdir()
        create_scaffold(str(project))
        schema_path = project / ".agent" / "CONVERSATION_REGISTRY.schema.json"
        schema_path.unlink()
        binding_path = project / ".agent" / "CONVERSATION_BINDING.json"
        result = validate_binding(str(binding_path))
        assert result["valid"] is False
        assert any("schema" in e.lower() for e in result["errors"])

    def test_schema_corrupted_json_fails(self, tmp_path):
        """Corrupted schema JSON file causes schema-related error."""
        project = tmp_path / "corrupt-schema-project"
        project.mkdir()
        create_scaffold(str(project))
        schema_path = project / ".agent" / "CONVERSATION_REGISTRY.schema.json"
        schema_path.write_text("{corrupted!!! not json", encoding="utf-8")
        binding_path = project / ".agent" / "CONVERSATION_BINDING.json"
        result = validate_binding(str(binding_path))
        assert result["valid"] is False
        assert any("CONVERSATION_REGISTRY.schema.json" in e for e in result["errors"])

    def test_schema_missing_required_field_in_schema_file(self, tmp_path):
        """Schema file missing JSON Schema fields ($schema, type, etc.) fails."""
        project = tmp_path / "incomplete-schema-project"
        project.mkdir()
        create_scaffold(str(project))
        schema_path = project / ".agent" / "CONVERSATION_REGISTRY.schema.json"
        # Write a valid JSON but not a real JSON Schema
        schema_path.write_text(
            json.dumps({"schema_version": "1.0.0", "note": "not a real schema"}),
            encoding="utf-8"
        )
        binding_path = project / ".agent" / "CONVERSATION_BINDING.json"
        result = validate_binding(str(binding_path))
        assert result["valid"] is False
        assert any("JSON Schema field" in e for e in result["errors"])

    def test_capture_policy_const_violation_schema(self, tmp_path):
        """capture_policy field violating schema const constraint fails."""
        project = tmp_path / "const-violation-project"
        project.mkdir()
        create_scaffold(str(project))
        binding_path = project / ".agent" / "CONVERSATION_BINDING.json"
        data = json.loads(binding_path.read_text(encoding="utf-8"))
        data["bindings"][0]["capture_policy"]["must_include_end_marker"] = False
        binding_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        result = validate_binding(str(binding_path))
        assert result["valid"] is False
        assert any("must_include_end_marker" in e for e in result["errors"])

    def test_fresh_scaffold_passes_all_r2_checks(self, tmp_path):
        """Fresh scaffold binding passes all R2 validation checks."""
        project = tmp_path / "r2-pass-project"
        project.mkdir()
        create_scaffold(str(project))
        binding_path = project / ".agent" / "CONVERSATION_BINDING.json"
        result = validate_binding(str(binding_path))
        assert result["valid"] is True, (
            f"Fresh scaffold should pass all R2 checks, errors: {result.get('errors', [])}"
        )
        assert result["details"].get("schema_file_loaded") is True


# ---------------------------------------------------------------------------
# Tests: R3 — Full JSON Schema closure + pending binding policy
# ---------------------------------------------------------------------------

class TestR3FullSchemaValidation:
    """R3 tests: complete schema validation and fail-closed behavior."""

    def test_fresh_scaffold_binding_file_passes_real_json_schema(self, tmp_path):
        """Fresh scaffold CONVERSATION_BINDING.json passes Draft 2020-12 validation."""
        project = tmp_path / "r3-fresh-schema-project"
        project.mkdir()
        create_scaffold(str(project))
        agent_dir = project / ".agent"
        binding_data = json.loads(
            (agent_dir / "CONVERSATION_BINDING.json").read_text(encoding="utf-8")
        )
        schema_data = json.loads(
            (agent_dir / "CONVERSATION_REGISTRY.schema.json").read_text(encoding="utf-8")
        )
        validator = Draft202012Validator(schema_data)
        errors = list(validator.iter_errors(binding_data))
        assert errors == []

    def test_binding_missing_top_level_project_id_fails_schema_validation(self, tmp_path):
        """Missing top-level project_id is rejected by full schema validation."""
        project = tmp_path / "r3-missing-project-id"
        project.mkdir()
        create_scaffold(str(project))
        binding_path = project / ".agent" / "CONVERSATION_BINDING.json"
        data = json.loads(binding_path.read_text(encoding="utf-8"))
        data.pop("project_id", None)
        binding_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        result = validate_binding(str(binding_path))
        assert result["valid"] is False
        assert any("project_id" in e for e in result["errors"])

    def test_binding_missing_default_policy_fails_schema_validation(self, tmp_path):
        """Missing default_conversation_policy is rejected by full schema validation."""
        project = tmp_path / "r3-missing-created-at"
        project.mkdir()
        create_scaffold(str(project))
        binding_path = project / ".agent" / "CONVERSATION_BINDING.json"
        data = json.loads(binding_path.read_text(encoding="utf-8"))
        data.pop("default_conversation_policy", None)
        binding_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        result = validate_binding(str(binding_path))
        assert result["valid"] is False
        assert any("default_conversation_policy" in e for e in result["errors"])

    def test_fresh_scaffold_defaults_to_pending_not_active(self, tmp_path):
        """Fresh scaffold must not fabricate an active binding."""
        project = tmp_path / "r3-no-active-binding"
        project.mkdir()
        create_scaffold(str(project))
        binding_path = project / ".agent" / "CONVERSATION_BINDING.json"
        data = json.loads(binding_path.read_text(encoding="utf-8"))
        result = validate_binding(str(binding_path))
        assert result["valid"] is True, result["errors"]
        assert result["summary"]["active_count"] == 0
        assert result["summary"]["pending_count"] == 1
        assert data["bindings"][0]["binding_status"] == "pending_manual_binding"
        assert data["bindings"][0]["conversation_id"] is None
        assert data["bindings"][0]["chat_url"] is None

    def test_schema_binding_field_mismatch_fails(self, tmp_path):
        """A schema-required top-level field missing from the binding is rejected."""
        project = tmp_path / "r3-schema-binding-mismatch"
        project.mkdir()
        create_scaffold(str(project))
        agent_dir = project / ".agent"
        schema_path = agent_dir / "CONVERSATION_REGISTRY.schema.json"
        schema_data = json.loads(schema_path.read_text(encoding="utf-8"))
        schema_data["required"].append("review_channel")
        schema_data["properties"]["review_channel"] = {"type": "string"}
        schema_path.write_text(json.dumps(schema_data, indent=2), encoding="utf-8")
        result = validate_binding(str(agent_dir / "CONVERSATION_BINDING.json"))
        assert result["valid"] is False
        assert any("review_channel" in e for e in result["errors"])

    def test_complete_valid_binding_passes(self, tmp_path):
        """A complete legal binding passes validator and real schema validation."""
        project = tmp_path / "r3-complete-valid-binding"
        project.mkdir()
        create_scaffold(str(project))
        binding_path = project / ".agent" / "CONVERSATION_BINDING.json"
        result = validate_binding(str(binding_path), project_root=str(project))
        assert result["valid"] is True, result["errors"]
        assert result["details"].get("schema_validation") == "passed"

    def test_top_level_bindings_not_array_fails_schema_validation(self, tmp_path):
        """The whole-file schema rejects bindings that are not an array."""
        project = tmp_path / "r3-bindings-not-array"
        project.mkdir()
        create_scaffold(str(project))
        binding_path = project / ".agent" / "CONVERSATION_BINDING.json"
        data = json.loads(binding_path.read_text(encoding="utf-8"))
        data["bindings"] = {"agent_id": "not-an-array"}
        binding_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        result = validate_binding(str(binding_path))
        assert result["valid"] is False
        assert any(
            "bindings" in e or "array" in e.lower() or "list" in e.lower()
            for e in result["errors"]
        )


# ---------------------------------------------------------------------------
# Tests: External runtime governance scope
# ---------------------------------------------------------------------------

class TestExternalRuntimeGovernanceScope:
    """Tests for dev-frame/opencode/paper governance boundaries."""

    REQUIRED_RUNTIME_IDS = {
        "devframe-control-plane",
        "dev-frame-opencode",
        "paper-workflow",
    }

    def test_fresh_scaffold_declares_external_runtime_governance(self, tmp_path):
        """Fresh scaffold records the three governed external runtimes."""
        project = tmp_path / "governance-scope-scaffold"
        project.mkdir()
        create_scaffold(str(project))
        binding_path = project / ".agent" / "CONVERSATION_BINDING.json"
        data = json.loads(binding_path.read_text(encoding="utf-8"))
        scope = data["governance_scope"]
        assert scope["default_execution_policy"] == (
            "human_gated_for_external_runtime_execution"
        )
        assert scope["forbid_ad_hoc_gpt_submission"] is True
        assert scope["forbid_cross_repo_smoke_without_human_gate"] is True
        runtime_ids = {
            item["runtime_id"] for item in scope["external_runtimes"]
        }
        assert runtime_ids == self.REQUIRED_RUNTIME_IDS

    def test_missing_governance_scope_fails_validation(self, tmp_path):
        """The whole-file schema and validator require governance_scope."""
        project = tmp_path / "missing-governance-scope"
        project.mkdir()
        create_scaffold(str(project))
        binding_path = project / ".agent" / "CONVERSATION_BINDING.json"
        data = json.loads(binding_path.read_text(encoding="utf-8"))
        data.pop("governance_scope", None)
        binding_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        result = validate_binding(str(binding_path), project_root=str(project))
        assert result["valid"] is False
        assert any("governance_scope" in e for e in result["errors"])

    def test_missing_opencode_runtime_fails_validation(self, tmp_path):
        """dev-frame-opencode must be explicitly governed before pilot use."""
        project = tmp_path / "missing-opencode-runtime"
        project.mkdir()
        create_scaffold(str(project))
        binding_path = project / ".agent" / "CONVERSATION_BINDING.json"
        data = json.loads(binding_path.read_text(encoding="utf-8"))
        data["governance_scope"]["external_runtimes"] = [
            runtime for runtime in data["governance_scope"]["external_runtimes"]
            if runtime["runtime_id"] != "dev-frame-opencode"
        ]
        binding_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        result = validate_binding(str(binding_path), project_root=str(project))
        assert result["valid"] is False
        assert any("dev-frame-opencode" in e for e in result["errors"])

    def test_external_runtime_human_gate_required(self, tmp_path):
        """External runtime execution boundaries must remain human-gated."""
        project = tmp_path / "runtime-human-gate"
        project.mkdir()
        create_scaffold(str(project))
        binding_path = project / ".agent" / "CONVERSATION_BINDING.json"
        data = json.loads(binding_path.read_text(encoding="utf-8"))
        data["governance_scope"]["external_runtimes"][0][
            "human_gate_required"
        ] = False
        binding_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        result = validate_binding(str(binding_path), project_root=str(project))
        assert result["valid"] is False
        assert any("human_gate_required" in e for e in result["errors"])


# ---------------------------------------------------------------------------
# Tests: Multi-agent / multi-GPT pilot plan
# ---------------------------------------------------------------------------

class TestMultiAgentPilotPlan:
    """Tests for the pilot preparation document."""

    def test_pilot_plan_exists(self):
        """Pilot plan document exists."""
        plan_path = Path(__file__).resolve().parent.parent / "docs" / (
            "MULTI_AGENT_MULTI_GPT_PILOT_PLAN.md"
        )
        assert plan_path.exists()

    def test_pilot_plan_forbids_last_message_only_capture(self):
        """Pilot plan forbids last-message-only capture."""
        plan_path = Path(__file__).resolve().parent.parent / "docs" / (
            "MULTI_AGENT_MULTI_GPT_PILOT_PLAN.md"
        )
        content = plan_path.read_text(encoding="utf-8")
        assert "forbid_last_message_only_capture" in content
        assert "last assistant message" in content

    def test_pilot_plan_requires_one_agent_one_conversation(self):
        """Pilot plan requires one agent per conversation."""
        plan_path = Path(__file__).resolve().parent.parent / "docs" / (
            "MULTI_AGENT_MULTI_GPT_PILOT_PLAN.md"
        )
        content = plan_path.read_text(encoding="utf-8")
        assert "one_agent_one_conversation" in content
        assert "one agent bound to one conversation" in content

    def test_pilot_plan_marks_missing_chat_url_as_pending(self):
        """Pilot plan keeps missing conversation metadata pending, not active."""
        plan_path = Path(__file__).resolve().parent.parent / "docs" / (
            "MULTI_AGENT_MULTI_GPT_PILOT_PLAN.md"
        )
        content = plan_path.read_text(encoding="utf-8")
        assert '"binding_status": "pending_manual_binding"' in content
        assert '"chat_url": null' in content
        assert "Do not report `pending_manual_binding` as `active`" in content

    def test_pilot_plan_declares_runtime_governance_preflight(self):
        """Pilot plan includes dev-frame/opencode/paper governance preflight."""
        plan_path = Path(__file__).resolve().parent.parent / "docs" / (
            "MULTI_AGENT_MULTI_GPT_PILOT_PLAN.md"
        )
        content = plan_path.read_text(encoding="utf-8")
        assert "devframe-control-plane" in content
        assert "dev-frame-opencode" in content
        assert "paper-workflow" in content
        assert "human_gated_for_external_runtime_execution" in content
        assert "capability-inventory.md" in content
        assert "tool-policy.md" in content
