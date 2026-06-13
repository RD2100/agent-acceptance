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
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from validate_conversation_registry import validate_binding

REPO = Path(__file__).resolve().parent.parent
REQUIRED_RUNTIMES = {
    "devframe-control-plane",
    "dev-frame-opencode",
    "paper-workflow",
}
DEFAULT_ACTIVATION_RECORD = (
    Path("_reports") / "multi-agent-multi-gpt-pilot-a1" / "ACTIVATION_RECORD.json"
)
SESSION_EVIDENCE_MAX_AGE_SECONDS = 15 * 60
CLOCK_SKEW_TOLERANCE_SECONDS = 5 * 60


def _check(name: str, status: str, detail: str, evidence: str | None = None) -> dict:
    return {
        "name": name,
        "status": status,
        "detail": detail,
        "evidence": evidence,
    }


def _load_json(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
        if not isinstance(data, dict):
            return None, f"JSON root must be an object: {path}"
        return data, None
    except FileNotFoundError:
        return None, f"file not found: {path}"
    except json.JSONDecodeError as exc:
        return None, f"invalid JSON: {exc}"
    except OSError as exc:
        return None, f"cannot read file: {path}: {exc}"


def _parse_timestamp(value: Any, field: str, errors: list[str]) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{field} must be a non-empty ISO timestamp")
        return None
    raw = value.strip()
    if raw.endswith("Z"):
        raw = raw[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(raw)
    except ValueError:
        errors.append(f"{field} must be a valid ISO timestamp")
        return None
    if parsed.tzinfo is None:
        errors.append(f"{field} must include a timezone")
        return None
    return parsed.astimezone(timezone.utc)


def _resolve_evidence_path(
    repo_root: Path, value: Any, field: str, errors: list[str]
) -> Path | None:
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{field} must be a non-empty path")
        return None
    root = repo_root.resolve()
    candidate = Path(value)
    candidate = candidate.resolve() if candidate.is_absolute() else (root / candidate).resolve()
    try:
        candidate.relative_to(root)
    except ValueError:
        errors.append(f"{field} must stay within repository root")
        return None
    if not candidate.is_file():
        errors.append(f"{field} not found: {candidate}")
        return None
    return candidate


def _validate_activation_record(
    path: Path, agent_ids: list[str], repo_root: Path
) -> list[dict]:
    if not path.exists():
        return [
            _check(
                "run_authorization",
                "human_required",
                f"run-bound activation record missing: {path}",
                str(path),
            )
        ]

    data, load_error = _load_json(path)
    if load_error or data is None:
        return [_check("activation_record", "blocked", load_error or "load failed", str(path))]

    authorization = data.get("authorization")
    authorization_errors: list[str] = []
    run_id = data.get("run_id")
    if not isinstance(run_id, str) or not run_id.strip():
        authorization_errors.append("activation record run_id must be non-empty")
    if not isinstance(authorization, dict):
        authorization_errors.append("authorization object is required")
        authorization = {}

    required_strings = (
        "authorizing_task",
        "exact_command",
        "evidence_file",
        "decision_maker",
        "decision_reason",
    )
    for field in required_strings:
        value = authorization.get(field)
        if not isinstance(value, str) or not value.strip():
            authorization_errors.append(f"authorization {field} must be non-empty")
    if authorization.get("authorized") is not True:
        authorization_errors.append("authorization must set authorized=true")
    if authorization.get("risk_acknowledged") is not True:
        authorization_errors.append("authorization must set risk_acknowledged=true")
    write_set = authorization.get("expected_write_set")
    if not isinstance(write_set, list) or not write_set or not all(
        isinstance(item, str) and item.strip() for item in write_set
    ):
        authorization_errors.append(
            "authorization expected_write_set must be a non-empty string list"
        )

    approved_at = _parse_timestamp(
        authorization.get("approved_at"), "authorization approved_at", authorization_errors
    )
    expires_at = _parse_timestamp(
        authorization.get("expires_at"), "authorization expires_at", authorization_errors
    )
    now = datetime.now(timezone.utc)
    if approved_at and (approved_at - now).total_seconds() > CLOCK_SKEW_TOLERANCE_SECONDS:
        authorization_errors.append("authorization approved_at is in the future")
    if approved_at and expires_at and expires_at <= approved_at:
        authorization_errors.append("authorization expires_at must be after approved_at")
    if expires_at and expires_at <= now:
        authorization_errors.append("authorization record is expired")

    command = authorization.get("exact_command")
    if isinstance(command, str) and isinstance(run_id, str) and run_id not in command:
        authorization_errors.append("authorization exact_command must include run_id")
    authorization_evidence = _resolve_evidence_path(
        repo_root,
        authorization.get("evidence_file"),
        "authorization evidence_file",
        authorization_errors,
    )
    if authorization_evidence:
        evidence_data, evidence_error = _load_json(authorization_evidence)
        if evidence_error or evidence_data is None:
            authorization_errors.append(
                "authorization evidence invalid: " + (evidence_error or "load failed")
            )
        else:
            if evidence_data.get("run_id") != run_id:
                authorization_errors.append("authorization evidence run_id mismatch")
            if evidence_data.get("authorized") is not True:
                authorization_errors.append("authorization evidence must set authorized=true")

    checks = [
        _check(
            "run_authorization",
            "passed" if not authorization_errors else "human_required",
            "run-bound authorization is current and auditable"
            if not authorization_errors
            else "; ".join(authorization_errors),
            str(path),
        )
    ]

    active_agents = data.get("active_agents")
    session_errors: list[str] = []
    if not isinstance(active_agents, list):
        active_agents = []
        session_errors.append("active_agents must be a list")
    by_id = {
        item.get("agent_id"): item
        for item in active_agents
        if isinstance(item, dict) and isinstance(item.get("agent_id"), str)
    }
    session_ids: list[str] = []
    for agent_id in agent_ids:
        agent = by_id.get(agent_id)
        if not agent:
            session_errors.append(f"activation record missing agent: {agent_id}")
            continue
        if agent.get("binding_status") != "active":
            session_errors.append(f"agent {agent_id} is not active")
        if agent.get("cdp_session_verified") is not True:
            session_errors.append(f"agent {agent_id} lacks live CDP verification")
        session_id = agent.get("session_id")
        if not isinstance(session_id, str) or not session_id.strip():
            session_errors.append(f"agent {agent_id} lacks session_id")
        else:
            session_ids.append(session_id)
        evidence_file = agent.get("evidence_file")
        evidence_path = _resolve_evidence_path(
            repo_root,
            evidence_file,
            f"agent {agent_id} session evidence_file",
            session_errors,
        )
        verified_at = _parse_timestamp(
            agent.get("verified_at"),
            f"agent {agent_id} verified_at",
            session_errors,
        )
        now = datetime.now(timezone.utc)
        if verified_at:
            age_seconds = (now - verified_at).total_seconds()
            if age_seconds < -CLOCK_SKEW_TOLERANCE_SECONDS:
                session_errors.append(f"agent {agent_id} verified_at is in the future")
            elif age_seconds > SESSION_EVIDENCE_MAX_AGE_SECONDS:
                session_errors.append(f"agent {agent_id} session evidence is stale")
        if evidence_path:
            evidence_data, evidence_error = _load_json(evidence_path)
            if evidence_error or evidence_data is None:
                session_errors.append(
                    f"agent {agent_id} session evidence invalid: "
                    + (evidence_error or "load failed")
                )
            else:
                if evidence_data.get("agent_id") != agent_id:
                    session_errors.append(f"agent {agent_id} evidence agent_id mismatch")
                if evidence_data.get("session_id") != session_id:
                    session_errors.append(f"agent {agent_id} evidence session_id mismatch")
                if evidence_data.get("live") is not True:
                    session_errors.append(f"agent {agent_id} evidence does not prove live=true")
                if evidence_data.get("verified_at") != agent.get("verified_at"):
                    session_errors.append(f"agent {agent_id} evidence verified_at mismatch")

    cdp_session = data.get("cdp_session")
    if not isinstance(cdp_session, dict) or cdp_session.get("active") is not True:
        session_errors.append("cdp_session.active must be true")

    checks.append(
        _check(
            "live_agent_sessions",
            "passed" if not session_errors else "human_required",
            "all declared agents have current live session evidence"
            if not session_errors
            else "; ".join(session_errors),
            str(path),
        )
    )

    independent = len(session_ids) >= 2 and len(session_ids) == len(set(session_ids))
    checks.append(
        _check(
            "independent_session_ids",
            "passed" if independent else "human_required",
            f"{len(session_ids)} unique live session id(s)"
            if independent
            else "at least two distinct verified session_id values are required",
            str(path),
        )
    )
    return checks


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
            _check(
                "cap_029_execution",
                "passed",
                "capability approved for human-gated execution; run authorization is checked separately",
                str(path),
            )
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
    activation_record_path: Path | None = None,
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
    activation_record_path = activation_record_path or repo_root / DEFAULT_ACTIVATION_RECORD
    checks.extend(
        _validate_activation_record(Path(activation_record_path), agent_ids, repo_root)
    )

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
    parser.add_argument(
        "--activation-record",
        help="Run-bound activation record with authorization and live session evidence.",
    )
    args = parser.parse_args()

    binding_paths = [Path(p) for p in args.bindings] if args.bindings else None
    exit_code, report = evaluate_preflight(
        repo_root=REPO,
        binding_paths=binding_paths,
        project_roots=args.project_roots,
        activation_record_path=(
            Path(args.activation_record) if args.activation_record else None
        ),
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
