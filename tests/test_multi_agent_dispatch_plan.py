"""Tests for the multi-agent dispatch plan packet."""

import json
import subprocess
import sys
from pathlib import Path

from jsonschema import Draft202012Validator

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))

from multi_agent_dispatch_plan import build_plan, validate_plan

REPO = Path(__file__).resolve().parent.parent
PLAN_SCHEMA_PATH = REPO / "schemas" / "agent-runtime" / "multi-agent-dispatch-plan.schema.json"
TASK_SCHEMA_PATH = REPO / "schemas" / "agent-runtime" / "task-spec.schema.json"
PREFLIGHT_PATH = REPO / "_reports" / "multi-agent-gate0-preflight-a1" / "GATE0_PREFLIGHT.json"


def _validator(path: Path) -> Draft202012Validator:
    schema = json.loads(path.read_text(encoding="utf-8-sig"))
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


def _load_schema(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _assert_schema_valid(path: Path, data: dict) -> None:
    errors = sorted(
        _validator(path).iter_errors(data),
        key=lambda error: list(error.absolute_path),
    )
    assert errors == []


def test_plan_schema_task_spec_definition_tracks_core_task_schema_contract():
    """Embedded TaskSpec definition must not drift on core required fields/enums."""
    plan_schema = _load_schema(PLAN_SCHEMA_PATH)
    task_schema = _load_schema(TASK_SCHEMA_PATH)
    embedded = plan_schema["$defs"]["task_spec"]

    assert embedded["required"] == task_schema["required"]
    for field in ["priority", "status"]:
        assert embedded["properties"][field]["enum"] == task_schema["properties"][field]["enum"]
    assert embedded["additionalProperties"] is False
    assert task_schema["additionalProperties"] is False


def test_plan_schema_task_spec_definition_tracks_nested_contracts():
    """Embedded TaskSpec nested gate/conflict/security contracts must not drift."""
    plan_schema = _load_schema(PLAN_SCHEMA_PATH)
    task_schema = _load_schema(TASK_SCHEMA_PATH)
    embedded = plan_schema["$defs"]["task_spec"]["properties"]
    core = task_schema["properties"]

    for field in ["gate_0", "conflict_registry", "security_report"]:
        assert embedded[field]["required"] == core[field]["required"]
        assert embedded[field]["properties"].keys() == core[field]["properties"].keys()

    embedded_gate = embedded["gate_0"]["properties"]
    core_gate = core["gate_0"]["properties"]
    for field in ["sufficiency_decision", "decision"]:
        assert embedded_gate[field]["enum"] == core_gate[field]["enum"]

    embedded_inventory = embedded_gate["inventory_evidence"]
    core_inventory = core_gate["inventory_evidence"]
    assert embedded_inventory["required"] == core_inventory["required"]
    assert embedded_inventory["properties"].keys() == core_inventory["properties"].keys()

    embedded_conflict = embedded["conflict_registry"]["properties"]
    core_conflict = core["conflict_registry"]["properties"]
    assert embedded_conflict["conflict_level"]["enum"] == core_conflict["conflict_level"]["enum"]


def test_default_plan_matches_preflight_and_is_read_only():
    """Current artifacts remain human-gated until live authorization exists."""
    plan = build_plan(preflight_path=PREFLIGHT_PATH)
    valid, errors = validate_plan(plan)

    assert valid is True
    assert errors == []
    assert plan["status"] == "HUMAN_REQUIRED"
    assert plan["executed_external_runtime"] is False
    assert plan["source_preflight"]["overall"] == "HUMAN_REQUIRED"
    assert plan["source_preflight"]["human_gate_required"] is True
    assert plan["conflict_summary"]["has_errors"] is False
    assert len(plan["assignments"]) >= 4
    assert any(item["parallel_safe"] for item in plan["assignments"])
    assert any(not item["parallel_safe"] for item in plan["assignments"])


def test_default_plan_validates_against_plan_and_task_schemas():
    """The generated dispatch packet and embedded TaskSpecs are schema-valid."""
    plan = build_plan(preflight_path=PREFLIGHT_PATH)

    _assert_schema_valid(PLAN_SCHEMA_PATH, plan)
    for assignment in plan["assignments"]:
        _assert_schema_valid(TASK_SCHEMA_PATH, assignment["task_spec"])


def test_plan_schema_validates_embedded_task_spec_priority():
    """Plan schema itself rejects invalid embedded TaskSpec fields."""
    plan = build_plan(preflight_path=PREFLIGHT_PATH)
    plan["assignments"][0]["task_spec"]["priority"] = "P9"
    errors = sorted(
        _validator(PLAN_SCHEMA_PATH).iter_errors(plan),
        key=lambda error: list(error.absolute_path),
    )

    assert any(
        list(error.absolute_path)[-2:] == ["task_spec", "priority"]
        and "P9" in error.message
        for error in errors
    )


def test_task_schema_rejects_unknown_fields():
    """Misspelled governance fields must fail closed in the canonical schema."""
    plan = build_plan(preflight_path=PREFLIGHT_PATH)
    task_spec = plan["assignments"][0]["task_spec"]
    task_spec["security_reprot"] = {"scan_status": "passed"}

    errors = list(_validator(TASK_SCHEMA_PATH).iter_errors(task_spec))

    assert any("Additional properties are not allowed" in error.message for error in errors)


def test_generated_security_report_starts_not_run():
    """Planning must not imply that a secret scan already ran."""
    plan = build_plan(preflight_path=PREFLIGHT_PATH)

    for assignment in plan["assignments"]:
        report = assignment["task_spec"]["security_report"]
        assert report["scan_status"] == "not_run"
        assert report["real_key_patterns_found"] is None
        assert report["key_rotation_needed"] is None


def test_parallel_ready_assignments_have_disjoint_write_sets():
    """Parallel-ready tasks must not share output files or directories."""
    plan = build_plan(preflight_path=PREFLIGHT_PATH)
    seen_writes = set()

    for assignment in plan["assignments"]:
        task_spec = assignment["task_spec"]
        if not assignment["parallel_safe"] or task_spec["status"] != "ready":
            continue
        for path in task_spec["conflict_registry"]["write_set"]:
            assert path not in seen_writes
            seen_writes.add(path)


def test_validate_plan_detects_parallel_write_conflict():
    """A same-group write overlap blocks the dispatch plan."""
    plan = build_plan(preflight_path=PREFLIGHT_PATH)
    ready_assignments = [
        item
        for item in plan["assignments"]
        if item["parallel_safe"] and item["task_spec"]["status"] == "ready"
    ]
    assert len(ready_assignments) >= 2
    shared_path = "_reports/shared-conflict/REPORT.md"
    ready_assignments[0]["task_spec"]["conflict_registry"]["write_set"] = [shared_path]
    ready_assignments[1]["task_spec"]["conflict_registry"]["write_set"] = [shared_path]

    valid, errors = validate_plan(plan)

    assert valid is False
    assert any("write conflict" in error for error in errors)


def test_validate_plan_detects_directory_file_write_conflict():
    """A parent directory write overlaps with a child file write in parallel groups."""
    plan = build_plan(preflight_path=PREFLIGHT_PATH)
    ready_assignments = [
        item
        for item in plan["assignments"]
        if item["parallel_safe"] and item["task_spec"]["status"] == "ready"
    ]
    assert len(ready_assignments) >= 2
    ready_assignments[0]["task_spec"]["conflict_registry"]["write_set"] = [
        "_reports/shared-conflict"
    ]
    ready_assignments[1]["task_spec"]["conflict_registry"]["write_set"] = [
        "_reports/shared-conflict/REPORT.md"
    ]

    valid, errors = validate_plan(plan)

    assert valid is False
    assert any("write conflict" in error for error in errors)


def test_cli_writes_output_and_preserves_human_gate_exit(tmp_path):
    """CLI output is durable JSON and current repo exits 2 for human gate."""
    output_path = tmp_path / "nested" / "DISPATCH_PLAN.json"

    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPTS / "multi_agent_dispatch_plan.py"),
            "--preflight",
            str(PREFLIGHT_PATH),
            "--output",
            str(output_path),
        ],
        cwd=REPO,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 2
    stdout_plan = json.loads(result.stdout)
    file_plan = json.loads(output_path.read_text(encoding="utf-8"))
    assert file_plan == stdout_plan
    _assert_schema_valid(PLAN_SCHEMA_PATH, file_plan)
    assert file_plan["status"] == "HUMAN_REQUIRED"
    assert file_plan["executed_external_runtime"] is False


def test_ready_plan_rejects_deferred_human_activation_tasks(tmp_path):
    """A forged PASS preflight cannot hide unresolved human activation tasks."""
    preflight = {
        "overall": "PASS",
        "executed_external_runtime": False,
        "human_gate_required": False,
        "agent_count": 2,
        "checks": [],
    }
    path = tmp_path / "preflight.json"
    path.write_text(json.dumps(preflight), encoding="utf-8")
    plan = build_plan(preflight_path=path)
    human_task = next(
        item for item in plan["assignments"]
        if item["parallel_group_id"] == "human-gated-activation"
    )
    human_task["task_spec"]["status"] = "deferred"
    human_task["blocking_conditions"] = ["authorization missing"]
    plan["status"] = "READY"

    valid, errors = validate_plan(plan)

    assert valid is False
    assert any("READY plan has unresolved human activation" in error for error in errors)


def test_missing_preflight_returns_blocked_plan_without_traceback(tmp_path):
    plan = build_plan(preflight_path=tmp_path / "missing.json")

    assert plan["status"] == "BLOCKED"
    assert plan["source_preflight"]["overall"] == "BLOCKED"
    assert "file not found" in plan["source_preflight"]["detail"]
