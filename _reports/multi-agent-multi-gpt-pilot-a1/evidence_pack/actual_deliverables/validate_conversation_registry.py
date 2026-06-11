#!/usr/bin/env python3
"""validate_conversation_registry.py — Standalone validator for AWSP Conversation Registry bindings.

Validates the structure, schema, and policy compliance of conversation registry
binding JSON files per AWSP v1.3.0.

Checks performed:
1. File existence
2. Valid JSON parsing
3. schema_version presence
4. project_root match (if provided)
5. default_conversation_policy presence
6. governance_scope external runtime boundaries
7. bindings is a list
8. Per-binding: agent_id, role, duplicate detection, binding_status,
   active-status requirements, capture_policy completeness
9. Schema-based validation against CONVERSATION_REGISTRY.schema.json
10. Optional task_id scope validation
11. Optional run_id recording

Usage:
    python scripts/validate_conversation_registry.py path/to/binding.json
    python scripts/validate_conversation_registry.py path/to/binding.json --project-root /my/project
    python scripts/validate_conversation_registry.py path/to/binding.json --task-id task-a1 --run-id run-123
"""

import argparse
import fnmatch
import json
import sys
from pathlib import Path

from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError

AWSP_VERSION = "1.3.0"

REPO = Path(__file__).resolve().parent.parent

ALLOWED_STATUSES = {
    "pending_manual_binding",
    "active",
    "paused",
    "retired",
    "invalid",
}

ALLOWED_ROLES = {
    "reviewer",
    "executor",
    "observer",
    "orchestrator",
}

REQUIRED_CAPTURE_FIELDS = [
    "must_match_run_id",
    "must_match_task_id",
    "must_include_end_marker",
    "forbid_last_message_only_capture",
]

REQUIRED_EXTERNAL_RUNTIMES = {
    "devframe-control-plane",
    "dev-frame-opencode",
    "paper-workflow",
}


def _normalize_path(p: str) -> str:
    """Normalize a path string: forward slashes, strip trailing slash."""
    return str(p).replace("\\", "/").rstrip("/")


def _has_real_binding_value(value: object) -> bool:
    """Return True only for non-empty, non-placeholder binding metadata."""
    if not isinstance(value, str):
        return False
    stripped = value.strip()
    if not stripped:
        return False
    return not (stripped.startswith("<") and stripped.endswith(">"))


def validate_binding(
    binding_path: str,
    project_root: str | None = None,
    task_id: str | None = None,
    run_id: str | None = None,
) -> dict:
    """Validate an AWSP Conversation Registry binding file.

    Args:
        binding_path: Path to the binding JSON file.
        project_root: Optional project root to cross-check against the
            binding's declared project_root field.
        task_id: Optional task ID to validate against allowed_task_scope.
        run_id: Optional run ID to record in result details.

    Returns:
        dict with keys: valid (bool), errors (list[str]),
        warnings (list[str]), details (dict).
    """
    errors: list[str] = []
    warnings: list[str] = []
    details: dict = {
        "awsp_version": AWSP_VERSION,
        "binding_path": str(binding_path),
    }

    # ------------------------------------------------------------------
    # 1. File existence
    # ------------------------------------------------------------------
    bp = Path(binding_path)
    if not bp.exists():
        errors.append(f"Binding file not found: {bp}")
        return {"valid": False, "errors": errors, "warnings": warnings, "details": details}

    # ------------------------------------------------------------------
    # 2. Parse JSON
    # ------------------------------------------------------------------
    try:
        data = json.loads(bp.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        errors.append(f"Invalid JSON: {exc}")
        return {"valid": False, "errors": errors, "warnings": warnings, "details": details}

    details["parsed"] = True

    # ------------------------------------------------------------------
    # 3. schema_version
    # ------------------------------------------------------------------
    if "schema_version" not in data:
        errors.append("Missing required field: schema_version")
    else:
        details["schema_version"] = data["schema_version"]

    # ------------------------------------------------------------------
    # 4. project_root match
    # ------------------------------------------------------------------
    if project_root is not None:
        binding_project_root = data.get("project_root")
        if binding_project_root is None:
            errors.append("Binding does not declare project_root")
        else:
            norm_expected = _normalize_path(project_root)
            norm_actual = _normalize_path(binding_project_root)
            if norm_expected != norm_actual:
                errors.append(
                    f"project_root mismatch: expected '{norm_expected}', "
                    f"got '{norm_actual}'"
                )
            details["project_root_checked"] = True

    # ------------------------------------------------------------------
    # 5. default_conversation_policy
    # ------------------------------------------------------------------
    if "default_conversation_policy" not in data:
        errors.append("Missing required field: default_conversation_policy")

    # ------------------------------------------------------------------
    # 6. governance_scope includes external runtime boundaries
    # ------------------------------------------------------------------
    governance_scope = data.get("governance_scope")
    if governance_scope is None:
        errors.append("Missing required field: governance_scope")
    elif not isinstance(governance_scope, dict):
        errors.append("Field 'governance_scope' must be an object")
    else:
        if governance_scope.get("default_execution_policy") != (
            "human_gated_for_external_runtime_execution"
        ):
            errors.append(
                "governance_scope.default_execution_policy must be "
                "human_gated_for_external_runtime_execution"
            )
        for field in [
            "forbid_ad_hoc_gpt_submission",
            "forbid_cross_repo_smoke_without_human_gate",
        ]:
            if governance_scope.get(field) is not True:
                errors.append(f"governance_scope.{field} must be true")

        external_runtimes = governance_scope.get("external_runtimes")
        if not isinstance(external_runtimes, list):
            errors.append("governance_scope.external_runtimes must be a list")
        else:
            runtime_ids = {
                runtime.get("runtime_id")
                for runtime in external_runtimes
                if isinstance(runtime, dict)
            }
            missing_runtimes = REQUIRED_EXTERNAL_RUNTIMES - runtime_ids
            if missing_runtimes:
                errors.append(
                    "governance_scope.external_runtimes missing required "
                    f"runtime_id(s): {', '.join(sorted(missing_runtimes))}"
                )
            for idx, runtime in enumerate(external_runtimes):
                prefix = f"governance_scope.external_runtimes[{idx}]"
                if not isinstance(runtime, dict):
                    errors.append(f"{prefix}: entry is not a JSON object")
                    continue
                runtime_id = runtime.get("runtime_id")
                if runtime_id not in REQUIRED_EXTERNAL_RUNTIMES:
                    errors.append(f"{prefix}: unknown runtime_id '{runtime_id}'")
                if runtime.get("human_gate_required") is not True:
                    errors.append(f"{prefix}: human_gate_required must be true")
                if not runtime.get("forbidden_actions"):
                    errors.append(f"{prefix}: forbidden_actions must not be empty")
                if not runtime.get("allowed_actions"):
                    errors.append(f"{prefix}: allowed_actions must not be empty")
            details["governance_runtime_count"] = len(external_runtimes)
            details["governance_runtime_ids"] = sorted(
                runtime_id for runtime_id in runtime_ids if runtime_id
            )

    # ------------------------------------------------------------------
    # 7. bindings is a list
    # ------------------------------------------------------------------
    bindings = data.get("bindings")
    if bindings is None:
        errors.append("Missing required field: bindings")
        return {"valid": False, "errors": errors, "warnings": warnings, "details": details}

    if not isinstance(bindings, list):
        errors.append("Field 'bindings' must be a list")
        return {"valid": False, "errors": errors, "warnings": warnings, "details": details}

    details["binding_count"] = len(bindings)

    # ------------------------------------------------------------------
    # 8. Per-binding validation
    # ------------------------------------------------------------------
    seen_agent_ids: set[str] = set()
    active_binding_count = 0

    for idx, binding in enumerate(bindings):
        prefix = f"bindings[{idx}]"

        if not isinstance(binding, dict):
            errors.append(f"{prefix}: entry is not a JSON object")
            continue

        # agent_id presence and non-empty
        agent_id = binding.get("agent_id")
        if not agent_id:
            errors.append(f"{prefix}: missing or empty agent_id")
        else:
            # Duplicate agent_id detection
            if agent_id in seen_agent_ids:
                errors.append(f"{prefix}: duplicate agent_id '{agent_id}'")
            seen_agent_ids.add(agent_id)

        # role field (v1.3.0)
        role = binding.get("role")
        if not role:
            errors.append(f"{prefix}: missing or empty role")
        elif role not in ALLOWED_ROLES:
            errors.append(
                f"{prefix}: invalid role '{role}' "
                f"(allowed: {', '.join(sorted(ALLOWED_ROLES))})"
            )

        # binding_status
        status = binding.get("binding_status")
        if status is None:
            errors.append(f"{prefix}: missing binding_status")
        elif status not in ALLOWED_STATUSES:
            errors.append(
                f"{prefix}: invalid binding_status '{status}' "
                f"(allowed: {', '.join(sorted(ALLOWED_STATUSES))})"
            )

        # Active bindings must have chat_url or conversation_id
        if status == "active":
            active_binding_count += 1
            has_chat_url = _has_real_binding_value(binding.get("chat_url"))
            has_conv_id = _has_real_binding_value(binding.get("conversation_id"))
            if not has_chat_url and not has_conv_id:
                errors.append(
                    f"{prefix}: active binding must have a real chat_url or "
                    "conversation_id"
                )

        # capture_policy
        capture_policy = binding.get("capture_policy")
        if capture_policy is None:
            errors.append(f"{prefix}: missing capture_policy")
        elif not isinstance(capture_policy, dict):
            errors.append(f"{prefix}: capture_policy must be an object")
        else:
            for field in REQUIRED_CAPTURE_FIELDS:
                if field not in capture_policy:
                    errors.append(
                        f"{prefix}: capture_policy missing field '{field}'"
                    )
                elif capture_policy[field] is not True:
                    errors.append(
                        f"{prefix}: capture_policy.{field} must be true (boolean), "
                        f"got {json.dumps(capture_policy[field])}"
                    )

    details["active_binding_count"] = active_binding_count
    details["pending_binding_count"] = sum(
        1
        for binding in bindings
        if isinstance(binding, dict)
        and binding.get("binding_status") == "pending_manual_binding"
    )

    # ------------------------------------------------------------------
    # 9. Schema-based validation against CONVERSATION_REGISTRY.schema.json
    # ------------------------------------------------------------------
    schema_path = bp.parent / "CONVERSATION_REGISTRY.schema.json"
    if schema_path.exists():
        try:
            schema_data = json.loads(schema_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            errors.append(f"CONVERSATION_REGISTRY.schema.json is invalid JSON: {e}")
            details["schema_file_loaded"] = False
            details["schema_validation"] = "failed"
        except OSError as e:
            errors.append(f"CONVERSATION_REGISTRY.schema.json cannot be read: {e}")
            details["schema_file_loaded"] = False
            details["schema_validation"] = "failed"
        else:
            details["schema_file_loaded"] = True
            details["schema_path"] = str(schema_path)

            required_schema_fields = ["$schema", "type", "properties", "required"]
            schema_is_usable = True
            for sf in required_schema_fields:
                if sf not in schema_data:
                    schema_is_usable = False
                    errors.append(
                        f"CONVERSATION_REGISTRY.schema.json missing JSON Schema field: {sf}"
                    )

            if schema_is_usable:
                try:
                    Draft202012Validator.check_schema(schema_data)
                except SchemaError as e:
                    schema_is_usable = False
                    errors.append(f"CONVERSATION_REGISTRY.schema.json schema error: {e.message}")

            schema_error_count = 0
            if schema_is_usable:
                validator = Draft202012Validator(schema_data)
                validation_errors = sorted(
                    validator.iter_errors(data),
                    key=lambda err: list(err.absolute_path),
                )
                schema_error_count = len(validation_errors)
                for err in validation_errors:
                    location = ".".join(str(p) for p in err.absolute_path)
                    if not location:
                        location = "<binding>"
                    errors.append(
                        f"schema validation failed at {location}: {err.message}"
                    )

            details["schema_validation_errors"] = schema_error_count
            details["schema_validation"] = (
                "passed" if schema_is_usable and schema_error_count == 0 else "failed"
            )
    else:
        errors.append(
            "CONVERSATION_REGISTRY.schema.json not found alongside binding file; "
            "schema validation failed closed"
        )
        details["schema_file_loaded"] = False
        details["schema_validation"] = "failed"

    # ------------------------------------------------------------------
    # 10. task_id scope validation
    # ------------------------------------------------------------------
    if task_id is not None:
        details["task_id"] = task_id
        task_matched = False
        for idx, binding in enumerate(bindings):
            if not isinstance(binding, dict):
                continue
            allowed_scope = binding.get("allowed_task_scope")
            if allowed_scope is None:
                continue
            # allowed_task_scope can be a string pattern or list of patterns
            patterns = (
                allowed_scope
                if isinstance(allowed_scope, list)
                else [allowed_scope]
            )
            for pattern in patterns:
                if isinstance(pattern, str) and fnmatch.fnmatch(task_id, pattern):
                    task_matched = True
                    break
            if task_matched:
                break

        if not task_matched:
            warnings.append(
                f"task_id '{task_id}' did not match any binding's allowed_task_scope"
            )

    # ------------------------------------------------------------------
    # 11. run_id recording
    # ------------------------------------------------------------------
    if run_id is not None:
        details["run_id"] = run_id

    valid = len(errors) == 0
    summary = {
        "binding_count": details.get("binding_count", 0),
        "active_count": details.get("active_binding_count", 0),
        "pending_count": details.get("pending_binding_count", 0),
    }
    return {
        "valid": valid,
        "schema_validated": details.get("schema_validation") == "passed",
        "errors": errors,
        "warnings": warnings,
        "summary": summary,
        "details": details,
    }


def main() -> None:
    """CLI entry point: parse arguments, validate, and emit JSON result."""
    parser = argparse.ArgumentParser(
        description="Validate AWSP Conversation Registry binding files."
    )
    parser.add_argument(
        "binding_path",
        help="Path to the conversation registry binding JSON file.",
    )
    parser.add_argument(
        "--project-root",
        default=None,
        help="Project root directory to cross-check against the binding.",
    )
    parser.add_argument(
        "--task-id",
        default=None,
        help="Task ID to validate against allowed_task_scope patterns.",
    )
    parser.add_argument(
        "--run-id",
        default=None,
        help="Run ID to record in validation details.",
    )
    args = parser.parse_args()

    result = validate_binding(
        binding_path=args.binding_path,
        project_root=args.project_root,
        task_id=args.task_id,
        run_id=args.run_id,
    )

    print(json.dumps(result, indent=2, ensure_ascii=False))
    sys.exit(0 if result["valid"] else 1)


if __name__ == "__main__":
    main()
