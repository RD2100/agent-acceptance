#!/usr/bin/env python3
"""Gate 0 preflight for the multi-agent / multi-GPT pilot.

This checker is intentionally read-only. It validates governance evidence and
reports whether the pilot can proceed, needs a human gate, or is blocked.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

from validate_conversation_registry import validate_binding

REPO = Path(__file__).resolve().parent.parent
REQUIRED_RUNTIMES = {
    "devframe-control-plane",
    "dev-frame-opencode",
    "paper-workflow",
}


def _check(name: str, status: str, detail: str, evidence: str | None = None) -> dict:
    return {
        "name": name,
        "status": status,
        "detail": detail,
        "evidence": evidence,
    }


def _load_json(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    try:
        return json.loads(path.read_text(encoding="utf-8")), None
    except FileNotFoundError:
        return None, f"file not found: {path}"
    except json.JSONDecodeError as exc:
        return None, f"invalid JSON: {exc}"


def _section(text: str, heading: str) -> str:
    marker = f"## {heading}"
    start = text.find(marker)
    if start < 0:
        return ""
    next_heading = text.find("\n## ", start + len(marker))
    if next_heading < 0:
        return text[start:]
    return text[start:next_heading]


def _field_value(section: str, field: str) -> str | None:
    match = re.search(rf"^- \*\*{re.escape(field)}\*\*: (.+)$", section, re.M)
    return match.group(1).strip() if match else None


def _validate_bindings(binding_paths: list[Path], project_roots: list[str | None]) -> tuple[list[dict], list[str]]:
    checks: list[dict] = []
    agent_ids: list[str] = []

    for idx, binding_path in enumerate(binding_paths):
        project_root = project_roots[idx] if idx < len(project_roots) else None
        result = validate_binding(str(binding_path), project_root=project_root)
        if not result["valid"]:
            checks.append(
                _check(
                    f"binding_{idx}_valid",
                    "blocked",
                    "; ".join(result["errors"]),
                    str(binding_path),
                )
            )
            continue

        checks.append(
            _check(
                f"binding_{idx}_valid",
                "passed",
                "conversation binding validates",
                str(binding_path),
            )
        )
        data, load_error = _load_json(binding_path)
        if load_error or data is None:
            checks.append(
                _check(f"binding_{idx}_load", "blocked", load_error or "load failed", str(binding_path))
            )
            continue

        runtimes = {
            runtime.get("runtime_id")
            for runtime in data.get("governance_scope", {}).get("external_runtimes", [])
            if isinstance(runtime, dict)
        }
        if REQUIRED_RUNTIMES <= runtimes:
            checks.append(
                _check(
                    f"binding_{idx}_runtime_scope",
                    "passed",
                    "all governed external runtimes are declared",
                    str(binding_path),
                )
            )
        else:
            missing = sorted(REQUIRED_RUNTIMES - runtimes)
            checks.append(
                _check(
                    f"binding_{idx}_runtime_scope",
                    "blocked",
                    "missing runtime(s): " + ", ".join(missing),
                    str(binding_path),
                )
            )

        for binding in data.get("bindings", []):
            if isinstance(binding, dict) and binding.get("agent_id"):
                agent_ids.append(binding["agent_id"])
                if binding.get("binding_status") == "pending_manual_binding":
                    checks.append(
                        _check(
                            f"agent_{binding['agent_id']}_manual_binding",
                            "human_required",
                            "agent remains pending_manual_binding",
                            str(binding_path),
                        )
                    )

    duplicates = sorted({agent for agent in agent_ids if agent_ids.count(agent) > 1})
    if duplicates:
        checks.append(
            _check(
                "unique_agent_ids",
                "blocked",
                "duplicate agent_id(s): " + ", ".join(duplicates),
            )
        )
    else:
        checks.append(
            _check("unique_agent_ids", "passed", f"{len(agent_ids)} unique agent id(s)")
        )

    if len(agent_ids) < 2:
        checks.append(
            _check(
                "pilot_agent_count",
                "human_required",
                "pilot requires at least two independently bound agents",
            )
        )
    else:
        checks.append(
            _check("pilot_agent_count", "passed", f"{len(agent_ids)} agent(s) declared")
        )

    return checks, agent_ids


def _validate_capability_inventory(path: Path) -> list[dict]:
    if not path.exists():
        return [_check("capability_inventory", "blocked", "capability inventory missing", str(path))]

    text = path.read_text(encoding="utf-8", errors="replace")
    cap29 = _section(text, "29. dev-frame-opencode Dispatch")
    if not cap29:
        return [_check("cap_029_registered", "blocked", "CAP-029 section missing", str(path))]

    checks = [_check("cap_029_registered", "passed", "CAP-029 section exists", str(path))]
    usable_gate0 = _field_value(cap29, "Passport usable_for_gate0")
    usable_execution = _field_value(cap29, "Passport usable_for_execution")
    status = _field_value(cap29, "Status")

    if usable_gate0 == "true":
        checks.append(_check("cap_029_gate0", "passed", "usable_for_gate0=true", str(path)))
    else:
        checks.append(
            _check("cap_029_gate0", "blocked", "CAP-029 is not usable for Gate 0", str(path))
        )

    if status == "approved" and usable_execution == "true":
        checks.append(
            _check("cap_029_execution", "passed", "opencode dispatch executable", str(path))
        )
    else:
        checks.append(
            _check(
                "cap_029_execution",
                "human_required",
                f"opencode dispatch not executable (status={status}, usable_for_execution={usable_execution})",
                str(path),
            )
        )

    return checks


def _validate_tool_policy(path: Path) -> list[dict]:
    if not path.exists():
        return [_check("tool_policy", "blocked", "tool policy missing", str(path))]

    text = path.read_text(encoding="utf-8", errors="replace")
    required_terms = [
        "`opencode run` / dev-frame-opencode dispatch",
        "Cross-repo pytest/smoke scripts",
        "Paper workflow",
        "legacy `authorized=true` JSON file is not sufficient",
    ]
    missing = [term for term in required_terms if term not in text]
    if missing:
        return [
            _check(
                "tool_policy_runtime_gates",
                "blocked",
                "missing policy term(s): " + ", ".join(missing),
                str(path),
            )
        ]
    return [
        _check(
            "tool_policy_runtime_gates",
            "passed",
            "opencode, cross-repo, paper, and authorization gates documented",
            str(path),
        )
    ]


def evaluate_preflight(
    repo_root: Path = REPO,
    binding_paths: list[Path] | None = None,
    project_roots: list[str | None] | None = None,
) -> tuple[int, dict]:
    repo_root = Path(repo_root)
    binding_paths = binding_paths or [repo_root / ".agent" / "CONVERSATION_BINDING.json"]
    project_roots = project_roots or [str(repo_root) for _ in binding_paths]

    checks: list[dict] = []
    binding_checks, agent_ids = _validate_bindings(binding_paths, project_roots)
    checks.extend(binding_checks)
    checks.extend(
        _validate_capability_inventory(
            repo_root / "docs" / "agent-runtime" / "capability-inventory.md"
        )
    )
    checks.extend(_validate_tool_policy(repo_root / "docs" / "agent-runtime" / "tool-policy.md"))

    if any(check["status"] == "blocked" for check in checks):
        overall = "BLOCKED"
        exit_code = 1
    elif any(check["status"] == "human_required" for check in checks):
        overall = "HUMAN_REQUIRED"
        exit_code = 2
    else:
        overall = "PASS"
        exit_code = 0

    report = {
        "overall": overall,
        "executed_external_runtime": False,
        "human_gate_required": overall == "HUMAN_REQUIRED",
        "agent_count": len(agent_ids),
        "checks": checks,
    }
    return exit_code, report


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Read-only Gate 0 preflight for multi-agent / multi-GPT pilot."
    )
    parser.add_argument(
        "--binding",
        action="append",
        dest="bindings",
        help="Conversation binding JSON path. Repeat for multi-project pilots.",
    )
    parser.add_argument(
        "--project-root",
        action="append",
        dest="project_roots",
        help="Project root matching each --binding. Defaults to repository root.",
    )
    parser.add_argument(
        "--output",
        help="Optional path to write the JSON preflight report.",
    )
    args = parser.parse_args()

    binding_paths = [Path(p) for p in args.bindings] if args.bindings else None
    exit_code, report = evaluate_preflight(
        repo_root=REPO,
        binding_paths=binding_paths,
        project_roots=args.project_roots,
    )
    report_json = json.dumps(report, indent=2, ensure_ascii=False)
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(report_json + "\n", encoding="utf-8")
    print(report_json)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
