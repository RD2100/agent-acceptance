#!/usr/bin/env python3
"""Evaluate local, controlled-pilot, and formal-use readiness.

The gate is intentionally read-only. It consumes current structured evidence
and never dispatches agents, opens browser sessions, or executes external
runtimes. Missing human authority remains HUMAN_REQUIRED; malformed or
contradictory evidence is BLOCKED.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parent.parent
MAX_EVIDENCE_AGE_SECONDS = 24 * 60 * 60
CLOCK_SKEW_TOLERANCE_SECONDS = 5 * 60
MODES = ("local_governance", "controlled_pilot", "formal_use")


def _check(name: str, status: str, detail: str, evidence: str | None = None) -> dict:
    return {"name": name, "status": status, "detail": detail, "evidence": evidence}


def _parse_time(value: Any, field: str, errors: list[str]) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{field} must be a non-empty ISO timestamp")
        return None
    raw = value.strip()
    if raw.endswith("Z"):
        raw = raw[:-1] + "+00:00"
    raw = re.sub(r"(\.\d{6})\d+(?=[+-]\d{2}:\d{2}$)", r"\1", raw)
    try:
        parsed = datetime.fromisoformat(raw)
    except ValueError:
        errors.append(f"{field} must be a valid ISO timestamp")
        return None
    if parsed.tzinfo is None:
        errors.append(f"{field} must include a timezone")
        return None
    return parsed.astimezone(timezone.utc)


def _load_json(
    path: Path | None,
    repo_root: Path,
    label: str,
    *,
    missing_status: str,
) -> tuple[dict[str, Any] | None, dict | None]:
    if path is None:
        return None, _check(label, missing_status, f"{label} path was not supplied")

    root = repo_root.resolve()
    candidate = Path(path)
    candidate = candidate.resolve() if candidate.is_absolute() else (root / candidate).resolve()
    try:
        candidate.relative_to(root)
    except ValueError:
        return None, _check(
            label,
            "blocked",
            f"evidence path must stay within repository root: {candidate}",
            str(candidate),
        )

    try:
        data = json.loads(candidate.read_text(encoding="utf-8-sig"))
    except FileNotFoundError:
        return None, _check(label, missing_status, f"file not found: {candidate}", str(candidate))
    except json.JSONDecodeError as exc:
        return None, _check(label, "blocked", f"invalid JSON: {exc}", str(candidate))
    except OSError as exc:
        return None, _check(label, "blocked", f"cannot read evidence: {exc}", str(candidate))

    if not isinstance(data, dict):
        return None, _check(label, "blocked", "JSON root must be an object", str(candidate))
    return data, None


def _resolve_file(
    value: Any, repo_root: Path, field: str, errors: list[str]
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


def _freshness_errors(data: dict[str, Any], field: str) -> list[str]:
    errors: list[str] = []
    timestamp = _parse_time(data.get(field), field, errors)
    if timestamp:
        age = (datetime.now(timezone.utc) - timestamp).total_seconds()
        if age < -CLOCK_SKEW_TOLERANCE_SECONDS:
            errors.append(f"{field} is in the future")
        elif age > MAX_EVIDENCE_AGE_SECONDS:
            errors.append(f"{field} is stale")
    return errors


def _validate_local(path: Path | None, repo_root: Path) -> dict:
    data, load_check = _load_json(
        path, repo_root, "local_evidence", missing_status="blocked"
    )
    if load_check:
        return load_check

    errors = _freshness_errors(data, "generated_at")
    task_id = data.get("task_id")
    if task_id != "PRODUCTION-READINESS-AUTOMATION-A1":
        errors.append("local evidence task_id mismatch")
    canonical = data.get("canonical_tests")
    if not isinstance(canonical, dict):
        errors.append("canonical_tests object is required")
    else:
        if canonical.get("command") != "python -m pytest tests/ -q":
            errors.append("canonical_tests command must be python -m pytest tests/ -q")
        if canonical.get("exit_code") != 0:
            errors.append("canonical_tests exit_code must be 0")
        if canonical.get("failed") != 0:
            errors.append("canonical_tests failed must be 0")
        if not isinstance(canonical.get("passed"), int) or canonical.get("passed", 0) <= 0:
            errors.append("canonical_tests passed must be a positive integer")
        raw_path = _resolve_file(
            canonical.get("raw_output"), repo_root, "canonical_tests raw_output", errors
        )
        expected_sha = canonical.get("raw_output_sha256")
        if not isinstance(expected_sha, str) or not re.fullmatch(
            r"[0-9a-fA-F]{64}", expected_sha
        ):
            errors.append("canonical_tests raw_output_sha256 must be a SHA256 hex string")
        elif raw_path:
            actual_sha = hashlib.sha256(raw_path.read_bytes()).hexdigest()
            if actual_sha.lower() != expected_sha.lower():
                errors.append("canonical_tests raw_output SHA256 mismatch")
            raw_text = raw_path.read_text(encoding="utf-8-sig", errors="replace")
            if f"{canonical.get('passed')} passed" not in raw_text:
                errors.append("canonical_tests raw_output does not confirm passed count")

    probes = data.get("stress_probes")
    expected = {
        "allowed_edit": {
            "status": "PASS",
            "exit_code": 0,
            "file": "scripts/production_readiness_gate.py",
            "command": "python scripts\\qoderwork_task_runner.py edit-check --task-id PRODUCTION-READINESS-AUTOMATION-A1 --file scripts/production_readiness_gate.py",
            "markers": [
                "SADP Task Runner: EDIT-CHECK scripts/production_readiness_gate.py",
                "PASS: scripts/production_readiness_gate.py is in TaskSpec write_set",
                "[PASS] File scripts/production_readiness_gate.py approved",
            ],
        },
        "forbidden_edit": {
            "status": "BLOCKED",
            "exit_code": 1,
            "file": "README.md",
            "command": "python scripts\\qoderwork_task_runner.py edit-check --task-id PRODUCTION-READINESS-AUTOMATION-A1 --file README.md",
            "markers": [
                "SADP Task Runner: EDIT-CHECK README.md",
                "BLOCKED: README.md not in write_set",
                "[BLOCKED] File README.md BLOCKED",
            ],
        },
        "missing_finish_artifacts": {
            "status": "BLOCKED",
            "exit_code": 1,
            "file": None,
            "command": "python scripts\\qoderwork_task_runner.py finish --task-id PRODUCTION-READINESS-AUTOMATION-A1",
            "markers": [
                "SADP Task Runner: FINISH PRODUCTION-READINESS-AUTOMATION-A1",
                "BLOCKED: No ExecutionReport found",
                "[BLOCKED] Task PRODUCTION-READINESS-AUTOMATION-A1 BLOCKED",
            ],
        },
    }
    if not isinstance(probes, dict):
        errors.append("stress_probes object is required")
    else:
        for name, expected_probe in expected.items():
            probe = probes.get(name)
            if not isinstance(probe, dict) or probe.get("status") != expected_probe["status"]:
                errors.append(f"stress probe {name} must be {expected_probe['status']}")
                continue
            evidence_path = probe.get("evidence")
            evidence, evidence_check = _load_json(
                Path(evidence_path) if isinstance(evidence_path, str) else None,
                repo_root,
                f"stress_probe_{name}",
                missing_status="blocked",
            )
            if evidence_check:
                errors.append(evidence_check["detail"])
                continue
            if evidence.get("probe") != name:
                errors.append(f"stress probe {name} evidence name mismatch")
            if evidence.get("task_id") != task_id:
                errors.append(f"stress probe {name} task_id mismatch")
            if evidence.get("file") != expected_probe["file"]:
                errors.append(f"stress probe {name} file mismatch")
            if evidence.get("status") != expected_probe["status"]:
                errors.append(f"stress probe {name} evidence status mismatch")
            if evidence.get("exit_code") != expected_probe["exit_code"]:
                errors.append(f"stress probe {name} evidence exit_code mismatch")
            command = evidence.get("command")
            if not isinstance(command, str) or command.strip() != expected_probe["command"]:
                errors.append(f"stress probe {name} runner command mismatch")
            output = evidence.get("output")
            if not isinstance(output, str) or any(
                marker not in output for marker in expected_probe["markers"]
            ):
                errors.append(f"stress probe {name} runner output markers missing")

    if data.get("executed_external_runtime") is not False:
        errors.append("local verification must set executed_external_runtime=false")

    return _check(
        "local_evidence",
        "blocked" if errors else "passed",
        "; ".join(errors) if errors else "canonical tests and runner stress probes passed",
        str(path),
    )


def _validate_preflight(path: Path | None, repo_root: Path) -> dict:
    data, load_check = _load_json(
        path, repo_root, "gate0_preflight", missing_status="human_required"
    )
    if load_check:
        return load_check
    freshness_errors = _freshness_errors(data, "generated_at")
    if freshness_errors:
        return _check(
            "gate0_preflight", "blocked", "; ".join(freshness_errors), str(path)
        )
    if data.get("executed_external_runtime") is not False:
        return _check(
            "gate0_preflight", "blocked", "preflight must be read-only", str(path)
        )

    overall = data.get("overall")
    human_gate = data.get("human_gate_required")
    if overall == "PASS" and human_gate is False:
        return _check("gate0_preflight", "passed", "current Gate 0 is PASS", str(path))
    if overall == "HUMAN_REQUIRED" and human_gate is True:
        return _check(
            "gate0_preflight",
            "human_required",
            "current Gate 0 requires run-bound authorization or live sessions",
            str(path),
        )
    if overall == "BLOCKED":
        return _check("gate0_preflight", "blocked", "current Gate 0 is BLOCKED", str(path))
    return _check(
        "gate0_preflight",
        "blocked",
        f"contradictory preflight state: overall={overall}, human_gate_required={human_gate}",
        str(path),
    )


def _validate_dispatch(
    path: Path | None, repo_root: Path, preflight_path: Path | None
) -> dict:
    data, load_check = _load_json(
        path, repo_root, "dispatch_plan", missing_status="human_required"
    )
    if load_check:
        return load_check
    freshness_errors = _freshness_errors(data, "generated_at")
    if freshness_errors:
        return _check(
            "dispatch_plan", "blocked", "; ".join(freshness_errors), str(path)
        )
    if data.get("executed_external_runtime") is not False:
        return _check("dispatch_plan", "blocked", "dispatch plan must be read-only", str(path))

    status = data.get("status")
    if status == "READY":
        source = data.get("source_preflight")
        if not isinstance(source, dict) or source.get("overall") != "PASS" or source.get(
            "human_gate_required"
        ) is not False:
            return _check(
                "dispatch_plan",
                "blocked",
                "READY dispatch requires a PASS source preflight",
                str(path),
            )
        source_errors: list[str] = []
        source_path = _resolve_file(
            source.get("path"), repo_root, "dispatch source preflight path", source_errors
        )
        expected_preflight = _resolve_file(
            str(preflight_path) if preflight_path else None,
            repo_root,
            "current preflight path",
            source_errors,
        )
        if source_path and expected_preflight and source_path != expected_preflight:
            source_errors.append("dispatch source preflight path must match current preflight")
        if source_path:
            actual_sha = hashlib.sha256(source_path.read_bytes()).hexdigest()
            expected_sha = source.get("sha256")
            if not isinstance(expected_sha, str) or not re.fullmatch(
                r"[0-9a-fA-F]{64}", expected_sha
            ):
                source_errors.append("dispatch source preflight sha256 must be a SHA256 hex string")
            elif expected_sha.lower() != actual_sha.lower():
                source_errors.append("dispatch source preflight SHA256 mismatch")
            source_data, source_load_check = _load_json(
                source_path, repo_root, "dispatch_source_preflight", missing_status="blocked"
            )
            if source_load_check:
                source_errors.append(source_load_check["detail"])
            else:
                for field in ("generated_at", "overall", "human_gate_required"):
                    if source.get(field) != source_data.get(field):
                        source_errors.append(f"dispatch source preflight {field} mismatch")
                if source_data.get("executed_external_runtime") is not False:
                    source_errors.append("dispatch source preflight must be read-only")
        source_errors.extend(_freshness_errors(source, "generated_at"))
        if source_errors:
            return _check("dispatch_plan", "blocked", "; ".join(source_errors), str(path))
        return _check("dispatch_plan", "passed", "dispatch plan is READY", str(path))
    if status == "HUMAN_REQUIRED":
        return _check(
            "dispatch_plan", "human_required", "dispatch plan remains human-gated", str(path)
        )
    if status == "BLOCKED":
        return _check("dispatch_plan", "blocked", "dispatch plan is BLOCKED", str(path))
    return _check("dispatch_plan", "blocked", f"unknown dispatch status: {status}", str(path))


def _validate_pilot(
    path: Path | None,
    repo_root: Path,
    preflight_path: Path | None,
    dispatch_path: Path | None,
) -> tuple[dict, str | None, datetime | None]:
    data, load_check = _load_json(
        path, repo_root, "real_multi_gpt_pilot", missing_status="human_required"
    )
    if load_check:
        return load_check, None, None

    errors = _freshness_errors(data, "completed_at")
    completed_at = _parse_time(data.get("completed_at"), "completed_at", [])
    run_id = data.get("run_id")
    if not isinstance(run_id, str) or not run_id.strip():
        errors.append("pilot run_id must be non-empty")
    if data.get("status") != "pass":
        errors.append("pilot status must be pass")
    if data.get("executed_external_runtime") is not True:
        errors.append("real pilot must set executed_external_runtime=true")
    for field, artifact_path in (
        ("gate0_preflight_sha256", preflight_path),
        ("dispatch_plan_sha256", dispatch_path),
    ):
        expected_sha = data.get(field)
        if not isinstance(expected_sha, str) or not re.fullmatch(
            r"[0-9a-fA-F]{64}", expected_sha
        ):
            errors.append(f"pilot {field} must be a SHA256 hex string")
            continue
        resolved = _resolve_file(
            str(artifact_path) if artifact_path else None,
            repo_root,
            field.removesuffix("_sha256"),
            errors,
        )
        if resolved:
            actual_sha = hashlib.sha256(resolved.read_bytes()).hexdigest()
            if actual_sha.lower() != expected_sha.lower():
                errors.append(f"pilot {field.removesuffix('_sha256')} SHA256 mismatch")

    sessions = data.get("agent_sessions")
    session_ids: list[str] = []
    agent_ids: list[str] = []
    if not isinstance(sessions, list) or len(sessions) < 2:
        errors.append("at least two agent_sessions are required")
    else:
        for item in sessions:
            if not isinstance(item, dict):
                errors.append("agent_sessions entries must be objects")
                continue
            agent_id = item.get("agent_id")
            session_id = item.get("session_id")
            if not isinstance(agent_id, str) or not agent_id.strip():
                errors.append("each pilot agent requires agent_id")
            else:
                agent_ids.append(agent_id)
            if not isinstance(session_id, str) or not session_id.strip():
                errors.append("each pilot agent requires session_id")
            else:
                session_ids.append(session_id)
            session_evidence, evidence_check = _load_json(
                Path(item["evidence_file"])
                if isinstance(item.get("evidence_file"), str)
                else None,
                repo_root,
                f"agent_{agent_id or 'unknown'}_session_evidence",
                missing_status="blocked",
            )
            if evidence_check:
                errors.append(evidence_check["detail"])
            else:
                session_errors = _freshness_errors(session_evidence, "verified_at")
                if (
                    session_evidence.get("agent_id") != agent_id
                    or session_evidence.get("session_id") != session_id
                    or session_evidence.get("live") is not True
                ):
                    session_errors.append(
                        f"agent {agent_id or 'unknown'} session evidence mismatch"
                    )
                if item.get("verified_at") != session_evidence.get("verified_at"):
                    session_errors.append(
                        f"agent {agent_id or 'unknown'} session verified_at mismatch"
                    )
                errors.extend(session_errors)
        if len(session_ids) < 2 or len(session_ids) != len(set(session_ids)):
            errors.append("pilot requires at least two distinct session_id values")

    review = data.get("review")
    if not isinstance(review, dict):
        errors.append("independent review object is required")
    else:
        reviewer_id = review.get("reviewer_id")
        executor_ids = review.get("executor_ids")
        if review.get("verdict") != "pass":
            errors.append("independent review verdict must be pass")
        if not isinstance(reviewer_id, str) or not reviewer_id.strip():
            errors.append("reviewer_id must be non-empty")
        if not isinstance(executor_ids, list) or not executor_ids:
            errors.append("review executor_ids must be a non-empty list")
        elif reviewer_id in executor_ids:
            errors.append("reviewer_id must differ from executor_ids")
        elif any(executor_id not in agent_ids for executor_id in executor_ids):
            errors.append("review executor_ids must reference pilot agent_ids")
        if reviewer_id and reviewer_id not in agent_ids:
            errors.append("reviewer_id must reference a pilot agent_id")
        evidence_files = review.get("evidence_files")
        if not isinstance(evidence_files, list) or len(evidence_files) < 2:
            errors.append("review evidence_files must contain review.md and review.yaml evidence")
        else:
            resolved_review_files = [
                _resolve_file(value, repo_root, "review evidence_file", errors)
                for value in evidence_files
            ]
            suffixes = {item.suffix.lower() for item in resolved_review_files if item}
            if ".md" not in suffixes or not ({".yaml", ".yml"} & suffixes):
                errors.append("review evidence_files must include markdown and YAML artifacts")

    return (
        _check(
            "real_multi_gpt_pilot",
            "blocked" if errors else "passed",
            "; ".join(errors) if errors else "real two-session pilot passed independent review",
            str(path),
        ),
        run_id if isinstance(run_id, str) else None,
        completed_at,
    )


def _validate_authorization(
    path: Path | None,
    repo_root: Path,
    pilot_run_id: str | None,
    pilot_completed_at: datetime | None,
) -> dict:
    data, load_check = _load_json(
        path, repo_root, "production_authorization", missing_status="human_required"
    )
    if load_check:
        return load_check

    if data.get("authorized") is not True:
        return _check(
            "production_authorization",
            "human_required",
            "formal-use promotion has not been authorized",
            str(path),
        )

    errors: list[str] = []
    if data.get("scope") != "formal_use":
        errors.append("authorization scope must be formal_use")
    if pilot_run_id and data.get("run_id") != pilot_run_id:
        errors.append("authorization run_id must match pilot run_id")
    if data.get("risk_acknowledged") is not True:
        errors.append("authorization must set risk_acknowledged=true")
    for field in ("authorization_id", "decision_maker", "decision_reason"):
        value = data.get(field)
        if not isinstance(value, str) or not value.strip():
            errors.append(f"authorization {field} must be non-empty")

    approved_at = _parse_time(data.get("approved_at"), "approved_at", errors)
    expires_at = _parse_time(data.get("expires_at"), "expires_at", errors)
    now = datetime.now(timezone.utc)
    if approved_at and (approved_at - now).total_seconds() > CLOCK_SKEW_TOLERANCE_SECONDS:
        errors.append("approved_at is in the future")
    if approved_at and expires_at and expires_at <= approved_at:
        errors.append("expires_at must be after approved_at")
    if approved_at and pilot_completed_at and approved_at < pilot_completed_at:
        errors.append("production authorization must be approved after pilot completion")
    if errors:
        return _check(
            "production_authorization", "blocked", "; ".join(errors), str(path)
        )
    if expires_at and expires_at <= now:
        return _check(
            "production_authorization",
            "human_required",
            "production authorization is expired",
            str(path),
        )

    return _check(
        "production_authorization",
        "passed",
        "formal-use promotion is explicitly authorized",
        str(path),
    )


def evaluate_readiness(
    *,
    mode: str,
    repo_root: Path = REPO,
    local_evidence: Path | None = None,
    preflight: Path | None = None,
    dispatch_plan: Path | None = None,
    pilot_evidence: Path | None = None,
    production_authorization: Path | None = None,
) -> tuple[int, dict[str, Any]]:
    if mode not in MODES:
        report = {
            "mode": mode,
            "status": "BLOCKED",
            "executed_external_runtime": False,
            "checks": [_check("mode", "blocked", f"unsupported mode: {mode}")],
        }
        return 1, report

    checks = [_validate_local(local_evidence, Path(repo_root))]
    pilot_run_id = None
    pilot_completed_at = None
    if mode in {"controlled_pilot", "formal_use"}:
        checks.append(_validate_preflight(preflight, Path(repo_root)))
        checks.append(_validate_dispatch(dispatch_plan, Path(repo_root), preflight))
    if mode == "formal_use":
        pilot_check, pilot_run_id, pilot_completed_at = _validate_pilot(
            pilot_evidence,
            Path(repo_root),
            preflight,
            dispatch_plan,
        )
        checks.append(pilot_check)
        checks.append(
            _validate_authorization(
                production_authorization,
                Path(repo_root),
                pilot_run_id,
                pilot_completed_at,
            )
        )

    if any(check["status"] == "blocked" for check in checks):
        status, exit_code = "BLOCKED", 1
    elif any(check["status"] == "human_required" for check in checks):
        status, exit_code = "HUMAN_REQUIRED", 2
    else:
        status, exit_code = "READY", 0

    report = {
        "mode": mode,
        "status": status,
        "executed_external_runtime": False,
        "human_gate_required": status == "HUMAN_REQUIRED",
        "checks": checks,
    }
    return exit_code, report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=MODES, required=True)
    parser.add_argument("--repo-root", default=str(REPO))
    parser.add_argument("--local-evidence", required=True)
    parser.add_argument("--preflight")
    parser.add_argument("--dispatch-plan")
    parser.add_argument("--pilot-evidence")
    parser.add_argument("--production-authorization")
    parser.add_argument("--output")
    args = parser.parse_args()

    exit_code, report = evaluate_readiness(
        mode=args.mode,
        repo_root=Path(args.repo_root),
        local_evidence=Path(args.local_evidence),
        preflight=Path(args.preflight) if args.preflight else None,
        dispatch_plan=Path(args.dispatch_plan) if args.dispatch_plan else None,
        pilot_evidence=Path(args.pilot_evidence) if args.pilot_evidence else None,
        production_authorization=(
            Path(args.production_authorization) if args.production_authorization else None
        ),
    )
    payload = json.dumps(report, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(payload, encoding="utf-8")
    print(payload, end="")
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
