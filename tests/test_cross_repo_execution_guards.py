#!/usr/bin/env python3
"""Tests for human-gated cross-repo verification scripts."""

import json
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))

import cross_repo_verify
import multi_repo_smoke


class _Completed:
    def __init__(self, returncode=0, stdout="ok\n"):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = ""


def _authorization_record(scope: str, repos: list[str]) -> dict:
    return {
        "schema_version": "1.0.0",
        "authorized": True,
        "scope": scope,
        "allowed_repos": repos,
        "decision_maker": "human-reviewer",
        "decision_reason": "Authorize this bounded cross-repo verification run.",
        "approved_at": "2026-06-09T00:00:00+00:00",
        "expires_at": "2999-01-01T00:00:00+00:00",
        "risk_acknowledged": True,
    }


def test_cross_repo_verify_default_is_human_required(monkeypatch):
    """Default cross_repo_verify mode must not execute subprocesses."""
    monkeypatch.setattr(
        cross_repo_verify.subprocess,
        "run",
        lambda *args, **kwargs: pytest.fail("subprocess.run should not be called"),
    )

    exit_code, report = cross_repo_verify.run_verification()

    assert exit_code == 2
    assert report["overall"] == "HUMAN_REQUIRED"
    assert report["executed"] is False
    assert report["human_gate_required"] is True


def test_cross_repo_verify_execute_requires_authorization(monkeypatch):
    """--execute without a valid authorization record fails closed."""
    monkeypatch.setattr(
        cross_repo_verify.subprocess,
        "run",
        lambda *args, **kwargs: pytest.fail("subprocess.run should not be called"),
    )

    exit_code, report = cross_repo_verify.run_verification(execute=True)

    assert exit_code == 2
    assert report["overall"] == "HUMAN_REQUIRED"
    assert "authorization" in report["errors"][0]


def test_cross_repo_verify_authorized_executes(monkeypatch, tmp_path):
    """A valid narrow authorization permits the existing command plan to run."""
    calls = []

    def fake_run(*args, **kwargs):
        calls.append((args, kwargs))
        return _Completed()

    monkeypatch.setattr(cross_repo_verify.subprocess, "run", fake_run)
    auth = tmp_path / "auth.json"
    auth.write_text(
        json.dumps(_authorization_record("cross_repo_verify", list(cross_repo_verify.REPOS))),
        encoding="utf-8",
    )

    exit_code, report = cross_repo_verify.run_verification(
        execute=True,
        authorization_record=str(auth),
    )

    assert exit_code == 0
    assert report["overall"] == "PASS"
    assert report["executed"] is True
    assert len(calls) == len(cross_repo_verify.REPOS)


def test_cross_repo_verify_timeout_is_structured_fail(monkeypatch, tmp_path):
    """Authorized timeouts return FAIL JSON instead of bubbling an exception."""
    calls = []

    def fake_run(*args, **kwargs):
        calls.append((args, kwargs))
        if len(calls) == 1:
            raise cross_repo_verify.subprocess.TimeoutExpired(
                cmd=args[0],
                timeout=300,
                output="partial output\n",
            )
        return _Completed()

    monkeypatch.setattr(cross_repo_verify.subprocess, "run", fake_run)
    auth = tmp_path / "auth.json"
    auth.write_text(
        json.dumps(_authorization_record("cross_repo_verify", list(cross_repo_verify.REPOS))),
        encoding="utf-8",
    )

    exit_code, report = cross_repo_verify.run_verification(
        execute=True,
        authorization_record=str(auth),
    )

    first_repo = list(cross_repo_verify.REPOS)[0]
    assert exit_code == 1
    assert report["overall"] == "FAIL"
    assert report["executed"] is True
    assert report["repos"][first_repo]["status"] == "FAIL"
    assert report["repos"][first_repo]["error_type"] == "timeout"
    assert report["repos"][first_repo]["timeout_seconds"] == 300


def test_cross_repo_verify_missing_cwd_is_structured_fail(monkeypatch, tmp_path):
    """Authorized missing cwd errors return FAIL JSON."""
    def fake_run(*args, **kwargs):
        raise FileNotFoundError("missing cwd")

    monkeypatch.setattr(cross_repo_verify.subprocess, "run", fake_run)
    auth = tmp_path / "auth.json"
    auth.write_text(
        json.dumps(_authorization_record("cross_repo_verify", list(cross_repo_verify.REPOS))),
        encoding="utf-8",
    )

    exit_code, report = cross_repo_verify.run_verification(
        execute=True,
        authorization_record=str(auth),
    )

    assert exit_code == 1
    assert report["overall"] == "FAIL"
    assert report["executed"] is True
    assert all(repo["error_type"] == "missing_cwd" for repo in report["repos"].values())


def test_cross_repo_verify_execution_exception_is_structured_fail(monkeypatch, tmp_path):
    """Authorized OSError failures return FAIL JSON."""
    def fake_run(*args, **kwargs):
        raise OSError("execution failed")

    monkeypatch.setattr(cross_repo_verify.subprocess, "run", fake_run)
    auth = tmp_path / "auth.json"
    auth.write_text(
        json.dumps(_authorization_record("cross_repo_verify", list(cross_repo_verify.REPOS))),
        encoding="utf-8",
    )

    exit_code, report = cross_repo_verify.run_verification(
        execute=True,
        authorization_record=str(auth),
    )

    assert exit_code == 1
    assert report["overall"] == "FAIL"
    assert report["executed"] is True
    assert all(
        repo["error_type"] == "execution_exception"
        for repo in report["repos"].values()
    )


def test_cross_repo_verify_rejects_legacy_lightweight_auth(monkeypatch, tmp_path):
    """Legacy scope-only authorization is not auditable enough to execute."""
    monkeypatch.setattr(
        cross_repo_verify.subprocess,
        "run",
        lambda *args, **kwargs: pytest.fail("subprocess.run should not be called"),
    )
    auth = tmp_path / "legacy-auth.json"
    auth.write_text(
        json.dumps({
            "authorized": True,
            "scope": "cross_repo_verify",
            "allowed_repos": list(cross_repo_verify.REPOS),
        }),
        encoding="utf-8",
    )

    exit_code, report = cross_repo_verify.run_verification(
        execute=True,
        authorization_record=str(auth),
    )

    assert exit_code == 2
    assert report["overall"] == "HUMAN_REQUIRED"
    assert report["executed"] is False
    assert any("decision_maker" in err for err in report["errors"])


def test_cross_repo_verify_rejects_legacy_utf8_bom_auth(monkeypatch, tmp_path):
    """Windows UTF-8 BOM files parse, then fail on missing audit fields."""
    monkeypatch.setattr(
        cross_repo_verify.subprocess,
        "run",
        lambda *args, **kwargs: pytest.fail("subprocess.run should not be called"),
    )
    auth = tmp_path / "legacy-bom-auth.json"
    auth.write_text(
        json.dumps({
            "authorized": True,
            "scope": "cross_repo_verify",
            "allowed_repos": list(cross_repo_verify.REPOS),
        }),
        encoding="utf-8-sig",
    )

    exit_code, report = cross_repo_verify.run_verification(
        execute=True,
        authorization_record=str(auth),
    )

    assert exit_code == 2
    assert report["overall"] == "HUMAN_REQUIRED"
    assert report["executed"] is False
    assert not any("invalid JSON" in err for err in report["errors"])
    assert any("decision_maker" in err for err in report["errors"])


def test_cross_repo_verify_rejects_expired_auth(monkeypatch, tmp_path):
    """Expired authorization records fail closed."""
    monkeypatch.setattr(
        cross_repo_verify.subprocess,
        "run",
        lambda *args, **kwargs: pytest.fail("subprocess.run should not be called"),
    )
    auth_data = _authorization_record("cross_repo_verify", list(cross_repo_verify.REPOS))
    auth_data["expires_at"] = "2000-01-01T00:00:00+00:00"
    auth = tmp_path / "expired-auth.json"
    auth.write_text(json.dumps(auth_data), encoding="utf-8")

    exit_code, report = cross_repo_verify.run_verification(
        execute=True,
        authorization_record=str(auth),
    )

    assert exit_code == 2
    assert report["overall"] == "HUMAN_REQUIRED"
    assert report["executed"] is False
    assert any("expired" in err for err in report["errors"])


def test_multi_repo_smoke_default_is_human_required(monkeypatch):
    """Default multi_repo_smoke mode must not execute subprocesses."""
    monkeypatch.setattr(
        multi_repo_smoke.subprocess,
        "run",
        lambda *args, **kwargs: pytest.fail("subprocess.run should not be called"),
    )

    exit_code, report = multi_repo_smoke.run_smoke()

    assert exit_code == 2
    assert report["overall"] == "HUMAN_REQUIRED"
    assert report["executed"] is False
    assert report["human_gate_required"] is True


def test_multi_repo_smoke_execute_requires_authorization(monkeypatch):
    """--execute without authorization fails closed for multi_repo_smoke."""
    monkeypatch.setattr(
        multi_repo_smoke.subprocess,
        "run",
        lambda *args, **kwargs: pytest.fail("subprocess.run should not be called"),
    )

    exit_code, report = multi_repo_smoke.run_smoke(execute=True)

    assert exit_code == 2
    assert report["overall"] == "HUMAN_REQUIRED"
    assert "authorization" in report["errors"][0]


def test_multi_repo_smoke_authorized_executes(monkeypatch, tmp_path):
    """A valid narrow authorization permits the existing smoke plan to run."""
    calls = []

    def fake_run(*args, **kwargs):
        calls.append((args, kwargs))
        return _Completed()

    monkeypatch.setattr(multi_repo_smoke.subprocess, "run", fake_run)
    auth = tmp_path / "auth.json"
    auth.write_text(
        json.dumps(_authorization_record("multi_repo_smoke", list(multi_repo_smoke.REPOS))),
        encoding="utf-8",
    )

    exit_code, report = multi_repo_smoke.run_smoke(
        execute=True,
        authorization_record=str(auth),
    )

    assert exit_code == 0
    assert report["overall"] == "PASS"
    assert report["executed"] is True
    assert len(calls) == len(multi_repo_smoke.REPOS)


def test_multi_repo_smoke_known_issues_do_not_fake_green(monkeypatch, tmp_path):
    """Known issue labels cannot convert a non-zero repo run into overall PASS."""
    calls = []

    def fake_run(*args, **kwargs):
        calls.append((args, kwargs))
        cwd = kwargs.get("cwd", "")
        if str(cwd).replace("\\", "/").endswith("/devframe-control-plane"):
            return _Completed(returncode=1, stdout="3 failed, 10 passed\n")
        return _Completed(returncode=0, stdout="10 passed\n")

    monkeypatch.setattr(multi_repo_smoke.subprocess, "run", fake_run)
    auth = tmp_path / "auth.json"
    auth.write_text(
        json.dumps(_authorization_record("multi_repo_smoke", list(multi_repo_smoke.REPOS))),
        encoding="utf-8",
    )

    exit_code, report = multi_repo_smoke.run_smoke(
        execute=True,
        authorization_record=str(auth),
    )

    assert exit_code == 1
    assert report["overall"] == "FAIL"
    assert report["executed"] is True
    assert report["repos"]["devframe-control-plane"]["status"] == "KNOWN_ISSUES"
    assert report["repos"]["devframe-control-plane"]["known_failure_allowance"] == 3
    assert len(calls) == len(multi_repo_smoke.REPOS)


def test_multi_repo_smoke_timeout_is_structured_fail(monkeypatch, tmp_path):
    """Authorized smoke timeouts return structured FAIL evidence."""
    def fake_run(*args, **kwargs):
        raise multi_repo_smoke.subprocess.TimeoutExpired(
            cmd=args[0],
            timeout=120,
            output="partial smoke output\n",
        )

    monkeypatch.setattr(multi_repo_smoke.subprocess, "run", fake_run)
    auth = tmp_path / "auth.json"
    auth.write_text(
        json.dumps(_authorization_record("multi_repo_smoke", list(multi_repo_smoke.REPOS))),
        encoding="utf-8",
    )

    exit_code, report = multi_repo_smoke.run_smoke(
        execute=True,
        authorization_record=str(auth),
    )

    assert exit_code == 1
    assert report["overall"] == "FAIL"
    assert report["executed"] is True
    assert all(repo["status"] == "FAIL" for repo in report["repos"].values())
    assert all(repo["error_type"] == "timeout" for repo in report["repos"].values())


def test_multi_repo_smoke_missing_cwd_is_structured_fail(monkeypatch, tmp_path):
    """Authorized smoke missing cwd errors return structured FAIL evidence."""
    def fake_run(*args, **kwargs):
        raise FileNotFoundError("missing cwd")

    monkeypatch.setattr(multi_repo_smoke.subprocess, "run", fake_run)
    auth = tmp_path / "auth.json"
    auth.write_text(
        json.dumps(_authorization_record("multi_repo_smoke", list(multi_repo_smoke.REPOS))),
        encoding="utf-8",
    )

    exit_code, report = multi_repo_smoke.run_smoke(
        execute=True,
        authorization_record=str(auth),
    )

    assert exit_code == 1
    assert report["overall"] == "FAIL"
    assert report["executed"] is True
    assert all(repo["status"] == "FAIL" for repo in report["repos"].values())
    assert all(repo["error_type"] == "missing_cwd" for repo in report["repos"].values())


def test_multi_repo_smoke_execution_exception_is_structured_fail(monkeypatch, tmp_path):
    """Authorized smoke OSError failures return structured FAIL evidence."""
    def fake_run(*args, **kwargs):
        raise OSError("execution failed")

    monkeypatch.setattr(multi_repo_smoke.subprocess, "run", fake_run)
    auth = tmp_path / "auth.json"
    auth.write_text(
        json.dumps(_authorization_record("multi_repo_smoke", list(multi_repo_smoke.REPOS))),
        encoding="utf-8",
    )

    exit_code, report = multi_repo_smoke.run_smoke(
        execute=True,
        authorization_record=str(auth),
    )

    assert exit_code == 1
    assert report["overall"] == "FAIL"
    assert report["executed"] is True
    assert all(
        repo["error_type"] == "execution_exception"
        for repo in report["repos"].values()
    )


def test_multi_repo_smoke_rejects_unknown_repo_in_auth(monkeypatch, tmp_path):
    """Authorization repo scope must exactly match the script plan."""
    monkeypatch.setattr(
        multi_repo_smoke.subprocess,
        "run",
        lambda *args, **kwargs: pytest.fail("subprocess.run should not be called"),
    )
    auth_data = _authorization_record(
        "multi_repo_smoke",
        list(multi_repo_smoke.REPOS) + ["unexpected-repo"],
    )
    auth = tmp_path / "unknown-repo-auth.json"
    auth.write_text(json.dumps(auth_data), encoding="utf-8")

    exit_code, report = multi_repo_smoke.run_smoke(
        execute=True,
        authorization_record=str(auth),
    )

    assert exit_code == 2
    assert report["overall"] == "HUMAN_REQUIRED"
    assert report["executed"] is False
    assert any("unknown repo" in err for err in report["errors"])
