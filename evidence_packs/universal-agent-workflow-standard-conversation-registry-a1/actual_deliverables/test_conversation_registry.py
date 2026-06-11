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
from jsonschema import Draft7Validator

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
        """Pending status binding without chat_url is allowed if another binding is active."""
        project = tmp_path / "pending-ok-project"
        project.mkdir()
        create_scaffold(str(project))
        binding_path = project / ".agent" / "CONVERSATION_BINDING.json"
        data = json.loads(binding_path.read_text(encoding="utf-8"))
        active_binding = dict(data["bindings"][0])
        active_binding["agent_id"] = "active-agent"
        active_binding["binding_status"] = "active"
        active_binding["conversation_id"] = "active-conversation"
        # Ensure pending_manual_binding status with null chat_url can coexist
        # with an active binding.
        data["bindings"][0]["binding_status"] = "pending_manual_binding"
        data["bindings"][0]["chat_url"] = None
        data["bindings"].append(active_binding)
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
# Tests: R3 — Full JSON Schema closure + active binding policy
# ---------------------------------------------------------------------------

class TestR3FullSchemaValidation:
    """R3 tests: complete schema validation and fail-closed behavior."""

    def test_fresh_scaffold_entries_pass_real_json_schema(self, tmp_path):
        """Fresh scaffold binding entries pass Draft7 validation."""
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
        validator = Draft7Validator(schema_data)
        errors = []
        for entry in binding_data["bindings"]:
            errors.extend(validator.iter_errors(entry))
        assert errors == []

    def test_binding_missing_project_id_fails_schema_validation(self, tmp_path):
        """Missing project_id is rejected by full schema validation."""
        project = tmp_path / "r3-missing-project-id"
        project.mkdir()
        create_scaffold(str(project))
        binding_path = project / ".agent" / "CONVERSATION_BINDING.json"
        data = json.loads(binding_path.read_text(encoding="utf-8"))
        data["bindings"][0].pop("project_id", None)
        binding_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        result = validate_binding(str(binding_path))
        assert result["valid"] is False
        assert any("project_id" in e for e in result["errors"])

    def test_binding_missing_created_at_fails_schema_validation(self, tmp_path):
        """Missing created_at is rejected by full schema validation."""
        project = tmp_path / "r3-missing-created-at"
        project.mkdir()
        create_scaffold(str(project))
        binding_path = project / ".agent" / "CONVERSATION_BINDING.json"
        data = json.loads(binding_path.read_text(encoding="utf-8"))
        data["bindings"][0].pop("created_at", None)
        binding_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        result = validate_binding(str(binding_path))
        assert result["valid"] is False
        assert any("created_at" in e for e in result["errors"])

    def test_no_active_binding_fails(self, tmp_path):
        """At least one binding must be active."""
        project = tmp_path / "r3-no-active-binding"
        project.mkdir()
        create_scaffold(str(project))
        binding_path = project / ".agent" / "CONVERSATION_BINDING.json"
        data = json.loads(binding_path.read_text(encoding="utf-8"))
        for entry in data["bindings"]:
            entry["binding_status"] = "pending_manual_binding"
        binding_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        result = validate_binding(str(binding_path))
        assert result["valid"] is False
        assert any("active" in e.lower() for e in result["errors"])

    def test_schema_binding_field_mismatch_fails(self, tmp_path):
        """A schema-required field missing from the binding is rejected."""
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
