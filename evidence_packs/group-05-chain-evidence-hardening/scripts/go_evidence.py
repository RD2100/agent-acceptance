"""Create and finalize @go run evidence packages.

M4-M1-S1: deterministic final_batch_status synthesis from
guard_result, evidence_status, reviewer_verdict, and blocked_by.
"""

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None


# --- allowed value sets (mirrors task spec) ---
GUARD_RESULT_VALUES = frozenset({"pass", "blocked", "failed"})
EVIDENCE_STATUS_VALUES = frozenset({"pass", "failed", "missing", "invalid"})
REVIEWER_VERDICT_VALUES = frozenset({"accepted", "rejected", "blocked", "invalid", "timeout", "missing"})
FINAL_BATCH_STATUS_VALUES = frozenset({"pass", "blocked", "failed", "human_required"})

BLOCKED_BY_ORIGINS = frozenset({"policy", "workspace", "artifact", "review"})
BLOCKED_BY_CODES = frozenset({
    "TaskSpec_boundary", "human_required", "new_dirty_change",
    "schema_invalid", "evidence_missing", "review_artifact_missing",
    "reviewer_invalid", "reviewer_rejected", "reviewer_timeout",
})


def utc_now():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def run_command(command, cwd):
    return subprocess.run(
        command,
        cwd=str(cwd),
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
    )


def write_text(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


# ---------------------------------------------------------------------------
# Signal extraction helpers
# ---------------------------------------------------------------------------

def _determine_guard_result(safety_path):
    """Read guard_result from safety-report.json.

    Handles both the standard guard format (exit_code) and the
    compliance-report format (overall_verdict + blocking_items).
    Returns (guard_result: str, blocked_by: list[dict]).
    """
    if not safety_path.is_file():
        return "failed", [{"origin": "artifact", "code": "evidence_missing",
                           "detail": "safety-report.json not found"}]

    try:
        safety = json.loads(safety_path.read_text(encoding="utf-8"))
    except Exception as exc:
        return "failed", [{"origin": "artifact", "code": "schema_invalid",
                           "detail": f"safety-report.json malformed: {exc}"}]

    # Standard guard format (from go_evidence.py guard)
    exit_code = safety.get("exit_code")
    if exit_code is not None:
        if exit_code == 0:
            return "pass", []
        blocked_by = []
        code = "TaskSpec_boundary" if safety.get("blocker_classification") == "TaskSpec_boundary" else "new_dirty_change"
        blocked_by.append({
            "origin": "policy",
            "code": code,
            "detail": safety.get("blocker_detail") or f"Guard exit code {exit_code}",
        })
        return "blocked", blocked_by

    # Compliance-report format
    verdict = str(safety.get("overall_verdict", "")).strip().upper()
    if "BLOCKED" in verdict or "FAIL" in verdict:
        blocked_by = []
        for item in safety.get("blocking_items", []):
            blocked_by.append({
                "origin": "workspace",
                "code": "new_dirty_change",
                "detail": item.get("issue", str(item)),
            })
        return "blocked", blocked_by

    return "pass", []


def _determine_reviewer_verdict(review_yaml_path):
    """Read reviewer_verdict from review.yaml.

    Returns (reviewer_verdict: str, blocked_by: list[dict]).
    Maps review.yaml verdict to canonical reviewer_verdict values.
    """
    if not review_yaml_path.is_file():
        return "missing", [{"origin": "artifact", "code": "review_artifact_missing",
                            "detail": "review.yaml not found"}]

    try:
        review = yaml.safe_load(review_yaml_path.read_text(encoding="utf-8")) or {}
    except Exception as exc:
        return "invalid", [{"origin": "artifact", "code": "schema_invalid",
                            "detail": f"review.yaml malformed: {exc}"}]

    verdict_raw = str(review.get("verdict", "")).strip().lower()
    verdict_map = {
        "pass": "accepted",
        "blocked": "blocked",
        "fail": "rejected",
        "escalate": "blocked",
    }
    mapped = verdict_map.get(verdict_raw, "invalid")

    if verdict_raw == "escalate":
        blocked_by = [{
            "origin": "policy",
            "code": "human_required",
            "detail": review.get("verdict_reason") or "Reviewer escalated: requires human decision",
        }]
        for f in review.get("findings", []):
            if not isinstance(f, dict):
                continue
            severity = str(f.get("severity", "")).upper()
            status = str(f.get("status", "")).strip().lower()
            if severity in ("P0", "P1") and status not in ("resolved", "false_positive"):
                blocked_by.append({
                    "origin": "review",
                    "code": "reviewer_rejected",
                    "detail": f.get("title", "Unresolved P0/P1 finding"),
                })
        return "blocked", blocked_by

    if mapped in ("blocked", "rejected", "invalid"):
        blocked_by = []
        for f in review.get("findings", []):
            if not isinstance(f, dict):
                continue
            severity = str(f.get("severity", "")).upper()
            status = str(f.get("status", "")).strip().lower()
            if severity in ("P0", "P1") and status not in ("resolved", "false_positive"):
                code = "reviewer_invalid" if mapped == "invalid" else "reviewer_rejected"
                blocked_by.append({
                    "origin": "review",
                    "code": code,
                    "detail": f.get("title", "Unresolved P0/P1 finding"),
                })
        if not blocked_by:
            code = "reviewer_invalid" if mapped == "invalid" else "reviewer_rejected"
            blocked_by.append({
                "origin": "review",
                "code": code,
                "detail": f"Reviewer verdict: {verdict_raw}",
            })
        return mapped, blocked_by

    return mapped, []


# ---------------------------------------------------------------------------
# Deterministic status synthesis (M4-M1-S1 precedence order)
# ---------------------------------------------------------------------------

def synthesize_final_status(guard_result, evidence_status, reviewer_verdict, blocked_by):
    """Apply deterministic synthesis precedence per M4-M1-S1.

    Order:
      1. Malformed/missing artifacts      → failed
      2. guard_result=blocked              → blocked
      3. human_required in blocked_by      → human_required
      4. reviewer_verdict in {blocked, rejected} → blocked
      5. evidence_status in {failed, invalid, missing} → failed (prevents pass)
      6. All pass                          → pass
      7. Otherwise                         → blocked (evidence=pass alone insufficient)
    """
    # 1 — fail closed on malformed / missing artifacts
    if evidence_status in ("invalid", "missing"):
        return "failed"
    if guard_result == "failed":
        return "failed"
    if reviewer_verdict in ("invalid", "timeout", "missing"):
        return "failed"

    # 2 — guard blocked forces blocked
    if guard_result == "blocked":
        return "blocked"

    # 3 — human_required (must precede reviewer blocked; escalate triggers this)
    for entry in blocked_by:
        if entry.get("code") == "human_required":
            return "human_required"

    # 4 — reviewer blocked / rejected forces blocked
    if reviewer_verdict in ("blocked", "rejected"):
        return "blocked"

    # 5 — evidence failure prevents pass
    if evidence_status == "failed":
        return "failed"

    # 6 — all clear
    if guard_result == "pass" and evidence_status == "pass" and reviewer_verdict == "accepted":
        return "pass"

    # 7 — default: blocked (evidence=pass alone never sufficient)
    return "blocked"


def format_report_yaml_front_matter(payload):
    """Render structured fields as a YAML-like front-matter block."""
    lines = ["---"]
    for key in ("final_batch_status", "guard_result", "evidence_status", "reviewer_verdict"):
        lines.append(f"{key}: {payload.get(key, 'unknown')}")
    blocked_by = payload.get("blocked_by", [])
    if blocked_by:
        lines.append("blocked_by:")
        for entry in blocked_by:
            o = entry.get("origin", "?")
            c = entry.get("code", "?")
            d = entry.get("detail", "")
            lines.append(f"  - origin: {o}")
            lines.append(f"    code: {c}")
            lines.append(f"    detail: {d}")
    else:
        lines.append("blocked_by: []")
    lines.append(f"generated_at: {payload.get('generated_at', '')}")
    lines.append(f"evidence_dir: {payload.get('evidence_dir', '')}")
    lines.append("---")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

def cmd_init(args, repo_root):
    run_dir = Path(args.run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)

    diff = run_command(
        ["git", "diff", "--binary", "HEAD", "--", ".", ":(exclude)runs/**"],
        repo_root,
    )
    write_text(run_dir / "diff.patch", diff.stdout or "\n")

    if not (run_dir / "test-output.md").exists():
        write_text(
            run_dir / "test-output.md",
            "# Test Output\n\nNo test output captured yet. Tester must replace this file.\n",
        )

    chain = {
        "run_id": args.run_id,
        "task_file": args.task,
        "executor_id": args.executor_id,
        "reviewer_id": None,
        "created_at": utc_now(),
        "producer": "tools/go_evidence.py init",
    }
    write_json(run_dir / "chain-evidence.json", chain)
    print(f"Evidence initialized: {run_dir}")


def _classify_guard_blocker(stdout_text):
    """Parse ai_guard.py task output to classify blocker type.

    Returns (blocker_classification: str, blocker_detail: str).
    """
    if "SCOPE:" in stdout_text:
        return "TaskSpec_boundary", "Files modified outside TaskSpec allow_write"
    if "DENIED:" in stdout_text:
        return "TaskSpec_boundary", "Files on deny list"
    if "SECRET:" in stdout_text:
        return "TaskSpec_boundary", "Secret pattern detected"
    return "new_dirty_change", "Guard blocked (unclassified)"


def cmd_guard(args, repo_root):
    run_dir = Path(args.run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)

    command = ["python", "tools/ai_guard.py", "task"]
    if args.task:
        command.append(args.task)

    result = run_command(command, repo_root)
    payload = {
        "generated_at": utc_now(),
        "producer": "tools/go_evidence.py guard",
        "command": " ".join(command),
        "exit_code": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
    }
    if result.returncode != 0:
        classification, detail = _classify_guard_blocker(result.stdout)
        payload["blocker_classification"] = classification
        payload["blocker_detail"] = detail
    write_json(run_dir / "safety-report.json", payload)
    print(result.stdout, end="")
    print(result.stderr, end="", file=sys.stderr)
    return result.returncode


def cmd_finalize(args, repo_root):
    run_dir = Path(args.run_dir)
    review_yaml_path = run_dir / "review.yaml"
    chain_path = run_dir / "chain-evidence.json"
    safety_path = run_dir / "safety-report.json"

    # 1 — Update chain-evidence.json with reviewer metadata
    if yaml and review_yaml_path.is_file() and chain_path.is_file():
        try:
            review = yaml.safe_load(review_yaml_path.read_text(encoding="utf-8")) or {}
            chain = json.loads(chain_path.read_text(encoding="utf-8"))
            chain["reviewer_id"] = review.get("reviewer_id")
            chain["reviewer_role"] = review.get("reviewer_role")
            chain["reviewed_at"] = utc_now()
            write_json(chain_path, chain)
        except Exception:
            pass

    # 2 — Run ai_guard evidence
    command = ["python", "tools/ai_guard.py", "evidence", "--out", str(run_dir)]
    result = run_command(command, repo_root)

    # 3 — Extract signals
    guard_result, guard_blocked_by = _determine_guard_result(safety_path)
    evidence_status = "pass" if result.returncode == 0 else "failed"
    # Prefer structured evidence-report.json when available
    evidence_report_path = run_dir / "evidence-report.json"
    if evidence_report_path.is_file():
        try:
            er = json.loads(evidence_report_path.read_text(encoding="utf-8"))
            if er.get("evidence_status") in EVIDENCE_STATUS_VALUES:
                evidence_status = er["evidence_status"]
        except Exception:
            pass
    reviewer_verdict, review_blocked_by = _determine_reviewer_verdict(review_yaml_path)

    blocked_by = guard_blocked_by + review_blocked_by

    # 4 — Synthesize final_batch_status
    final = synthesize_final_status(guard_result, evidence_status, reviewer_verdict, blocked_by)

    if chain_path.is_file():
        try:
            chain = json.loads(chain_path.read_text(encoding="utf-8"))
            chain["rerun_verified_at"] = now = utc_now()
            chain["rerun_summary"] = (
                f"guard={guard_result}; evidence={evidence_status}; "
                f"reviewer={reviewer_verdict}; final={final}"
            )
            write_json(chain_path, chain)
        except Exception:
            pass

    # 5 — Write final-report.md with structured front-matter
    now = utc_now()
    front = format_report_yaml_front_matter({
        "final_batch_status": final,
        "guard_result": guard_result,
        "evidence_status": evidence_status,
        "reviewer_verdict": reviewer_verdict,
        "blocked_by": blocked_by,
        "generated_at": now,
        "evidence_dir": str(run_dir),
    })

    guard_stdout = result.stdout.strip()
    guard_stderr = result.stderr.strip()

    parts = [
        front,
        "",
        "# Final Report",
        "",
        "## Signals",
        "",
        f"| Signal | Value |",
        f"|--------|-------|",
        f"| final_batch_status | {final} |",
        f"| guard_result | {guard_result} |",
        f"| evidence_status | {evidence_status} |",
        f"| reviewer_verdict | {reviewer_verdict} |",
        "",
        "## Blocked By",
        "",
    ]
    if blocked_by:
        for b in blocked_by:
            parts.append(f"- origin: `{b.get('origin', '?')}`  code: `{b.get('code', '?')}`  detail: {b.get('detail', '')}")
    else:
        parts.append("None")
    parts.append("")
    parts.append("## Evidence Validation Output")
    parts.append("")
    parts.append("```text")
    parts.append(guard_stdout or "(empty)")
    if guard_stderr:
        parts.append(guard_stderr)
    parts.append("```")
    parts.append("")
    parts.append(f"*Generated at: {now}*  ")
    parts.append(f"*Evidence directory: {run_dir}*  ")
    parts.append(f"*Guard command: {' '.join(command)}*  ")

    write_text(run_dir / "final-report.md", "\n".join(parts))

    print(result.stdout, end="")
    print(result.stderr, end="", file=sys.stderr)

    # 6 — Exit code mirrors final_batch_status
    exit_map = {"pass": 0, "blocked": 1, "failed": 2, "human_required": 3}
    return exit_map.get(final, 1)


def main():
    parser = argparse.ArgumentParser(description="Create @go evidence packages")
    parser.add_argument("--repo-root", default=".", help="Repository root")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init")
    init_parser.add_argument("run_dir")
    init_parser.add_argument("--run-id", required=True)
    init_parser.add_argument("--task", required=True)
    init_parser.add_argument("--executor-id", required=True)

    guard_parser = subparsers.add_parser("guard")
    guard_parser.add_argument("run_dir")
    guard_parser.add_argument("--task")

    finalize_parser = subparsers.add_parser("finalize")
    finalize_parser.add_argument("run_dir")

    args = parser.parse_args()
    repo_root = Path(args.repo_root).resolve()

    if args.command == "init":
        cmd_init(args, repo_root)
        return 0
    if args.command == "guard":
        return cmd_guard(args, repo_root)
    if args.command == "finalize":
        return cmd_finalize(args, repo_root)
    return 2


if __name__ == "__main__":
    sys.exit(main())
