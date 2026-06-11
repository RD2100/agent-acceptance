#!/usr/bin/env python3
"""Human-gated cross-repo smoke check.

Default mode prints a HUMAN_REQUIRED plan. Real cross-repo pytest execution
requires an explicit authorization record.
"""

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from cross_repo_authorization import validate_cross_repo_authorization

AUTH_SCOPE = "multi_repo_smoke"

REPOS = {
    "agent-acceptance": Path("D:/agent-acceptance"),
    "devframe-control-plane": Path("D:/devframe-control-plane"),
}
KNOWN_FAILURES = {"devframe-control-plane": 3}


def build_plan() -> dict:
    """Return commands that would run after human authorization."""
    return {
        name: {
            "path": str(path),
            "cmd": [sys.executable, "-m", "pytest", "tests/", "-q", "--tb=line"],
            "known_failures": KNOWN_FAILURES.get(name, 0),
        }
        for name, path in REPOS.items()
    }


def validate_authorization_record(record_path: str | None) -> tuple[bool, list[str]]:
    """Validate the narrow authorization record required for execution."""
    authorized, errors, _record = validate_cross_repo_authorization(
        record_path,
        required_scope=AUTH_SCOPE,
        required_repos=list(REPOS),
    )
    return authorized, errors


def _tail(stdout: str | None, stderr: str | None) -> str:
    text = (stdout or stderr or "").strip()
    return text.split("\n")[-1] if text else "error"


def _run_repo_smoke(name: str, path: Path) -> dict:
    """Run one authorized smoke command and return structured fail-closed evidence."""
    allowance = KNOWN_FAILURES.get(name, 0)
    try:
        completed = subprocess.run(
            [sys.executable, "-m", "pytest", "tests/", "-q", "--tb=line"],
            cwd=str(path),
            capture_output=True,
            text=True,
            timeout=120,
        )
    except subprocess.TimeoutExpired as exc:
        return {
            "status": "FAIL",
            "exit": None,
            "tail": _tail(str(exc.output or ""), str(exc.stderr or "")),
            "known_failure_allowance": allowance,
            "error_type": "timeout",
            "timeout_seconds": exc.timeout,
        }
    except FileNotFoundError as exc:
        return {
            "status": "FAIL",
            "exit": None,
            "tail": str(exc),
            "known_failure_allowance": allowance,
            "error_type": "missing_cwd",
        }
    except OSError as exc:
        return {
            "status": "FAIL",
            "exit": None,
            "tail": str(exc),
            "known_failure_allowance": allowance,
            "error_type": "execution_exception",
        }

    exit_code = completed.returncode
    status = (
        "PASS"
        if exit_code == 0
        else ("KNOWN_ISSUES" if name in KNOWN_FAILURES else "FAIL")
    )
    return {
        "status": status,
        "exit": exit_code,
        "tail": _tail(completed.stdout, completed.stderr),
        "known_failure_allowance": allowance,
        "error_type": None,
    }


def run_smoke(
    execute: bool = False,
    authorization_record: str | None = None,
) -> tuple[int, dict]:
    """Run or plan cross-repo smoke checks with fail-closed gating."""
    timestamp = datetime.now(timezone.utc).isoformat()
    plan = build_plan()

    if not execute:
        return 2, {
            "timestamp": timestamp,
            "overall": "HUMAN_REQUIRED",
            "human_gate_required": True,
            "executed": False,
            "reason": "cross-repo pytest execution is blocked by default",
            "planned_repos": plan,
        }

    authorized, auth_errors = validate_authorization_record(authorization_record)
    if not authorized:
        return 2, {
            "timestamp": timestamp,
            "overall": "HUMAN_REQUIRED",
            "human_gate_required": True,
            "executed": False,
            "errors": auth_errors,
            "planned_repos": plan,
        }

    results = {}
    for name, path in REPOS.items():
        results[name] = _run_repo_smoke(name, path)

    all_ok = all(v["status"] == "PASS" for v in results.values())
    return 0 if all_ok else 1, {
        "timestamp": timestamp,
        "overall": "PASS" if all_ok else "FAIL",
        "human_gate_required": True,
        "executed": True,
        "authorization_record": authorization_record,
        "repos": results,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Human-gated cross-repo smoke check."
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Actually run cross-repo commands. Requires --authorization-record.",
    )
    parser.add_argument(
        "--authorization-record",
        default=None,
        help="Auditable JSON record authorizing scope=multi_repo_smoke.",
    )
    args = parser.parse_args()

    exit_code, report = run_smoke(
        execute=args.execute,
        authorization_record=args.authorization_record,
    )
    print(json.dumps(report, indent=2, ensure_ascii=False))
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
