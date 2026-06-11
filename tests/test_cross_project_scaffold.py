#!/usr/bin/env python3
"""test_cross_project_scaffold.py — Tests for AWSP v1.2.0 cross-project features.

Covers:
1. validate_run_id_consistency parameterization (config with evidence_pack_dir)
2. Prompt-template validation (END_OF_GPT_RESPONSE marker, overall_judgment field)
3. awsp_scaffold.py (create and validate scaffold, including .agent/ governance)
"""

import json
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))

from validate_run_id_consistency import validate_run_id_consistency
from awsp_scaffold import create_scaffold, validate_scaffold, AWSP_DIRECTORIES


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _setup_full_consistent(tmp_path, run_id="TEST_TASK_A1_20260609T120000_RD"):
    """Helper: create a fully consistent set of artifacts (AWSP v1.1.0)."""
    report_dir = tmp_path / "test-task-a1"
    report_dir.mkdir()

    (report_dir / "run_id.txt").write_text(run_id, encoding="utf-8")
    (report_dir / "R1_RUN_ID.txt").write_text(run_id, encoding="utf-8")
    (report_dir / "GPT_REVIEW_PROMPT.md").write_text(
        "## Review " + "{{TASK_ID}}" + "\nrun_id: " + "{{RUN_ID}}"
        + "\noverall_judgment: accepted\n---END_OF_GPT_RESPONSE---\n",
        encoding="utf-8",
    )

    # Create evidence pack dir and zip
    pack_dir = tmp_path / "evidence_packs" / "test-task-a1"
    pack_dir.mkdir(parents=True, exist_ok=True)
    (pack_dir / f"{run_id}.zip").write_bytes(b"PK")

    # Create PACK_MANIFEST.md with run_id
    manifest = f"# PACK_MANIFEST\n\n| Field | Value |\n|-------|-------|\n| run_id | {run_id} |\n"
    (pack_dir / "PACK_MANIFEST.md").write_text(manifest, encoding="utf-8")

    return report_dir, run_id


# ---------------------------------------------------------------------------
# Tests: Cross-project parameterization
# ---------------------------------------------------------------------------

class TestCrossProjectParameterization:
    """Tests for config-based evidence_pack_dir parameterization."""

    def test_explicit_evidence_pack_dir(self, tmp_path):
        """Config with explicit evidence_pack_dir finds the pack."""
        report_dir, run_id = _setup_full_consistent(tmp_path)
        # Use explicit path instead of default multi-level search
        config = {"evidence_pack_dir": str(tmp_path / "evidence_packs" / "test-task-a1")}
        result = validate_run_id_consistency(str(report_dir), config=config)
        assert result["consistent"] is True
        assert result["details"].get("evidence_pack_dir_source") == "config"

    def test_explicit_evidence_pack_dir_not_found(self, tmp_path):
        """Config with non-existent evidence_pack_dir fails."""
        report_dir, run_id = _setup_full_consistent(tmp_path)
        config = {"evidence_pack_dir": str(tmp_path / "nonexistent" / "pack")}
        result = validate_run_id_consistency(str(report_dir), config=config)
        assert result["consistent"] is False
        assert any("does not exist" in e for e in result["errors"])

    def test_cross_project_layout(self, tmp_path):
        """Validator works with non-standard directory layout via config."""
        # Create a non-standard layout: project/tasks/TASK-A1/ and project/packs/TASK-A1/
        project = tmp_path / "my-project"
        project.mkdir()
        tasks_dir = project / "tasks" / "task-a1"
        tasks_dir.mkdir(parents=True)
        packs_dir = project / "packs" / "task-a1"
        packs_dir.mkdir(parents=True)

        run_id = "TASK_A1_20260609T120000_RD"
        (tasks_dir / "run_id.txt").write_text(run_id, encoding="utf-8")
        (tasks_dir / "GPT_REVIEW_PROMPT.md").write_text(
            "Review " + "{{TASK_ID}}" + "\nrun_id: " + "{{RUN_ID}}"
            + "\noverall_judgment: accepted\n---END_OF_GPT_RESPONSE---\n",
            encoding="utf-8",
        )
        (packs_dir / f"{run_id}.zip").write_bytes(b"PK")
        manifest = f"# PACK_MANIFEST\n\n| Field | Value |\n|-------|-------|\n| run_id | {run_id} |\n"
        (packs_dir / "PACK_MANIFEST.md").write_text(manifest, encoding="utf-8")

        config = {"evidence_pack_dir": str(packs_dir)}
        result = validate_run_id_consistency(str(tasks_dir), config=config)
        assert result["consistent"] is True


# ---------------------------------------------------------------------------
# Tests: Prompt-template validation (AWSP v1.1.0)
# ---------------------------------------------------------------------------

class TestPromptTemplateValidation:
    """Tests for AWSP v1.1.0 prompt-template checks."""

    def test_missing_end_marker(self, tmp_path):
        """Prompt without END_OF_GPT_RESPONSE marker fails."""
        report_dir, run_id = _setup_full_consistent(tmp_path)
        (report_dir / "GPT_REVIEW_PROMPT.md").write_text(
            "## Review " + "{{TASK_ID}}" + "\nrun_id: " + "{{RUN_ID}}"
            + "\noverall_judgment: accepted\n",
            encoding="utf-8",
        )
        result = validate_run_id_consistency(str(report_dir))
        assert result["consistent"] is False
        assert any("END_OF_GPT_RESPONSE" in e for e in result["errors"])

    def test_missing_overall_judgment(self, tmp_path):
        """Prompt without overall_judgment: field fails."""
        report_dir, run_id = _setup_full_consistent(tmp_path)
        (report_dir / "GPT_REVIEW_PROMPT.md").write_text(
            "## Review " + "{{TASK_ID}}" + "\nrun_id: " + "{{RUN_ID}}"
            + "\n---END_OF_GPT_RESPONSE---\n",
            encoding="utf-8",
        )
        result = validate_run_id_consistency(str(report_dir))
        assert result["consistent"] is False
        assert any("overall_judgment" in e for e in result["errors"])

    def test_verdict_instead_of_overall_judgment(self, tmp_path):
        """Prompt using verdict: without overall_judgment: fails."""
        report_dir, run_id = _setup_full_consistent(tmp_path)
        (report_dir / "GPT_REVIEW_PROMPT.md").write_text(
            "## Review " + "{{TASK_ID}}" + "\nrun_id: " + "{{RUN_ID}}"
            + "\nverdict: accepted\n---END_OF_GPT_RESPONSE---\n",
            encoding="utf-8",
        )
        result = validate_run_id_consistency(str(report_dir))
        assert result["consistent"] is False
        assert any("overall_judgment" in e for e in result["errors"])

    def test_full_compliant_prompt(self, tmp_path):
        """Fully AWSP v1.1.0 compliant prompt passes all checks."""
        report_dir, run_id = _setup_full_consistent(tmp_path)
        # The helper already creates a compliant prompt
        result = validate_run_id_consistency(str(report_dir))
        assert result["consistent"] is True
        assert result["details"]["prompt_has_end_marker"] is True
        assert result["details"]["prompt_has_overall_judgment"] is True


# ---------------------------------------------------------------------------
# Tests: AWSP scaffold
# ---------------------------------------------------------------------------

class TestAWSPScaffold:
    """Tests for awsp_scaffold.py create and validate functions."""

    def test_create_scaffold(self, tmp_path):
        """create_scaffold creates all required directories and files."""
        project = tmp_path / "new-project"
        project.mkdir()
        result = create_scaffold(str(project))
        assert len(result["errors"]) == 0
        for d in AWSP_DIRECTORIES:
            assert (project / d).exists()
            assert (project / d).is_dir()
        assert (project / ".awsp.json").exists()
        assert (project / "docs" / "AGENT_WORKFLOW_STANDARD.md").exists()

    def test_create_scaffold_dry_run(self, tmp_path):
        """Dry run previews without creating files."""
        project = tmp_path / "dry-project"
        project.mkdir()
        result = create_scaffold(str(project), dry_run=True)
        assert len(result["errors"]) == 0
        assert len(result["created"]) > 0
        # Files should NOT exist after dry run
        for d in AWSP_DIRECTORIES:
            assert not (project / d).exists()

    def test_validate_valid_scaffold(self, tmp_path):
        """validate_scaffold passes on a correctly scaffolded project."""
        project = tmp_path / "valid-project"
        project.mkdir()
        create_scaffold(str(project))
        result = validate_scaffold(str(project))
        assert result["valid"] is True
        assert result["errors"] == []

    def test_validate_missing_dirs(self, tmp_path):
        """validate_scaffold fails when directories are missing."""
        project = tmp_path / "incomplete-project"
        project.mkdir()
        # Only create some directories
        (project / "docs").mkdir()
        (project / "scripts").mkdir()
        result = validate_scaffold(str(project))
        assert result["valid"] is False
        assert any("Missing AWSP directories" in e for e in result["errors"])

    def test_validate_missing_config(self, tmp_path):
        """validate_scaffold fails when .awsp.json is missing."""
        project = tmp_path / "no-config-project"
        project.mkdir()
        for d in AWSP_DIRECTORIES:
            (project / d).mkdir()
        (project / "docs" / "AGENT_WORKFLOW_STANDARD.md").write_text("# AWSP", encoding="utf-8")
        result = validate_scaffold(str(project))
        assert result["valid"] is False
        assert any(".awsp.json" in e for e in result["errors"])

    def test_scaffold_config_content(self, tmp_path):
        """Generated .awsp.json contains correct AWSP version and project root."""
        project = tmp_path / "config-project"
        project.mkdir()
        create_scaffold(str(project))
        config = json.loads((project / ".awsp.json").read_text(encoding="utf-8"))
        assert config["awsp_version"] == "1.3.0"
        # Config stores POSIX-style paths (forward slashes)
        assert config["project_root"] == str(project).replace("\\", "/")
        assert "directories" in config
        assert "validation" in config
        assert config["validation"]["require_run_id_consistency"] is True

    def test_scaffold_force_overwrite(self, tmp_path):
        """Force mode overwrites existing template files."""
        project = tmp_path / "force-project"
        project.mkdir()
        create_scaffold(str(project))
        # Modify config file
        config_path = project / ".awsp.json"
        config_path.write_text("modified", encoding="utf-8")
        # Force recreate
        create_scaffold(str(project), force=True)
        config = json.loads(config_path.read_text(encoding="utf-8"))
        assert config["awsp_version"] == "1.3.0"

    def test_create_scaffold_nonexistent_root(self, tmp_path):
        """create_scaffold fails when project root doesn't exist."""
        result = create_scaffold(str(tmp_path / "nonexistent"))
        assert len(result["errors"]) > 0
        assert "does not exist" in result["errors"][0]


class TestValidateScaffoldContent:
    """Tests for validate_scaffold .awsp.json content checks."""

    def test_valid_scaffold_passes(self, tmp_path):
        """A properly scaffolded project passes validation."""
        create_scaffold(str(tmp_path))
        result = validate_scaffold(str(tmp_path))
        assert result["valid"] is True
        assert result["errors"] == []

    def test_version_mismatch_fails(self, tmp_path):
        """Mismatched awsp_version in .awsp.json fails validation."""
        create_scaffold(str(tmp_path))
        config_path = tmp_path / ".awsp.json"
        config = json.loads(config_path.read_text(encoding="utf-8"))
        config["awsp_version"] = "0.0.1"
        config_path.write_text(json.dumps(config), encoding="utf-8")
        result = validate_scaffold(str(tmp_path))
        assert result["valid"] is False
        assert any("mismatch" in e for e in result["errors"])

    def test_missing_config_fields_fails(self, tmp_path):
        """Missing required fields in .awsp.json fails validation."""
        create_scaffold(str(tmp_path))
        config_path = tmp_path / ".awsp.json"
        # Write config with missing fields
        config_path.write_text('{"awsp_version": "1.1.0"}', encoding="utf-8")
        result = validate_scaffold(str(tmp_path))
        assert result["valid"] is False
        assert any("missing required fields" in e for e in result["errors"])

    def test_missing_validation_section_fails(self, tmp_path):
        """Missing validation config keys in .awsp.json fails validation."""
        create_scaffold(str(tmp_path))
        config_path = tmp_path / ".awsp.json"
        config = json.loads(config_path.read_text(encoding="utf-8"))
        config["validation"] = {}
        config_path.write_text(json.dumps(config), encoding="utf-8")
        result = validate_scaffold(str(tmp_path))
        assert result["valid"] is False
        assert any("validation section missing" in e for e in result["errors"])

    def test_false_validation_values_fails(self, tmp_path):
        """Validation values set to false should fail validation (fail-closed)."""
        create_scaffold(str(tmp_path))
        config_path = tmp_path / ".awsp.json"
        config = json.loads(config_path.read_text(encoding="utf-8"))
        config["validation"]["require_run_id_consistency"] = False
        config["validation"]["require_evidence_pack"] = False
        config_path.write_text(json.dumps(config), encoding="utf-8")
        result = validate_scaffold(str(tmp_path))
        assert result["valid"] is False
        assert any("not all true" in e for e in result["errors"])

    def test_directories_mismatch_fails(self, tmp_path):
        """directories field not matching AWSP_DIRECTORIES fails validation."""
        create_scaffold(str(tmp_path))
        config_path = tmp_path / ".awsp.json"
        config = json.loads(config_path.read_text(encoding="utf-8"))
        config["directories"] = ["only_one_dir"]
        config_path.write_text(json.dumps(config), encoding="utf-8")
        result = validate_scaffold(str(tmp_path))
        assert result["valid"] is False
        assert any("directories field mismatch" in e for e in result["errors"])


class TestStrictVerdictCheck:
    """Tests for strict verdict field checking in validate_run_id_consistency."""

    def test_bare_verdict_with_overall_judgment_fails(self, tmp_path):
        """Prompt with both overall_judgment and bare verdict: should fail."""
        report_dir, run_id = _setup_full_consistent(tmp_path)
        # Overwrite prompt with both overall_judgment and bare verdict
        (report_dir / "GPT_REVIEW_PROMPT.md").write_text(
            "## Review " + "{{TASK_ID}}" + "\nrun_id: " + "{{RUN_ID}}"
            + "\noverall_judgment: accepted\nverdict: accepted\n"
            + "---END_OF_GPT_RESPONSE---\n",
            encoding="utf-8",
        )
        result = validate_run_id_consistency(str(report_dir))
        assert result["consistent"] is False
        assert any("bare verdict:" in e for e in result["errors"])

    def test_overall_judgment_only_passes(self, tmp_path):
        """Prompt with only overall_judgment (no bare verdict) passes."""
        report_dir, run_id = _setup_full_consistent(tmp_path)
        result = validate_run_id_consistency(str(report_dir))
        assert result["consistent"] is True
        assert result["details"]["prompt_has_bare_verdict"] is False

    def test_indented_verdict_fails(self, tmp_path):
        """Indented verdict: (with leading whitespace) should still be caught."""
        report_dir, run_id = _setup_full_consistent(tmp_path)
        (report_dir / "GPT_REVIEW_PROMPT.md").write_text(
            "## Review " + "{{TASK_ID}}" + "\nrun_id: " + "{{RUN_ID}}"
            + "\noverall_judgment: accepted\n  verdict: accepted\n"
            + "---END_OF_GPT_RESPONSE---\n",
            encoding="utf-8",
        )
        result = validate_run_id_consistency(str(report_dir))
        assert result["consistent"] is False
        assert any("bare verdict:" in e for e in result["errors"])


# ---------------------------------------------------------------------------
# Tests: AWSP v1.2.0 .agent/ governance components
# ---------------------------------------------------------------------------

class TestAgentConfigScaffold:
    """Tests for .agent/ governance config directory generation (v1.2.0)."""

    def test_agent_directory_created(self, tmp_path):
        """create_scaffold creates .agent/ directory."""
        project = tmp_path / "agent-config-project"
        project.mkdir()
        create_scaffold(str(project))
        assert (project / ".agent").exists()
        assert (project / ".agent").is_dir()

    def test_agent_config_files_generated(self, tmp_path):
        """create_scaffold generates all 4 .agent/ config files."""
        project = tmp_path / "agent-files-project"
        project.mkdir()
        create_scaffold(str(project))
        expected_files = [
            ".agent/REQUIRED_READS.json",
            ".agent/PROJECT_AGENT_CONFIG.json",
            ".agent/GATE_CONFIG.json",
            ".agent/startup_proof_template.json",
        ]
        for f in expected_files:
            assert (project / f).exists(), f"Missing: {f}"
            # Verify valid JSON
            data = json.loads((project / f).read_text(encoding="utf-8"))
            assert "schema_version" in data, f"{f} missing schema_version"

    def test_agent_config_has_correct_awsp_version(self, tmp_path):
        """Agent config files reference correct AWSP version."""
        project = tmp_path / "version-check-project"
        project.mkdir()
        create_scaffold(str(project))
        config = json.loads(
            (project / ".agent" / "PROJECT_AGENT_CONFIG.json").read_text(encoding="utf-8")
        )
        assert config["awsp_version"] == "1.3.0"

    def test_gate_config_has_required_gates(self, tmp_path):
        """GATE_CONFIG.json defines startup, pre-task, and pre-GPT gates."""
        project = tmp_path / "gate-config-project"
        project.mkdir()
        create_scaffold(str(project))
        gate_config = json.loads(
            (project / ".agent" / "GATE_CONFIG.json").read_text(encoding="utf-8")
        )
        assert "gates" in gate_config
        assert "startup_read_gate" in gate_config["gates"]
        assert "pre_task_gate" in gate_config["gates"]
        assert "pre_gpt_review_gate" in gate_config["gates"]

    def test_project_agent_config_governance_flags(self, tmp_path):
        """PROJECT_AGENT_CONFIG.json has all governance enforcement flags."""
        project = tmp_path / "governance-flags-project"
        project.mkdir()
        create_scaffold(str(project))
        config = json.loads(
            (project / ".agent" / "PROJECT_AGENT_CONFIG.json").read_text(encoding="utf-8")
        )
        gov = config["governance"]
        assert gov["enforce_startup_read_gate"] is True
        assert gov["enforce_pre_task_gate"] is True
        assert gov["enforce_pre_gpt_review_gate"] is True
        assert gov["enforce_state_machine"] is True
        assert gov["enforce_human_required_decision_record"] is True


class TestValidateAgentConfig:
    """Tests for validate_scaffold .agent/ governance checks (v1.2.0)."""

    def test_valid_scaffold_with_agent_config_passes(self, tmp_path):
        """A properly scaffolded project with .agent/ passes validation."""
        create_scaffold(str(tmp_path))
        result = validate_scaffold(str(tmp_path))
        assert result["valid"] is True

    def test_missing_agent_files_fails(self, tmp_path):
        """Missing .agent/ governance files fails validation."""
        create_scaffold(str(tmp_path))
        # Remove .agent/ config files
        import shutil
        agent_dir = tmp_path / ".agent"
        if agent_dir.exists():
            shutil.rmtree(str(agent_dir))
        agent_dir.mkdir()  # Keep dir but remove files
        result = validate_scaffold(str(tmp_path))
        assert result["valid"] is False
        assert any(".agent/" in e or "governance config" in e for e in result["errors"])

    def test_project_root_mismatch_fails(self, tmp_path):
        """Mismatched project_root in .awsp.json fails validation."""
        create_scaffold(str(tmp_path))
        config_path = tmp_path / ".awsp.json"
        config = json.loads(config_path.read_text(encoding="utf-8"))
        config["project_root"] = "/wrong/path/project"
        config_path.write_text(json.dumps(config), encoding="utf-8")
        result = validate_scaffold(str(tmp_path))
        assert result["valid"] is False
        assert any("project_root mismatch" in e for e in result["errors"])

    def test_agent_config_invalid_json_fails(self, tmp_path):
        """Invalid JSON in .agent/ config file fails validation."""
        create_scaffold(str(tmp_path))
        # Corrupt a .agent/ config file
        gate_path = tmp_path / ".agent" / "GATE_CONFIG.json"
        gate_path.write_text("not valid json{{{", encoding="utf-8")
        result = validate_scaffold(str(tmp_path))
        assert result["valid"] is False
        assert any("GATE_CONFIG.json" in e for e in result["errors"])

    def test_agent_config_missing_schema_version_fails(self, tmp_path):
        """Config file without schema_version field fails validation."""
        create_scaffold(str(tmp_path))
        reads_path = tmp_path / ".agent" / "REQUIRED_READS.json"
        data = json.loads(reads_path.read_text(encoding="utf-8"))
        del data["schema_version"]
        reads_path.write_text(json.dumps(data), encoding="utf-8")
        result = validate_scaffold(str(tmp_path))
        assert result["valid"] is False
        assert any("schema_version" in e for e in result["errors"])

    def test_awsp_directories_includes_agent(self):
        """AWSP_DIRECTORIES includes .agent/ (v1.2.0)."""
        assert ".agent" in AWSP_DIRECTORIES


class TestR2AgentConfigContentValidation:
    """R2 tests: resolved path fix and .agent/ content validation."""

    def test_scaffold_resolves_relative_path(self, tmp_path):
        """create_scaffold stores resolved absolute path even with relative input."""
        import os
        project = tmp_path / "relative-test-project"
        project.mkdir()
        # Use a relative path by cd-ing to parent and using relative name
        old_cwd = os.getcwd()
        try:
            os.chdir(str(tmp_path))
            create_scaffold("relative-test-project")
        finally:
            os.chdir(old_cwd)
        config = json.loads(
            (project / ".awsp.json").read_text(encoding="utf-8")
        )
        # The stored project_root should be absolute (resolved)
        stored_root = config["project_root"]
        assert os.path.isabs(stored_root) or "/" in stored_root
        # Validation should pass with the stored absolute path
        result = validate_scaffold(str(project))
        assert result["valid"] is True

    def test_project_agent_config_version_mismatch_fails(self, tmp_path):
        """PROJECT_AGENT_CONFIG with wrong awsp_version fails validation."""
        create_scaffold(str(tmp_path))
        config_path = tmp_path / ".agent" / "PROJECT_AGENT_CONFIG.json"
        data = json.loads(config_path.read_text(encoding="utf-8"))
        data["awsp_version"] = "0.0.1"
        config_path.write_text(json.dumps(data), encoding="utf-8")
        result = validate_scaffold(str(tmp_path))
        assert result["valid"] is False
        assert any("PROJECT_AGENT_CONFIG.json awsp_version" in e for e in result["errors"])

    def test_project_agent_config_missing_awsp_version_fails(self, tmp_path):
        """PROJECT_AGENT_CONFIG without awsp_version field fails validation (fail-closed)."""
        create_scaffold(str(tmp_path))
        config_path = tmp_path / ".agent" / "PROJECT_AGENT_CONFIG.json"
        data = json.loads(config_path.read_text(encoding="utf-8"))
        del data["awsp_version"]
        config_path.write_text(json.dumps(data), encoding="utf-8")
        result = validate_scaffold(str(tmp_path))
        assert result["valid"] is False
        assert any("missing required field: awsp_version" in e for e in result["errors"])

    def test_missing_governance_flags_fails(self, tmp_path):
        """PROJECT_AGENT_CONFIG missing governance flags fails validation."""
        create_scaffold(str(tmp_path))
        config_path = tmp_path / ".agent" / "PROJECT_AGENT_CONFIG.json"
        data = json.loads(config_path.read_text(encoding="utf-8"))
        # Remove a governance flag
        del data["governance"]["enforce_state_machine"]
        config_path.write_text(json.dumps(data), encoding="utf-8")
        result = validate_scaffold(str(tmp_path))
        assert result["valid"] is False
        assert any("governance flags" in e for e in result["errors"])

    def test_missing_gates_in_gate_config_fails(self, tmp_path):
        """GATE_CONFIG missing required gates fails validation."""
        create_scaffold(str(tmp_path))
        gate_path = tmp_path / ".agent" / "GATE_CONFIG.json"
        data = json.loads(gate_path.read_text(encoding="utf-8"))
        del data["gates"]["pre_task_gate"]
        gate_path.write_text(json.dumps(data), encoding="utf-8")
        result = validate_scaffold(str(tmp_path))
        assert result["valid"] is False
        assert any("missing required gates" in e for e in result["errors"])

    def test_missing_required_reads_array_fails(self, tmp_path):
        """REQUIRED_READS without required_reads array fails validation."""
        create_scaffold(str(tmp_path))
        reads_path = tmp_path / ".agent" / "REQUIRED_READS.json"
        data = json.loads(reads_path.read_text(encoding="utf-8"))
        del data["required_reads"]
        reads_path.write_text(json.dumps(data), encoding="utf-8")
        result = validate_scaffold(str(tmp_path))
        assert result["valid"] is False
        assert any("required_reads" in e for e in result["errors"])

    def test_self_validation_after_create_scaffold(self, tmp_path):
        """A freshly scaffolded project passes its own validate_scaffold()."""
        project = tmp_path / "self-validate-project"
        project.mkdir()
        create_scaffold(str(project))
        result = validate_scaffold(str(project))
        assert result["valid"] is True, f"Self-validation failed: {result['errors']}"


# ---------------------------------------------------------------------------
# Tests: STRICT-VALIDATION-A1 — deep boolean & structure checks
# ---------------------------------------------------------------------------

class TestStrictValidation:
    """Strict validation: governance boolean, gate config, required_reads structure."""

    def test_governance_flag_false_fails(self, tmp_path):
        """Governance flag set to false fails validation (fail-closed)."""
        create_scaffold(str(tmp_path))
        config_path = tmp_path / ".agent" / "PROJECT_AGENT_CONFIG.json"
        data = json.loads(config_path.read_text(encoding="utf-8"))
        data["governance"]["enforce_state_machine"] = False
        config_path.write_text(json.dumps(data), encoding="utf-8")
        result = validate_scaffold(str(tmp_path))
        assert result["valid"] is False
        assert any("governance flags not all true" in e for e in result["errors"])

    def test_gate_enabled_false_fails(self, tmp_path):
        """Gate with enabled=false fails validation (fail-closed)."""
        create_scaffold(str(tmp_path))
        gate_path = tmp_path / ".agent" / "GATE_CONFIG.json"
        data = json.loads(gate_path.read_text(encoding="utf-8"))
        data["gates"]["pre_task_gate"]["enabled"] = False
        gate_path.write_text(json.dumps(data), encoding="utf-8")
        result = validate_scaffold(str(tmp_path))
        assert result["valid"] is False
        assert any("enabled=true" in e and "pre_task_gate" in e for e in result["errors"])

    def test_gate_block_on_failure_false_fails(self, tmp_path):
        """Gate with block_on_failure=false fails validation."""
        create_scaffold(str(tmp_path))
        gate_path = tmp_path / ".agent" / "GATE_CONFIG.json"
        data = json.loads(gate_path.read_text(encoding="utf-8"))
        data["gates"]["pre_gpt_review_gate"]["block_on_failure"] = False
        gate_path.write_text(json.dumps(data), encoding="utf-8")
        result = validate_scaffold(str(tmp_path))
        assert result["valid"] is False
        assert any(
            "block_on_failure=true" in e and "pre_gpt_review_gate" in e
            for e in result["errors"]
        )

    def test_startup_read_gate_strict_mode_false_fails(self, tmp_path):
        """startup_read_gate with strict_mode=false fails validation."""
        create_scaffold(str(tmp_path))
        gate_path = tmp_path / ".agent" / "GATE_CONFIG.json"
        data = json.loads(gate_path.read_text(encoding="utf-8"))
        data["gates"]["startup_read_gate"]["strict_mode"] = False
        gate_path.write_text(json.dumps(data), encoding="utf-8")
        result = validate_scaffold(str(tmp_path))
        assert result["valid"] is False
        assert any("strict_mode=true" in e for e in result["errors"])

    def test_required_reads_entry_missing_fields_fails(self, tmp_path):
        """REQUIRED_READS entry missing required fields fails validation."""
        create_scaffold(str(tmp_path))
        reads_path = tmp_path / ".agent" / "REQUIRED_READS.json"
        data = json.loads(reads_path.read_text(encoding="utf-8"))
        # Replace first entry with incomplete one
        data["required_reads"][0] = {"path": "some/file.txt"}
        reads_path.write_text(json.dumps(data), encoding="utf-8")
        result = validate_scaffold(str(tmp_path))
        assert result["valid"] is False
        assert any("missing fields" in e for e in result["errors"])

    def test_required_reads_invalid_evidence_level_fails(self, tmp_path):
        """REQUIRED_READS entry with invalid evidence_level fails validation."""
        create_scaffold(str(tmp_path))
        reads_path = tmp_path / ".agent" / "REQUIRED_READS.json"
        data = json.loads(reads_path.read_text(encoding="utf-8"))
        data["required_reads"][0]["evidence_level"] = "P2"
        reads_path.write_text(json.dumps(data), encoding="utf-8")
        result = validate_scaffold(str(tmp_path))
        assert result["valid"] is False
        assert any("invalid evidence_level" in e for e in result["errors"])

    def test_p0_entry_must_read_at_startup_false_fails(self, tmp_path):
        """P0 entry with must_read_at_startup=false fails validation."""
        create_scaffold(str(tmp_path))
        reads_path = tmp_path / ".agent" / "REQUIRED_READS.json"
        data = json.loads(reads_path.read_text(encoding="utf-8"))
        # First P0 entry
        data["required_reads"][0]["must_read_at_startup"] = False
        reads_path.write_text(json.dumps(data), encoding="utf-8")
        result = validate_scaffold(str(tmp_path))
        assert result["valid"] is False
        assert any("must_read_at_startup=true" in e for e in result["errors"])

    def test_p0_entry_fail_closed_if_missing_false_fails(self, tmp_path):
        """P0 entry with fail_closed_if_missing=false fails validation."""
        create_scaffold(str(tmp_path))
        reads_path = tmp_path / ".agent" / "REQUIRED_READS.json"
        data = json.loads(reads_path.read_text(encoding="utf-8"))
        # First P0 entry
        data["required_reads"][0]["fail_closed_if_missing"] = False
        reads_path.write_text(json.dumps(data), encoding="utf-8")
        result = validate_scaffold(str(tmp_path))
        assert result["valid"] is False
        assert any("fail_closed_if_missing=true" in e for e in result["errors"])

    def test_strict_validation_passes_on_valid_scaffold(self, tmp_path):
        """A properly scaffolded project passes all strict validation checks."""
        create_scaffold(str(tmp_path))
        result = validate_scaffold(str(tmp_path))
        assert result["valid"] is True, f"Strict validation failed: {result['errors']}"


# ---------------------------------------------------------------------------
# Tests: R2 — type-safety & non-boolean truthy rejection
# ---------------------------------------------------------------------------

class TestR2TypeSafetyValidation:
    """R2: REQUIRED_READS field type checks and non-boolean truthy rejection."""

    def test_required_reads_path_integer_fails(self, tmp_path):
        """REQUIRED_READS entry with path=123 fails (non-string path)."""
        create_scaffold(str(tmp_path))
        reads_path = tmp_path / ".agent" / "REQUIRED_READS.json"
        data = json.loads(reads_path.read_text(encoding="utf-8"))
        data["required_reads"][0]["path"] = 123
        reads_path.write_text(json.dumps(data), encoding="utf-8")
        result = validate_scaffold(str(tmp_path))
        assert result["valid"] is False
        assert any("path must be a non-empty string" in e for e in result["errors"])

    def test_required_reads_path_empty_string_fails(self, tmp_path):
        """REQUIRED_READS entry with path='' fails (empty path)."""
        create_scaffold(str(tmp_path))
        reads_path = tmp_path / ".agent" / "REQUIRED_READS.json"
        data = json.loads(reads_path.read_text(encoding="utf-8"))
        data["required_reads"][0]["path"] = ""
        reads_path.write_text(json.dumps(data), encoding="utf-8")
        result = validate_scaffold(str(tmp_path))
        assert result["valid"] is False
        assert any("path must be a non-empty string" in e for e in result["errors"])

    def test_p1_must_read_at_startup_string_fails(self, tmp_path):
        """P1 entry with must_read_at_startup='yes' fails (non-boolean)."""
        create_scaffold(str(tmp_path))
        reads_path = tmp_path / ".agent" / "REQUIRED_READS.json"
        data = json.loads(reads_path.read_text(encoding="utf-8"))
        # Third entry is P1
        data["required_reads"][2]["must_read_at_startup"] = "yes"
        reads_path.write_text(json.dumps(data), encoding="utf-8")
        result = validate_scaffold(str(tmp_path))
        assert result["valid"] is False
        assert any("must_read_at_startup must be a boolean" in e for e in result["errors"])

    def test_p1_fail_closed_if_missing_string_fails(self, tmp_path):
        """P1 entry with fail_closed_if_missing='no' fails (non-boolean)."""
        create_scaffold(str(tmp_path))
        reads_path = tmp_path / ".agent" / "REQUIRED_READS.json"
        data = json.loads(reads_path.read_text(encoding="utf-8"))
        data["required_reads"][2]["fail_closed_if_missing"] = "no"
        reads_path.write_text(json.dumps(data), encoding="utf-8")
        result = validate_scaffold(str(tmp_path))
        assert result["valid"] is False
        assert any("fail_closed_if_missing must be a boolean" in e for e in result["errors"])

    def test_governance_flag_truthy_integer_fails(self, tmp_path):
        """Governance flag set to 1 (truthy int) fails validation."""
        create_scaffold(str(tmp_path))
        config_path = tmp_path / ".agent" / "PROJECT_AGENT_CONFIG.json"
        data = json.loads(config_path.read_text(encoding="utf-8"))
        data["governance"]["enforce_startup_read_gate"] = 1
        config_path.write_text(json.dumps(data), encoding="utf-8")
        result = validate_scaffold(str(tmp_path))
        assert result["valid"] is False
        assert any("governance flags not all true" in e for e in result["errors"])

    def test_governance_flag_truthy_string_fails(self, tmp_path):
        """Governance flag set to 'yes' (truthy string) fails validation."""
        create_scaffold(str(tmp_path))
        config_path = tmp_path / ".agent" / "PROJECT_AGENT_CONFIG.json"
        data = json.loads(config_path.read_text(encoding="utf-8"))
        data["governance"]["enforce_pre_task_gate"] = "yes"
        config_path.write_text(json.dumps(data), encoding="utf-8")
        result = validate_scaffold(str(tmp_path))
        assert result["valid"] is False
        assert any("governance flags not all true" in e for e in result["errors"])

    def test_gate_enabled_truthy_integer_fails(self, tmp_path):
        """Gate enabled=1 (truthy int) fails validation."""
        create_scaffold(str(tmp_path))
        gate_path = tmp_path / ".agent" / "GATE_CONFIG.json"
        data = json.loads(gate_path.read_text(encoding="utf-8"))
        data["gates"]["startup_read_gate"]["enabled"] = 1
        gate_path.write_text(json.dumps(data), encoding="utf-8")
        result = validate_scaffold(str(tmp_path))
        assert result["valid"] is False
        assert any("enabled=true" in e and "startup_read_gate" in e for e in result["errors"])

    def test_gate_block_on_failure_truthy_string_fails(self, tmp_path):
        """Gate block_on_failure='yes' (truthy string) fails validation."""
        create_scaffold(str(tmp_path))
        gate_path = tmp_path / ".agent" / "GATE_CONFIG.json"
        data = json.loads(gate_path.read_text(encoding="utf-8"))
        data["gates"]["pre_task_gate"]["block_on_failure"] = "yes"
        gate_path.write_text(json.dumps(data), encoding="utf-8")
        result = validate_scaffold(str(tmp_path))
        assert result["valid"] is False
        assert any(
            "block_on_failure=true" in e and "pre_task_gate" in e
            for e in result["errors"]
        )

    def test_r2_type_safety_passes_on_valid_scaffold(self, tmp_path):
        """A properly scaffolded project passes all R2 type-safety checks."""
        create_scaffold(str(tmp_path))
        result = validate_scaffold(str(tmp_path))
        assert result["valid"] is True, f"R2 type-safety failed: {result['errors']}"


# ---------------------------------------------------------------------------
# Tests: GOVERNANCE-SCRIPTS-A1 — deployable governance script scaffolding
# ---------------------------------------------------------------------------

class TestGovernanceScriptsScaffold:
    """Tests for governance script scaffold generation (v1.2.0)."""

    EXPECTED_SCRIPTS = [
        "scripts/startup_read_gate.py",
        "scripts/pre_task_gate.py",
        "scripts/pre_gpt_review_gate.py",
        "scripts/state_machine_runtime.py",
        "scripts/human_decision_record.py",
    ]

    def test_governance_scripts_created(self, tmp_path):
        """create_scaffold generates all 5 governance scripts."""
        project = tmp_path / "gov-scripts-project"
        project.mkdir()
        create_scaffold(str(project))
        for script in self.EXPECTED_SCRIPTS:
            script_path = project / script
            assert script_path.exists(), f"Missing governance script: {script}"

    def test_governance_scripts_are_valid_python(self, tmp_path):
        """Generated governance scripts are syntactically valid Python."""
        import py_compile
        project = tmp_path / "syntax-check-project"
        project.mkdir()
        create_scaffold(str(project))
        for script in self.EXPECTED_SCRIPTS:
            script_path = project / script
            try:
                py_compile.compile(str(script_path), doraise=True)
            except py_compile.PyCompileError as e:
                pytest.fail(f"Governance script {script} has syntax error: {e}")

    def test_governance_scripts_have_cli_entry_point(self, tmp_path):
        """Each governance script has if __name__ == '__main__' entry point."""
        project = tmp_path / "cli-check-project"
        project.mkdir()
        create_scaffold(str(project))
        for script in self.EXPECTED_SCRIPTS:
            script_path = project / script
            content = script_path.read_text(encoding="utf-8")
            assert 'if __name__' in content, (
                f"Governance script {script} missing CLI entry point"
            )

    def test_validate_governance_scripts_pass(self, tmp_path):
        """validate_scaffold passes when all governance scripts are present."""
        create_scaffold(str(tmp_path))
        result = validate_scaffold(str(tmp_path))
        assert result["valid"] is True, f"Validation failed: {result['errors']}"

    def test_validate_missing_governance_script_fails(self, tmp_path):
        """validate_scaffold fails when a governance script is missing."""
        create_scaffold(str(tmp_path))
        # Remove one governance script
        (tmp_path / "scripts" / "state_machine_runtime.py").unlink()
        result = validate_scaffold(str(tmp_path))
        assert result["valid"] is False
        assert any("Missing governance scripts" in e for e in result["errors"])

    def test_validate_governance_script_missing_core_function_fails(self, tmp_path):
        """validate_scaffold fails when governance script lacks core function."""
        create_scaffold(str(tmp_path))
        # Overwrite startup_read_gate.py without core 'gate' function
        script_path = tmp_path / "scripts" / "startup_read_gate.py"
        script_path.write_text(
            "#!/usr/bin/env python3\n"
            "# Missing core function\n"
            "if __name__ == '__main__':\n"
            "    print('hello')\n",
            encoding="utf-8"
        )
        result = validate_scaffold(str(tmp_path))
        assert result["valid"] is False
        assert any("missing core function" in e and "startup_read_gate.py" in e
                    for e in result["errors"])

    def test_validate_governance_script_missing_cli_entry_fails(self, tmp_path):
        """validate_scaffold fails when governance script lacks CLI entry point."""
        create_scaffold(str(tmp_path))
        # Overwrite pre_task_gate.py without CLI entry point
        script_path = tmp_path / "scripts" / "pre_task_gate.py"
        script_path.write_text(
            "#!/usr/bin/env python3\n"
            "def gate(task_id):\n"
            "    pass\n",
            encoding="utf-8"
        )
        result = validate_scaffold(str(tmp_path))
        assert result["valid"] is False
        assert any("CLI entry point" in e and "pre_task_gate.py" in e
                    for e in result["errors"])

    def test_validate_all_governance_scripts_missing_fails(self, tmp_path):
        """validate_scaffold reports all missing governance scripts."""
        create_scaffold(str(tmp_path))
        import shutil
        scripts_dir = tmp_path / "scripts"
        if scripts_dir.exists():
            shutil.rmtree(str(scripts_dir))
        scripts_dir.mkdir()
        result = validate_scaffold(str(tmp_path))
        assert result["valid"] is False
        assert any("Missing governance scripts" in e for e in result["errors"])


# ---------------------------------------------------------------------------
# R2: Conversation Registry — role field + JSON Schema validation via validate_scaffold()
# ---------------------------------------------------------------------------

class TestR2ConversationRegistryValidation:
    """R2 tests: role field in binding, JSON Schema in registry schema."""

    def test_scaffold_binding_has_role_field(self, tmp_path):
        """Generated CONVERSATION_BINDING.json includes role field."""
        create_scaffold(str(tmp_path))
        binding_path = tmp_path / ".agent" / "CONVERSATION_BINDING.json"
        data = json.loads(binding_path.read_text(encoding="utf-8"))
        assert "bindings" in data
        assert len(data["bindings"]) > 0
        assert "role" in data["bindings"][0], "Binding template missing role field"
        assert data["bindings"][0]["role"] in [
            "reviewer", "executor", "observer", "orchestrator"
        ]

    def test_registry_schema_has_json_schema_fields(self, tmp_path):
        """CONVERSATION_REGISTRY.schema.json has $schema, type, properties, required."""
        create_scaffold(str(tmp_path))
        schema_path = tmp_path / ".agent" / "CONVERSATION_REGISTRY.schema.json"
        data = json.loads(schema_path.read_text(encoding="utf-8"))
        for field in ["$schema", "type", "properties", "required"]:
            assert field in data, (
                f"CONVERSATION_REGISTRY.schema.json missing JSON Schema field: {field}"
            )

    def test_registry_schema_has_role_enum(self, tmp_path):
        """Schema defines role property with enum constraint."""
        create_scaffold(str(tmp_path))
        schema_path = tmp_path / ".agent" / "CONVERSATION_REGISTRY.schema.json"
        data = json.loads(schema_path.read_text(encoding="utf-8"))
        role_schema = data["properties"]["bindings"]["items"]["properties"]["role"]
        assert "enum" in role_schema
        assert set(role_schema["enum"]) == {
            "reviewer", "executor", "observer", "orchestrator"
        }

    def test_registry_schema_has_capture_policy_const(self, tmp_path):
        """Schema defines capture_policy with const:true constraints."""
        create_scaffold(str(tmp_path))
        schema_path = tmp_path / ".agent" / "CONVERSATION_REGISTRY.schema.json"
        data = json.loads(schema_path.read_text(encoding="utf-8"))
        cp = data["properties"]["bindings"]["items"]["properties"]["capture_policy"]
        for field in ["must_match_run_id", "must_match_task_id",
                      "must_include_end_marker",
                      "forbid_last_message_only_capture"]:
            assert cp["properties"][field].get("const") is True, (
                f"capture_policy.{field} should have const: true"
            )

    def test_registry_schema_has_bindings_items_schema(self, tmp_path):
        """Schema defines the whole binding file and bindings item schema."""
        create_scaffold(str(tmp_path))
        schema_path = tmp_path / ".agent" / "CONVERSATION_REGISTRY.schema.json"
        data = json.loads(schema_path.read_text(encoding="utf-8"))
        assert "bindings" in data["properties"]
        assert data["properties"]["bindings"]["type"] == "array"
        assert data["properties"]["bindings"]["items"]["type"] == "object"
        assert "role" in data["properties"]["bindings"]["items"]["properties"]

    def test_registry_schema_has_governance_scope(self, tmp_path):
        """Schema defines external runtime governance scope."""
        create_scaffold(str(tmp_path))
        schema_path = tmp_path / ".agent" / "CONVERSATION_REGISTRY.schema.json"
        data = json.loads(schema_path.read_text(encoding="utf-8"))
        assert "governance_scope" in data["required"]
        scope = data["properties"]["governance_scope"]
        assert scope["properties"]["forbid_ad_hoc_gpt_submission"]["const"] is True
        runtimes = scope["properties"]["external_runtimes"]
        assert runtimes["minItems"] == 3
        assert set(runtimes["items"]["properties"]["runtime_id"]["enum"]) == {
            "devframe-control-plane",
            "dev-frame-opencode",
            "paper-workflow",
        }

    def test_scaffold_binding_includes_external_runtime_scope(self, tmp_path):
        """Generated binding governs dev-frame, opencode, and paper workflow."""
        create_scaffold(str(tmp_path))
        binding_path = tmp_path / ".agent" / "CONVERSATION_BINDING.json"
        data = json.loads(binding_path.read_text(encoding="utf-8"))
        runtime_ids = {
            item["runtime_id"]
            for item in data["governance_scope"]["external_runtimes"]
        }
        assert runtime_ids == {
            "devframe-control-plane",
            "dev-frame-opencode",
            "paper-workflow",
        }

    def test_scaffold_binding_defaults_to_pending_manual_binding(self, tmp_path):
        """Fresh scaffold does not fabricate an active conversation binding."""
        create_scaffold(str(tmp_path))
        binding_path = tmp_path / ".agent" / "CONVERSATION_BINDING.json"
        data = json.loads(binding_path.read_text(encoding="utf-8"))
        binding = data["bindings"][0]
        assert binding["binding_status"] == "pending_manual_binding"
        assert binding["conversation_id"] is None
        assert binding["chat_url"] is None

    def test_validate_scaffold_missing_role_fails(self, tmp_path):
        """validate_scaffold fails when binding has no role field."""
        create_scaffold(str(tmp_path))
        binding_path = tmp_path / ".agent" / "CONVERSATION_BINDING.json"
        data = json.loads(binding_path.read_text(encoding="utf-8"))
        del data["bindings"][0]["role"]
        binding_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        result = validate_scaffold(str(tmp_path))
        assert result["valid"] is False
        assert any("role" in e for e in result["errors"])

    def test_validate_scaffold_invalid_role_fails(self, tmp_path):
        """validate_scaffold fails when binding has invalid role value."""
        create_scaffold(str(tmp_path))
        binding_path = tmp_path / ".agent" / "CONVERSATION_BINDING.json"
        data = json.loads(binding_path.read_text(encoding="utf-8"))
        data["bindings"][0]["role"] = "superadmin"
        binding_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        result = validate_scaffold(str(tmp_path))
        assert result["valid"] is False
        assert any("role" in e and "superadmin" in e for e in result["errors"])

    def test_validate_scaffold_missing_json_schema_field_fails(self, tmp_path):
        """validate_scaffold fails when registry schema missing $schema field."""
        create_scaffold(str(tmp_path))
        schema_path = tmp_path / ".agent" / "CONVERSATION_REGISTRY.schema.json"
        data = json.loads(schema_path.read_text(encoding="utf-8"))
        del data["$schema"]
        schema_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        result = validate_scaffold(str(tmp_path))
        assert result["valid"] is False
        assert any("JSON Schema field" in e for e in result["errors"])

    def test_validate_scaffold_active_binding_without_url_fails(self, tmp_path):
        """validate_scaffold rejects active bindings without chat_url or conversation_id."""
        create_scaffold(str(tmp_path))
        binding_path = tmp_path / ".agent" / "CONVERSATION_BINDING.json"
        data = json.loads(binding_path.read_text(encoding="utf-8"))
        data["bindings"][0]["binding_status"] = "active"
        data["bindings"][0]["conversation_id"] = None
        data["bindings"][0]["chat_url"] = None
        binding_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        result = validate_scaffold(str(tmp_path))
        assert result["valid"] is False
        assert any("active binding" in e and "chat_url" in e for e in result["errors"])
