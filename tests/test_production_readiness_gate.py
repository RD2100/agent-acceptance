from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from production_readiness_gate import evaluate_readiness


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _stamp(value: datetime | None = None) -> str:
    return (value or _now()).isoformat().replace("+00:00", "Z")


def _write(path: Path, data: object) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return path


def _local_evidence(root: Path) -> Path:
    raw_output = root / "canonical-tests.txt"
    raw_output.write_text("1304 passed, 0 failed in 30.00s\n", encoding="utf-8")
    raw_sha = hashlib.sha256(raw_output.read_bytes()).hexdigest()
    probe_evidence = {}
    probe_rows = (
        (
            "allowed_edit",
            "PASS",
            0,
            "scripts/production_readiness_gate.py",
            "python scripts\\qoderwork_task_runner.py edit-check --task-id PRODUCTION-READINESS-AUTOMATION-A1 --file scripts/production_readiness_gate.py",
            "=== SADP Task Runner: EDIT-CHECK scripts/production_readiness_gate.py ===\nPASS: scripts/production_readiness_gate.py is in TaskSpec write_set\n[PASS] File scripts/production_readiness_gate.py approved",
        ),
        (
            "forbidden_edit",
            "BLOCKED",
            1,
            "README.md",
            "python scripts\\qoderwork_task_runner.py edit-check --task-id PRODUCTION-READINESS-AUTOMATION-A1 --file README.md",
            "=== SADP Task Runner: EDIT-CHECK README.md ===\nBLOCKED: README.md not in write_set\n[BLOCKED] File README.md BLOCKED",
        ),
        (
            "missing_finish_artifacts",
            "BLOCKED",
            1,
            None,
            "python scripts\\qoderwork_task_runner.py finish --task-id PRODUCTION-READINESS-AUTOMATION-A1",
            "=== SADP Task Runner: FINISH PRODUCTION-READINESS-AUTOMATION-A1 ===\nBLOCKED: No ExecutionReport found\n[BLOCKED] Task PRODUCTION-READINESS-AUTOMATION-A1 BLOCKED",
        ),
    )
    for name, status, exit_code, file_name, command, output in probe_rows:
        probe_path = _write(
            root / f"{name}.json",
            {
                "probe": name,
                "task_id": "PRODUCTION-READINESS-AUTOMATION-A1",
                "file": file_name,
                "status": status,
                "exit_code": exit_code,
                "command": command,
                "output": output,
            },
        )
        probe_evidence[name] = {"status": status, "evidence": str(probe_path)}
    return _write(
        root / "local.json",
        {
            "schema_version": "1.0.0",
            "task_id": "PRODUCTION-READINESS-AUTOMATION-A1",
            "generated_at": _stamp(),
            "canonical_tests": {
                "command": "python -m pytest tests/ -q",
                "exit_code": 0,
                "passed": 1304,
                "failed": 0,
                "raw_output": str(raw_output),
                "raw_output_sha256": raw_sha,
            },
            "stress_probes": probe_evidence,
            "executed_external_runtime": False,
        },
    )


def _preflight(root: Path, overall: str = "PASS") -> Path:
    return _write(
        root / "preflight.json",
        {
            "generated_at": _stamp(),
            "overall": overall,
            "human_gate_required": overall == "HUMAN_REQUIRED",
            "executed_external_runtime": False,
            "checks": [],
        },
    )


def _dispatch(root: Path, status: str = "READY") -> Path:
    preflight = root / "preflight.json"
    if not preflight.exists():
        preflight = _preflight(root, "PASS" if status == "READY" else status)
    preflight_data = json.loads(preflight.read_text(encoding="utf-8"))
    preflight_sha = hashlib.sha256(preflight.read_bytes()).hexdigest()
    return _write(
        root / "dispatch.json",
        {
            "plan_id": "plan-a1",
            "generated_at": _stamp(),
            "status": status,
            "executed_external_runtime": False,
            "source_preflight": {
                "path": str(preflight),
                "sha256": preflight_sha,
                "generated_at": preflight_data.get("generated_at"),
                "overall": "PASS" if status == "READY" else status,
                "human_gate_required": status == "HUMAN_REQUIRED",
                "executed_external_runtime": False,
                "detail": "Loaded Gate 0 preflight artifact.",
            },
            "assignments": [],
        },
    )


def _pilot(
    root: Path,
    *,
    duplicate_sessions: bool = False,
    completed_at: datetime | None = None,
) -> Path:
    preflight = root / "preflight.json"
    if not preflight.exists():
        preflight = _preflight(root)
    dispatch = root / "dispatch.json"
    if not dispatch.exists():
        dispatch = _dispatch(root)
    second_session = "session-executor" if duplicate_sessions else "session-reviewer"
    executor_evidence = _write(
        root / "executor-session.json",
        {
            "agent_id": "executor-1",
            "session_id": "session-executor",
            "live": True,
            "verified_at": _stamp(),
        },
    )
    reviewer_evidence = _write(
        root / "reviewer-session.json",
        {
            "agent_id": "reviewer-1",
            "session_id": second_session,
            "live": True,
            "verified_at": _stamp(),
        },
    )
    review_md = root / "review.md"
    review_md.write_text("# Review\n\nPASS\n", encoding="utf-8")
    review_yaml = root / "review.yaml"
    review_yaml.write_text("verdict: pass\n", encoding="utf-8")
    return _write(
        root / "pilot.json",
        {
            "run_id": "pilot-run-a1",
            "status": "pass",
            "completed_at": _stamp(completed_at),
            "executed_external_runtime": True,
            "gate0_preflight_sha256": hashlib.sha256(preflight.read_bytes()).hexdigest(),
            "dispatch_plan_sha256": hashlib.sha256(dispatch.read_bytes()).hexdigest(),
            "agent_sessions": [
                {
                    "agent_id": "executor-1",
                    "session_id": "session-executor",
                    "verified_at": json.loads(
                        executor_evidence.read_text(encoding="utf-8")
                    )["verified_at"],
                    "evidence_file": str(executor_evidence),
                },
                {
                    "agent_id": "reviewer-1",
                    "session_id": second_session,
                    "verified_at": json.loads(
                        reviewer_evidence.read_text(encoding="utf-8")
                    )["verified_at"],
                    "evidence_file": str(reviewer_evidence),
                },
            ],
            "review": {
                "verdict": "pass",
                "reviewer_id": "reviewer-1",
                "executor_ids": ["executor-1"],
                "evidence_files": [str(review_md), str(review_yaml)],
            },
        },
    )


def _authorization(
    root: Path,
    *,
    authorized: bool = True,
    approved_at: datetime | None = None,
    expires_at: datetime | None = None,
) -> Path:
    approved = approved_at or _now()
    return _write(
        root / "authorization.json",
        {
            "authorization_id": "production-promotion-a1",
            "scope": "formal_use",
            "run_id": "pilot-run-a1",
            "authorized": authorized,
            "risk_acknowledged": True,
            "decision_maker": "human-owner",
            "decision_reason": "Pilot and rollback evidence accepted.",
            "approved_at": _stamp(approved),
            "expires_at": _stamp(expires_at or (approved + timedelta(hours=8))),
        },
    )


def test_local_governance_ready_with_current_passing_evidence(tmp_path: Path):
    code, report = evaluate_readiness(
        mode="local_governance",
        repo_root=tmp_path,
        local_evidence=_local_evidence(tmp_path),
    )

    assert code == 0
    assert report["status"] == "READY"
    assert report["executed_external_runtime"] is False


def test_missing_local_evidence_is_blocked(tmp_path: Path):
    code, report = evaluate_readiness(
        mode="local_governance",
        repo_root=tmp_path,
        local_evidence=tmp_path / "missing.json",
    )

    assert code == 1
    assert report["status"] == "BLOCKED"
    assert any(check["name"] == "local_evidence" for check in report["checks"])


def test_stale_local_evidence_is_blocked(tmp_path: Path):
    path = _local_evidence(tmp_path)
    data = json.loads(path.read_text(encoding="utf-8"))
    data["generated_at"] = _stamp(_now() - timedelta(days=2))
    _write(path, data)

    code, report = evaluate_readiness(
        mode="local_governance", repo_root=tmp_path, local_evidence=path
    )

    assert code == 1
    assert report["status"] == "BLOCKED"
    assert "stale" in str(report["checks"]).lower()


def test_local_raw_output_hash_mismatch_is_blocked(tmp_path: Path):
    path = _local_evidence(tmp_path)
    data = json.loads(path.read_text(encoding="utf-8"))
    raw_output = Path(data["canonical_tests"]["raw_output"])
    raw_output.write_text("tampered\n", encoding="utf-8")

    code, report = evaluate_readiness(
        mode="local_governance", repo_root=tmp_path, local_evidence=path
    )

    assert code == 1
    assert "sha256" in str(report["checks"]).lower()


def test_synthetic_probe_without_runner_command_and_output_is_blocked(tmp_path: Path):
    path = _local_evidence(tmp_path)
    data = json.loads(path.read_text(encoding="utf-8"))
    probe_path = Path(data["stress_probes"]["allowed_edit"]["evidence"])
    probe = json.loads(probe_path.read_text(encoding="utf-8"))
    probe.pop("command")
    probe.pop("output")
    _write(probe_path, probe)

    code, report = evaluate_readiness(
        mode="local_governance", repo_root=tmp_path, local_evidence=path
    )

    assert code == 1
    assert "runner command" in str(report["checks"]).lower()


def test_dotnet_seven_digit_fraction_timestamp_is_accepted(tmp_path: Path):
    path = _local_evidence(tmp_path)
    data = json.loads(path.read_text(encoding="utf-8"))
    data["generated_at"] = _now().strftime("%Y-%m-%dT%H:%M:%S.1234567+00:00")
    _write(path, data)

    code, report = evaluate_readiness(
        mode="local_governance", repo_root=tmp_path, local_evidence=path
    )

    assert code == 0
    assert report["status"] == "READY"


def test_controlled_pilot_preserves_human_required_preflight(tmp_path: Path):
    code, report = evaluate_readiness(
        mode="controlled_pilot",
        repo_root=tmp_path,
        local_evidence=_local_evidence(tmp_path),
        preflight=_preflight(tmp_path, "HUMAN_REQUIRED"),
        dispatch_plan=_dispatch(tmp_path, "HUMAN_REQUIRED"),
    )

    assert code == 2
    assert report["status"] == "HUMAN_REQUIRED"


def test_controlled_pilot_ready_after_preflight_and_dispatch(tmp_path: Path):
    code, report = evaluate_readiness(
        mode="controlled_pilot",
        repo_root=tmp_path,
        local_evidence=_local_evidence(tmp_path),
        preflight=_preflight(tmp_path),
        dispatch_plan=_dispatch(tmp_path),
    )

    assert code == 0
    assert report["status"] == "READY"


def test_ready_dispatch_requires_pass_source_preflight(tmp_path: Path):
    dispatch = _dispatch(tmp_path)
    data = json.loads(dispatch.read_text(encoding="utf-8"))
    data["source_preflight"]["overall"] = "HUMAN_REQUIRED"
    data["source_preflight"]["human_gate_required"] = True
    _write(dispatch, data)

    code, report = evaluate_readiness(
        mode="controlled_pilot",
        repo_root=tmp_path,
        local_evidence=_local_evidence(tmp_path),
        preflight=_preflight(tmp_path),
        dispatch_plan=dispatch,
    )

    assert code == 1
    assert "source preflight" in str(report["checks"]).lower()


def test_ready_dispatch_source_preflight_path_must_match_current_preflight(tmp_path: Path):
    preflight = _preflight(tmp_path)
    dispatch = _dispatch(tmp_path)
    alternate = _write(
        tmp_path / "alternate-preflight.json",
        {
            "generated_at": _stamp(),
            "overall": "PASS",
            "human_gate_required": False,
            "executed_external_runtime": False,
            "checks": [],
        },
    )
    data = json.loads(dispatch.read_text(encoding="utf-8"))
    data["source_preflight"]["path"] = str(alternate)
    data["source_preflight"]["sha256"] = hashlib.sha256(alternate.read_bytes()).hexdigest()
    _write(dispatch, data)

    code, report = evaluate_readiness(
        mode="controlled_pilot",
        repo_root=tmp_path,
        local_evidence=_local_evidence(tmp_path),
        preflight=preflight,
        dispatch_plan=dispatch,
    )

    assert code == 1
    assert "path must match" in str(report["checks"]).lower()


def test_ready_dispatch_source_preflight_hash_mismatch_is_blocked(tmp_path: Path):
    preflight = _preflight(tmp_path)
    dispatch = _dispatch(tmp_path)
    data = json.loads(dispatch.read_text(encoding="utf-8"))
    data["source_preflight"]["sha256"] = "0" * 64
    _write(dispatch, data)

    code, report = evaluate_readiness(
        mode="controlled_pilot",
        repo_root=tmp_path,
        local_evidence=_local_evidence(tmp_path),
        preflight=preflight,
        dispatch_plan=dispatch,
    )

    assert code == 1
    assert "sha256 mismatch" in str(report["checks"]).lower()


def test_ready_dispatch_source_preflight_repo_escape_is_blocked(tmp_path: Path):
    preflight = _preflight(tmp_path)
    dispatch = _dispatch(tmp_path)
    outside = tmp_path.parent / "outside-source-preflight.json"
    _write(
        outside,
        {
            "generated_at": _stamp(),
            "overall": "PASS",
            "human_gate_required": False,
            "executed_external_runtime": False,
        },
    )
    data = json.loads(dispatch.read_text(encoding="utf-8"))
    data["source_preflight"]["path"] = str(outside)
    data["source_preflight"]["sha256"] = hashlib.sha256(outside.read_bytes()).hexdigest()
    _write(dispatch, data)
    try:
        code, report = evaluate_readiness(
            mode="controlled_pilot",
            repo_root=tmp_path,
            local_evidence=_local_evidence(tmp_path),
            preflight=preflight,
            dispatch_plan=dispatch,
        )
    finally:
        outside.unlink(missing_ok=True)

    assert code == 1
    assert "repository root" in str(report["checks"]).lower()


@pytest.mark.parametrize(
    ("field_value", "expected_text"),
    [
        (None, "non-empty iso timestamp"),
        (_stamp(_now() - timedelta(days=2)), "stale"),
        (_stamp(_now() + timedelta(hours=1)), "future"),
        ("not-a-time", "valid iso timestamp"),
    ],
)
def test_preflight_timestamp_failures_block_controlled_pilot(
    tmp_path: Path, field_value: str | None, expected_text: str
):
    preflight = _preflight(tmp_path)
    data = json.loads(preflight.read_text(encoding="utf-8"))
    if field_value is None:
        data.pop("generated_at")
    else:
        data["generated_at"] = field_value
    _write(preflight, data)

    code, report = evaluate_readiness(
        mode="controlled_pilot",
        repo_root=tmp_path,
        local_evidence=_local_evidence(tmp_path),
        preflight=preflight,
        dispatch_plan=_dispatch(tmp_path),
    )

    assert code == 1
    assert expected_text in str(report["checks"]).lower()


@pytest.mark.parametrize(
    ("field_value", "expected_text"),
    [
        (None, "non-empty iso timestamp"),
        (_stamp(_now() - timedelta(days=2)), "stale"),
        (_stamp(_now() + timedelta(hours=1)), "future"),
        ("not-a-time", "valid iso timestamp"),
    ],
)
def test_dispatch_timestamp_failures_block_controlled_pilot(
    tmp_path: Path, field_value: str | None, expected_text: str
):
    dispatch = _dispatch(tmp_path)
    data = json.loads(dispatch.read_text(encoding="utf-8"))
    if field_value is None:
        data.pop("generated_at")
    else:
        data["generated_at"] = field_value
    _write(dispatch, data)

    code, report = evaluate_readiness(
        mode="controlled_pilot",
        repo_root=tmp_path,
        local_evidence=_local_evidence(tmp_path),
        preflight=_preflight(tmp_path),
        dispatch_plan=dispatch,
    )

    assert code == 1
    assert expected_text in str(report["checks"]).lower()


def test_preflight_repo_escape_is_blocked(tmp_path: Path):
    outside = tmp_path.parent / "outside-preflight.json"
    _write(outside, {"generated_at": _stamp(), "overall": "PASS"})
    try:
        code, report = evaluate_readiness(
            mode="controlled_pilot",
            repo_root=tmp_path,
            local_evidence=_local_evidence(tmp_path),
            preflight=outside,
            dispatch_plan=_dispatch(tmp_path),
        )
    finally:
        outside.unlink(missing_ok=True)

    assert code == 1
    assert "repository root" in str(report["checks"]).lower()


def test_formal_use_requires_real_pilot_evidence(tmp_path: Path):
    code, report = evaluate_readiness(
        mode="formal_use",
        repo_root=tmp_path,
        local_evidence=_local_evidence(tmp_path),
        preflight=_preflight(tmp_path),
        dispatch_plan=_dispatch(tmp_path),
    )

    assert code == 2
    assert report["status"] == "HUMAN_REQUIRED"
    assert any(check["name"] == "real_multi_gpt_pilot" for check in report["checks"])


def test_formal_use_rejects_duplicate_session_ids(tmp_path: Path):
    code, report = evaluate_readiness(
        mode="formal_use",
        repo_root=tmp_path,
        local_evidence=_local_evidence(tmp_path),
        preflight=_preflight(tmp_path),
        dispatch_plan=_dispatch(tmp_path),
        pilot_evidence=_pilot(tmp_path, duplicate_sessions=True),
        production_authorization=_authorization(tmp_path),
    )

    assert code == 1
    assert report["status"] == "BLOCKED"
    assert "distinct" in str(report["checks"]).lower()


def test_formal_use_requires_referenced_session_evidence(tmp_path: Path):
    pilot = _pilot(tmp_path)
    data = json.loads(pilot.read_text(encoding="utf-8"))
    Path(data["agent_sessions"][0]["evidence_file"]).unlink()

    code, report = evaluate_readiness(
        mode="formal_use",
        repo_root=tmp_path,
        local_evidence=_local_evidence(tmp_path),
        preflight=_preflight(tmp_path),
        dispatch_plan=_dispatch(tmp_path),
        pilot_evidence=pilot,
        production_authorization=_authorization(tmp_path),
    )

    assert code == 1
    assert "evidence" in str(report["checks"]).lower()


@pytest.mark.parametrize(
    ("field_value", "expected_text"),
    [
        (None, "non-empty iso timestamp"),
        (_stamp(_now() - timedelta(days=2)), "stale"),
        (_stamp(_now() + timedelta(hours=1)), "future"),
        ("not-a-time", "valid iso timestamp"),
    ],
)
def test_formal_use_session_evidence_timestamp_failures_are_blocked(
    tmp_path: Path, field_value: str | None, expected_text: str
):
    pilot = _pilot(tmp_path)
    data = json.loads(pilot.read_text(encoding="utf-8"))
    evidence_path = Path(data["agent_sessions"][0]["evidence_file"])
    evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
    if field_value is None:
        evidence.pop("verified_at")
        data["agent_sessions"][0].pop("verified_at")
    else:
        evidence["verified_at"] = field_value
        data["agent_sessions"][0]["verified_at"] = field_value
    _write(evidence_path, evidence)
    _write(pilot, data)

    code, report = evaluate_readiness(
        mode="formal_use",
        repo_root=tmp_path,
        local_evidence=_local_evidence(tmp_path),
        preflight=_preflight(tmp_path),
        dispatch_plan=_dispatch(tmp_path),
        pilot_evidence=pilot,
        production_authorization=_authorization(tmp_path),
    )

    assert code == 1
    assert expected_text in str(report["checks"]).lower()


def test_formal_use_session_verified_at_mismatch_is_blocked(tmp_path: Path):
    pilot = _pilot(tmp_path)
    data = json.loads(pilot.read_text(encoding="utf-8"))
    data["agent_sessions"][0]["verified_at"] = _stamp(_now() - timedelta(minutes=1))
    _write(pilot, data)

    code, report = evaluate_readiness(
        mode="formal_use",
        repo_root=tmp_path,
        local_evidence=_local_evidence(tmp_path),
        preflight=_preflight(tmp_path),
        dispatch_plan=_dispatch(tmp_path),
        pilot_evidence=pilot,
        production_authorization=_authorization(tmp_path),
    )

    assert code == 1
    assert "verified_at mismatch" in str(report["checks"]).lower()


def test_formal_use_binds_pilot_to_exact_preflight_artifact(tmp_path: Path):
    preflight = _preflight(tmp_path)
    dispatch = _dispatch(tmp_path)
    pilot = _pilot(tmp_path)
    preflight.write_text(preflight.read_text(encoding="utf-8") + "\n", encoding="utf-8")

    code, report = evaluate_readiness(
        mode="formal_use",
        repo_root=tmp_path,
        local_evidence=_local_evidence(tmp_path),
        preflight=preflight,
        dispatch_plan=dispatch,
        pilot_evidence=pilot,
        production_authorization=_authorization(tmp_path),
    )

    assert code == 1
    assert "preflight sha256" in str(report["checks"]).lower()


def test_formal_use_requires_production_authorization(tmp_path: Path):
    code, report = evaluate_readiness(
        mode="formal_use",
        repo_root=tmp_path,
        local_evidence=_local_evidence(tmp_path),
        preflight=_preflight(tmp_path),
        dispatch_plan=_dispatch(tmp_path),
        pilot_evidence=_pilot(tmp_path, completed_at=_now() - timedelta(hours=3)),
    )

    assert code == 2
    assert report["status"] == "HUMAN_REQUIRED"


def test_formal_use_ready_with_complete_current_chain(tmp_path: Path):
    code, report = evaluate_readiness(
        mode="formal_use",
        repo_root=tmp_path,
        local_evidence=_local_evidence(tmp_path),
        preflight=_preflight(tmp_path),
        dispatch_plan=_dispatch(tmp_path),
        pilot_evidence=_pilot(tmp_path),
        production_authorization=_authorization(tmp_path),
    )

    assert code == 0
    assert report["status"] == "READY"
    assert report["mode"] == "formal_use"


def test_production_authorization_must_follow_pilot(tmp_path: Path):
    code, report = evaluate_readiness(
        mode="formal_use",
        repo_root=tmp_path,
        local_evidence=_local_evidence(tmp_path),
        preflight=_preflight(tmp_path),
        dispatch_plan=_dispatch(tmp_path),
        pilot_evidence=_pilot(tmp_path),
        production_authorization=_authorization(
            tmp_path,
            approved_at=_now() - timedelta(hours=2),
            expires_at=_now() + timedelta(hours=2),
        ),
    )

    assert code == 1
    assert "after pilot" in str(report["checks"]).lower()


def test_expired_production_authorization_is_human_required(tmp_path: Path):
    code, report = evaluate_readiness(
        mode="formal_use",
        repo_root=tmp_path,
        local_evidence=_local_evidence(tmp_path),
        preflight=_preflight(tmp_path),
        dispatch_plan=_dispatch(tmp_path),
        pilot_evidence=_pilot(tmp_path, completed_at=_now() - timedelta(hours=3)),
        production_authorization=_authorization(
            tmp_path,
            approved_at=_now() - timedelta(hours=2),
            expires_at=_now() - timedelta(hours=1),
        ),
    )

    assert code == 2
    assert report["status"] == "HUMAN_REQUIRED"


def test_expired_malformed_authorization_is_blocked(tmp_path: Path):
    authorization = _authorization(
        tmp_path,
        approved_at=_now() - timedelta(hours=2),
        expires_at=_now() - timedelta(hours=1),
    )
    data = json.loads(authorization.read_text(encoding="utf-8"))
    data["scope"] = "wrong-scope"
    _write(authorization, data)

    code, report = evaluate_readiness(
        mode="formal_use",
        repo_root=tmp_path,
        local_evidence=_local_evidence(tmp_path),
        preflight=_preflight(tmp_path),
        dispatch_plan=_dispatch(tmp_path),
        pilot_evidence=_pilot(tmp_path),
        production_authorization=authorization,
    )

    assert code == 1
    assert report["status"] == "BLOCKED"


def test_repo_escape_is_blocked(tmp_path: Path):
    outside = tmp_path.parent / "outside-readiness.json"
    _write(outside, {})
    try:
        code, report = evaluate_readiness(
            mode="local_governance", repo_root=tmp_path, local_evidence=outside
        )
    finally:
        outside.unlink(missing_ok=True)

    assert code == 1
    assert report["status"] == "BLOCKED"
    assert "repository root" in str(report["checks"])


@pytest.mark.parametrize("mode", ["local_governance", "controlled_pilot", "formal_use"])
def test_report_never_claims_external_runtime_execution(tmp_path: Path, mode: str):
    code, report = evaluate_readiness(
        mode=mode,
        repo_root=tmp_path,
        local_evidence=_local_evidence(tmp_path),
    )

    assert code in {0, 1, 2}
    assert report["executed_external_runtime"] is False
