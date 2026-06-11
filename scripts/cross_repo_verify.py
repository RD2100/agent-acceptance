#!/usr/bin/env python3
"""Human-gated cross-repo DevFrame verification.

Default mode is a dry plan that exits HUMAN_REQUIRED. Real cross-repo pytest
or smoke execution requires an explicit authorization record.
"""

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone

from cross_repo_authorization import validate_cross_repo_authorization

AUTH_SCOPE = "cross_repo_verify"

REPOS = {
    "agent-acceptance": {
        "path": "D:/agent-acceptance",
        "cmd": [sys.executable, "-m", "pytest", "tests/", "-q", "--tb=line"],
    },
    "devframe-control-plane": {
        "path": "D:/devframe-control-plane",
        "cmd": [sys.executable, "-m", "pytest", "tests/", "-q", "--tb=line"],
    },
    "dev-frame-opencode": {
        "path": "D:/dev-frame-opencode",
        "cmd": [sys.executable, "smoke_test.py"],
    },
}


def build_plan() -> dict:
    """Return commands that would run after human authorization."""
    return {
        name: {
            "path": cfg["path"],
            "cmd": cfg["cmd"],
        }
        for name, cfg in REPOS.items()
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


def _run_repo_command(cfg: dict) -> dict:
    """Run one authorized command and return structured fail-closed evidence."""
    try:
        completed = subprocess.run(
            cfg["cmd"],
            capture_output=True,
            text=True,
            cwd=cfg["path"],
            timeout=300,
        )
    except subprocess.TimeoutExpired as exc:
        return {
            "status": "FAIL",
            "exit": None,
            "tail": _tail(str(exc.output or ""), str(exc.stderr or "")),
            "error_type": "timeout",
            "timeout_seconds": exc.timeout,
        }
    except FileNotFoundError as exc:
        return {
            "status": "FAIL",
            "exit": None,
            "tail": str(exc),
            "error_type": "missing_cwd",
        }
    except OSError as exc:
        return {
            "status": "FAIL",
            "exit": None,
            "tail": str(exc),
            "error_type": "execution_exception",
        }

    return {
        "status": "PASS" if completed.returncode == 0 else "FAIL",
        "exit": completed.returncode,
        "tail": _tail(completed.stdout, completed.stderr),
        "error_type": None,
    }


def run_verification(
    execute: bool = False,
    authorization_record: str | None = None,
) -> tuple[int, dict]:
    """Run or plan cross-repo verification with fail-closed gating."""
    timestamp = datetime.now(timezone.utc).isoformat()
    plan = build_plan()

    if not execute:
        return 2, {
            "timestamp": timestamp,
            "overall": "HUMAN_REQUIRED",
            "human_gate_required": True,
            "executed": False,
            "reason": "cross-repo pytest/smoke execution is blocked by default",
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
    for name, cfg in REPOS.items():
        results[name] = _run_repo_command(cfg)

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
        description="Human-gated cross-repo DevFrame verification."
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Actually run cross-repo commands. Requires --authorization-record.",
    )
    parser.add_argument(
        "--authorization-record",
        default=None,
        help="Auditable JSON record authorizing scope=cross_repo_verify.",
    )
    args = parser.parse_args()

    exit_code, report = run_verification(
        execute=args.execute,
        authorization_record=args.authorization_record,
    )
    print(json.dumps(report, indent=2, ensure_ascii=False))
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
