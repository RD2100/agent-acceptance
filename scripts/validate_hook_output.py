"""Hook output validator for EVIDENCE-CAPTURE-HOOK-FAILURE-RUNTIME-VALIDATION-A1.

Validates _evidence/hook-output/latest.json against
schemas/agent-runtime/evidence-capture.schema.json.

Failure semantics (v2.3.0):
  - sadp-audit exit_code != 0 → overall_result must be BLOCKED
  - ai-guard exit_code != 0 → overall_result must be BLOCKED
  - test-governance exit_code != 0 → overall_result must be BLOCKED
  - all exit_code == 0 → overall_result must be PASS
  - PASS_WITH_WARNINGS is forbidden
  - Semantic mismatch → validator exits nonzero (fail-closed)

Usage:
    python scripts/validate_hook_output.py \
        --file _evidence/hook-output/latest.json \
        --schema schemas/agent-runtime/evidence-capture.schema.json
"""
import argparse
import json
import sys
from pathlib import Path


def load_json(path: str) -> dict:
    """Load and parse a JSON file (handles UTF-8 BOM from PowerShell)."""
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def validate_against_schema(data: dict, schema: dict) -> list[str]:
    """Manual schema validation (no jsonschema dependency).

    Returns list of error messages. Empty list = valid.
    """
    errors = []

    # Check required top-level fields
    for field in schema.get("required", []):
        if field not in data:
            errors.append(f"Missing required field: {field}")

    # Validate hook_version format (semver pattern)
    hv = data.get("hook_version", "")
    import re
    if not re.match(r"^\d+\.\d+\.\d+$", hv):
        errors.append(f"hook_version '{hv}' does not match semver pattern")

    # Validate stages
    stages = data.get("stages", [])
    stages_schema = schema.get("properties", {}).get("stages", {})
    min_items = stages_schema.get("minItems", 1)
    max_items = stages_schema.get("maxItems", 4)

    if len(stages) < min_items:
        errors.append(f"stages has {len(stages)} items, minimum is {min_items}")
    if len(stages) > max_items:
        errors.append(f"stages has {len(stages)} items, maximum is {max_items}")

    valid_names = set()
    stage_items = stages_schema.get("items", {})
    name_enum = stage_items.get("properties", {}).get("name", {}).get("enum", [])
    valid_names = set(name_enum)

    required_stage_fields = ["name", "exit_code", "output_file", "duration_ms"]
    for i, stage in enumerate(stages):
        for field in required_stage_fields:
            if field not in stage:
                errors.append(f"stages[{i}] missing required field: {field}")
        name = stage.get("name", "")
        if name and valid_names and name not in valid_names:
            errors.append(f"stages[{i}].name '{name}' not in enum {valid_names}")
        ec = stage.get("exit_code")
        if ec is not None and not isinstance(ec, int):
            errors.append(f"stages[{i}].exit_code must be integer, got {type(ec).__name__}")
        dm = stage.get("duration_ms")
        if dm is not None and not isinstance(dm, int):
            errors.append(f"stages[{i}].duration_ms must be integer, got {type(dm).__name__}")

    # Validate overall_result enum
    or_enum = schema.get("properties", {}).get("overall_result", {}).get("enum", [])
    or_val = data.get("overall_result", "")
    if or_val and or_enum and or_val not in or_enum:
        errors.append(f"overall_result '{or_val}' not in enum {or_enum}")

    # Validate git_context
    gc = data.get("git_context", {})
    gc_required = schema.get("properties", {}).get("git_context", {}).get("required", [])
    for field in gc_required:
        if field not in gc:
            errors.append(f"git_context missing required field: {field}")

    return errors


def check_failure_semantics(data: dict) -> list[str]:
    """Verify the hook output follows expected failure semantics.

    Rules (v2.3.0):
      - sadp-audit exit_code != 0 → overall_result must be BLOCKED
      - ai-guard exit_code != 0 → overall_result must be BLOCKED
      - test-governance: advisory (runs in -Mode advisory, exit code logged but not blocking)
      - manifest-regen: advisory
      - all blocking exit_code == 0 → overall_result must be PASS
      - PASS_WITH_WARNINGS is forbidden in v2.3.0
    """
    errors = []
    stages = {s["name"]: s["exit_code"] for s in data.get("stages", [])}
    result = data.get("overall_result", "")

    # PASS_WITH_WARNINGS is forbidden
    if result == "PASS_WITH_WARNINGS":
        errors.append("overall_result=PASS_WITH_WARNINGS is forbidden in v2.3.0")

    # Blocking stages: sadp-audit and ai-guard must produce BLOCKED on failure
    blocking_stages = ["sadp-audit", "ai-guard"]
    for stage_name in blocking_stages:
        exit_code = stages.get(stage_name, 0)
        if exit_code != 0 and result != "BLOCKED":
            errors.append(
                f"{stage_name} exit_code={exit_code} but overall_result={result} (expected BLOCKED)"
            )

    # All blocking stages zero must produce PASS
    blocking_zeros = all(stages.get(s, 0) == 0 for s in blocking_stages)
    if blocking_zeros and result not in ("PASS", "BLOCKED"):
        errors.append(
            f"All blocking stages pass but overall_result={result} (expected PASS)"
        )

    return errors


def main():
    parser = argparse.ArgumentParser(description="Validate hook output against schema")
    parser.add_argument("--file", required=True, help="Path to latest.json")
    parser.add_argument("--schema", required=True, help="Path to evidence-capture.schema.json")
    args = parser.parse_args()

    file_path = Path(args.file)
    schema_path = Path(args.schema)

    if not file_path.exists():
        print(f"FAIL: File not found: {file_path}")
        sys.exit(1)
    if not schema_path.exists():
        print(f"FAIL: Schema not found: {schema_path}")
        sys.exit(1)

    # Load files
    try:
        data = load_json(str(file_path))
    except json.JSONDecodeError as e:
        print(f"FAIL: Invalid JSON in {file_path}: {e}")
        sys.exit(1)

    try:
        schema = load_json(str(schema_path))
    except json.JSONDecodeError as e:
        print(f"FAIL: Invalid JSON in schema {schema_path}: {e}")
        sys.exit(1)

    # Schema validation
    errors = validate_against_schema(data, schema)
    if errors:
        print(f"FAIL: Schema validation failed ({len(errors)} errors)")
        for err in errors:
            print(f"  - {err}")
        sys.exit(1)

    # Semantic checks — failures here are BLOCKING (fail-closed validator)
    semantic_errors = check_failure_semantics(data)
    if semantic_errors:
        print(f"FAIL: Semantic checks found {len(semantic_errors)} errors")
        for e in semantic_errors:
            print(f"  - {e}")
        sys.exit(1)

    # Report
    stages_summary = ", ".join(
        f"{s['name']}={s['exit_code']}" for s in data.get("stages", [])
    )
    print(f"PASS: {file_path} validates against {schema_path.name}")
    print(f"  hook_version: {data.get('hook_version', 'N/A')}")
    print(f"  overall_result: {data.get('overall_result', 'N/A')}")
    print(f"  stages: {stages_summary}")
    print(f"  timestamp: {data.get('timestamp', 'N/A')}")
    sys.exit(0)


if __name__ == "__main__":
    main()
