#!/usr/bin/env python3
"""validate_taskspec.py — Validate TaskSpec YAML structure. Catch write_set issues early."""
import sys, yaml, fnmatch
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

def validate(filepath):
    fp = Path(filepath)
    errors = []
    try:
        data = yaml.safe_load(fp.read_text(encoding="utf-8"))
    except yaml.YAMLError as e:
        return [f"YAML PARSE ERROR: {e}"]
    if not isinstance(data, dict):
        return [f"Not a YAML dict: {filepath}"]

    # Required: task_id
    if not data.get("task_id"):
        errors.append("missing task_id")

    # gate_0 structure
    gate = data.get("gate_0", {})
    if gate and not isinstance(gate, dict):
        errors.append("gate_0 must be a dict")

    # write_set must be a list
    ws = data.get("write_set", [])
    if not isinstance(ws, list):
        errors.append("write_set must be a list")
    else:
        for i, entry in enumerate(ws):
            if not isinstance(entry, str):
                errors.append(f"write_set[{i}] is not a string: {entry}")
            if entry.strip() != entry:
                errors.append(f"write_set[{i}] has leading/trailing whitespace")

    # Known sections after write_set — if items appear out of place
    if "known_dirty_worktree_excluded" in data:
        kd = data["known_dirty_worktree_excluded"]
        if not isinstance(kd, list):
            errors.append("known_dirty_worktree_excluded must be a list")

    return errors


def main():
    tasks_dir = REPO / ".ai" / "tasks"
    files = list(tasks_dir.glob("*.yaml")) + ([REPO / ".ai" / "current-task.yaml"] if (REPO / ".ai" / "current-task.yaml").exists() else [])

    all_ok = True
    for fp in sorted(files):
        errors = validate(str(fp))
        if errors:
            all_ok = False
            print(f"FAIL {fp.name}:")
            for e in errors:
                print(f"  - {e}")

    if all_ok:
        print(f"ALL OK: {len(files)} TaskSpecs valid")
    sys.exit(0 if all_ok else 1)

if __name__ == "__main__":
    main()
