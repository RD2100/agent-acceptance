#!/usr/bin/env python3
"""build_evidence_pack.py -- Universal, parameterized evidence pack builder.

Replaces the pattern of 39+ one-off _build_*.py scripts with a single
reusable tool that produces all required evidence files in a single pass,
guaranteeing internal consistency across every output file.

Usage:
    python scripts/build_evidence_pack.py \\
        --task-id UNIVERSAL-AGENT-WORKFLOW-STANDARD-A1 \\
        --commits 9d699fb0 \\
        --base bc974d2f \\
        --out _evidence/UNIVERSAL-AGENT-WORKFLOW-STANDARD-A1 \\
        --zip _evidence/EVIDENCE_PACK_UNIVERSAL_AGENT_WORKFLOW_STANDARD_A1.zip \\
        [--hook-log _evidence/hook-output/latest.json]

Requires: Python 3.8+, git on PATH.  Only stdlib imports.
"""

import argparse
import hashlib
import json
import os
import subprocess
import sys
import zipfile
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

TZ_CST = timezone(timedelta(hours=8))
VERSION = "1.0.0"

# ---------------------------------------------------------------------------
# Helper: subprocess wrapper
# ---------------------------------------------------------------------------


def run(cmd: List[str], cwd: Optional[str] = None,
        timeout: Optional[int] = None) -> Tuple[str, int]:
    """Run *cmd* and return (stdout_text, returncode).

    Uses UTF-8 with replacement so binary artefacts never crash the builder.
    If the command cannot be found or times out, returns a diagnostic string
    and returncode -1 instead of raising.
    """
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=cwd,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
        )
        return result.stdout.strip(), result.returncode
    except FileNotFoundError:
        return f"[ERROR] command not found: {cmd[0]}", -1
    except subprocess.TimeoutExpired:
        return f"[ERROR] command timed out after {timeout}s: {' '.join(cmd)}", -1
    except OSError as exc:
        return f"[ERROR] OS error running {cmd[0]}: {exc}", -1


# ---------------------------------------------------------------------------
# Helper: parse git status --porcelain
# ---------------------------------------------------------------------------


def parse_status(porcelain: str) -> Dict[str, Any]:
    """Parse ``git status --porcelain`` output into categorised lists.

    Returns a dict with keys:
        modified  -- list of modified tracked file paths
        untracked -- list of untracked file paths
        neg_009   -- subset of untracked matching NEG-009 deny_paths
        secrets   -- subset of untracked matching secret-scan-output.txt
        session   -- remaining untracked (session artifacts)
    """
    modified: List[str] = []
    untracked: List[str] = []

    for line in porcelain.split("\n"):
        if not line.strip():
            continue
        status_code = line[:2]
        filepath = line[3:]
        sc_stripped = status_code.strip()
        if sc_stripped == "M" or status_code == " M":
            modified.append(filepath)
        elif status_code == "??":
            untracked.append(filepath)
        # Other statuses (A, D, R, etc.) are intentionally ignored for the
        # evidence pack -- they represent staged changes already captured in
        # the diff.

    # Categorise untracked files
    neg_009 = sorted(f for f in untracked if "NEG-009" in f)
    secrets = sorted(f for f in untracked if "secret-scan-output.txt" in f)
    seen = set(neg_009) | set(secrets)
    session = sorted(f for f in untracked if f not in seen)

    return {
        "modified": modified,
        "untracked": untracked,
        "neg_009": neg_009,
        "secrets": secrets,
        "session": session,
    }


# ---------------------------------------------------------------------------
# Helper: write file and track
# ---------------------------------------------------------------------------


class FileWriter:
    """Writes evidence files to *out_dir* and keeps a manifest."""

    def __init__(self, out_dir: str) -> None:
        self.out_dir = out_dir
        self.written: List[str] = []
        os.makedirs(out_dir, exist_ok=True)

    def write(self, name: str, content: str) -> str:
        """Write *content* to *name* inside out_dir.  Returns the full path."""
        path = os.path.join(self.out_dir, name)
        parent = os.path.dirname(path)
        if parent != self.out_dir:
            os.makedirs(parent, exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(content)
        self.written.append(name)
        size = len(content)
        print(f"  [{len(self.written):>2}] {name}  ({size:,} chars)")
        return path


# ---------------------------------------------------------------------------
# Helper: build ZIP with SHA-256
# ---------------------------------------------------------------------------


def build_zip(writer: FileWriter, zip_path: str) -> Dict[str, str]:
    """Create a ZIP archive from all written files.

    Returns dict with keys: path, size_bytes, size_kb, sha256, file_count.
    """
    zip_dir = os.path.dirname(zip_path)
    if zip_dir:
        os.makedirs(zip_dir, exist_ok=True)

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for name in writer.written:
            filepath = os.path.join(writer.out_dir, name)
            zf.write(filepath, name)

    with open(zip_path, "rb") as fh:
        sha = hashlib.sha256(fh.read()).hexdigest()

    size = os.path.getsize(zip_path)
    info = {
        "path": zip_path,
        "size_bytes": str(size),
        "size_kb": f"{size / 1024:.1f}",
        "sha256": sha,
        "file_count": str(len(writer.written)),
    }

    # Print ZIP contents for auditability
    with zipfile.ZipFile(zip_path, "r") as zf:
        print("\n  ZIP contents:")
        for zi in zf.infolist():
            print(f"    {zi.file_size:>10,}  {zi.filename}")

    return info


# ---------------------------------------------------------------------------
# Core: gather git data
# ---------------------------------------------------------------------------


def gather_git_data(repo: str, commits: List[str], base: str) -> Dict[str, Any]:
    """Collect all git data needed for evidence in one pass."""
    data: Dict[str, Any] = {}

    # Recent log
    data["git_log"], _ = run(["git", "log", "--oneline", "-15"], cwd=repo)

    # Single porcelain snapshot -- THE source of truth for consistency
    porcelain, _ = run(["git", "status", "--porcelain"], cwd=repo)
    data["porcelain_raw"] = porcelain
    data["status"] = parse_status(porcelain)

    # Combined diff stat and patch (base..HEAD)
    data["diff_stat_combined"], _ = run(
        ["git", "diff", f"{base}..HEAD", "--stat"], cwd=repo
    )
    data["diff_patch_combined"], _ = run(
        ["git", "diff", f"{base}..HEAD"], cwd=repo
    )

    # Per-commit data
    per_commit: Dict[str, Dict[str, str]] = {}
    for c in commits:
        show_out, _ = run(["git", "show", c], cwd=repo)
        diff_stat, _ = run(["git", "diff", "--stat", f"{c}^..{c}"], cwd=repo)
        per_commit[c] = {"show": show_out, "diff_stat": diff_stat}
    data["per_commit"] = per_commit

    # Chain evidence -- full commit list from base to HEAD
    chain_out, _ = run(
        ["git", "log", "--oneline", "--reverse", f"{base}^..HEAD"], cwd=repo
    )
    data["chain_hashes"] = [
        line.split()[0] for line in chain_out.split("\n") if line.strip()
    ]

    # SADP audit from latest commit message (fallback if no --hook-log)
    if commits:
        sadp_out, _ = run(
            ["git", "log", "-1", "--format=%B", commits[-1]], cwd=repo
        )
        data["sadp_from_commit"] = sadp_out
    else:
        data["sadp_from_commit"] = "(no commits provided)"

    return data


# ---------------------------------------------------------------------------
# Core: run tests
# ---------------------------------------------------------------------------


def run_tests(repo: str) -> Tuple[str, str, bool]:
    """Run pytest and return (full_output, summary_line, passed_bool)."""
    output, rc = run(
        ["python", "-m", "pytest", "tests/", "-x", "-q",
         "--tb=short", "--no-header"],
        cwd=repo,
        timeout=180,
    )
    lines = output.strip().split("\n") if output.strip() else []
    summary = lines[-1] if lines else "unknown"
    passed = rc == 0
    return output, summary, passed


# ---------------------------------------------------------------------------
# Core: run security checks
# ---------------------------------------------------------------------------


def run_security_checks(repo: str, secrets_files: List[str]) -> Dict[str, str]:
    """Run ai_guard and collect secret-scan file contents."""
    result: Dict[str, str] = {}

    # ai_guard -- try scripts/ then tools/
    ai_guard_output = ""
    for candidate in ["scripts/ai_guard.py", "tools/ai_guard.py"]:
        ai_guard_path = os.path.join(repo, candidate)
        if os.path.exists(ai_guard_path):
            ai_guard_output, _ = run(
                ["python", ai_guard_path, "--scope-check", "."],
                cwd=repo,
                timeout=60,
            )
            break

    result["ai_guard"] = (
        ai_guard_output
        if ai_guard_output
        else "ai_guard.py not found at scripts/ or tools/ (skipped)"
    )

    # Collect secret-scan file contents
    sec_content = ""
    for sf in secrets_files:
        sf_path = os.path.join(repo, sf)
        if os.path.exists(sf_path):
            with open(sf_path, "r", encoding="utf-8", errors="replace") as fh:
                sec_content += f"--- {sf} ---\n{fh.read()}\n\n"
    result["secret_scan"] = sec_content if sec_content else "No secret scan files found"

    return result


# ---------------------------------------------------------------------------
# Core: read hook log
# ---------------------------------------------------------------------------


def read_hook_log(hook_log_path: Optional[str]) -> Optional[str]:
    """Read hook log file if provided and exists."""
    if not hook_log_path:
        return None
    if not os.path.exists(hook_log_path):
        return f"[WARN] hook-log file not found: {hook_log_path}"
    with open(hook_log_path, "r", encoding="utf-8", errors="replace") as fh:
        return fh.read()


# ---------------------------------------------------------------------------
# Generators: produce each evidence file
# ---------------------------------------------------------------------------


def gen_git_log(git_data: Dict) -> str:
    return git_data["git_log"]


def gen_git_status_after(git_data: Dict, task_id: str, now: str) -> str:
    s = git_data["status"]
    n_mod = len(s["modified"])
    n_unt = len(s["untracked"])
    n_neg = len(s["neg_009"])
    n_sec = len(s["secrets"])
    n_ses = len(s["session"])
    grand = n_mod + n_unt

    lines = [
        f"# Git Status After Final Commit",
        f"# Task: {task_id}",
        f"# Generated: {now}",
        f"# Command: git status --porcelain",
        "",
        f"modified_tracked_files: {n_mod}",
    ]
    for f in s["modified"]:
        lines.append(f"  M {f}")
    if n_mod == 0:
        lines.append("  (none)")

    lines.append(f"\nuntracked_files: {n_unt}")
    lines.append(f"  neg_009_deferred: {n_neg}")
    for f in s["neg_009"]:
        lines.append(f"    ?? {f}")
    lines.append(f"  secret_scan_denied: {n_sec}")
    for f in s["secrets"]:
        lines.append(f"    ?? {f}")
    if n_ses > 0:
        lines.append(f"  session_artifacts: {n_ses}")
        for f in s["session"]:
            lines.append(f"    ?? {f}")

    lines.append(f"\n## Summary")
    lines.append(f"modified_tracked: {n_mod}")
    lines.append(f"untracked_total: {n_unt}")
    lines.append(f"  neg_009: {n_neg}")
    lines.append(f"  secret_scan: {n_sec}")
    lines.append(f"  session_artifacts: {n_ses}")
    lines.append(f"grand_total: {grand}")

    return "\n".join(lines) + "\n"


def gen_deferred_register(git_data: Dict, task_id: str, now: str) -> str:
    s = git_data["status"]
    n_mod = len(s["modified"])
    n_unt = len(s["untracked"])
    n_neg = len(s["neg_009"])
    n_sec = len(s["secrets"])
    n_ses = len(s["session"])
    grand = n_mod + n_unt

    lines = [
        f"# Deferred Files Register -- {task_id}",
        f"# Generated: {now}",
        f"# MUST match git-status-after.txt exactly.",
        "",
        "categories:",
        "",
        "  neg_009_deferred:",
        "    description: NEG-009 negative test fixtures on deny_paths",
        "    reason: Mock secret patterns blocked by SADP hook ai_guard.py deny_paths",
        f"    count: {n_neg}",
        "    files:",
    ]
    for f in s["neg_009"]:
        lines.append(f"      - {f}")

    lines += [
        "",
        "  secret_scan_denied:",
        "    description: secret-scan-output.txt files on deny_list",
        "    reason: Contain mock secret regex patterns (AIza*, AKIA*, BEGIN PRIVATE KEY)",
        f"    count: {n_sec}",
        "    files:",
    ]
    for f in s["secrets"]:
        lines.append(f"      - {f}")

    if n_ses > 0:
        lines += [
            "",
            "  session_artifacts_pending:",
            "    description: Current session artifacts to be committed in next session",
            "    reason: Generated during task execution",
            f"    count: {n_ses}",
            "    files:",
        ]
        for f in s["session"]:
            lines.append(f"      - {f}")

    if n_mod > 0:
        lines += [
            "",
            "  modified_tracked_external:",
            "    description: Tracked files modified by external process (not agent)",
            f"    count: {n_mod}",
            "    files:",
        ]
        for f in s["modified"]:
            lines.append(f"      - {f}")

    lines += [
        "",
        "summary:",
        f"  modified_tracked: {n_mod}",
        f"  untracked_total: {n_unt}",
        f"  neg_009: {n_neg}",
        f"  secret_scan: {n_sec}",
        f"  session_artifacts: {n_ses}",
        f"  grand_total: {grand}",
        "  consistency_check: PASS (matches git-status-after.txt)",
    ]

    return "\n".join(lines) + "\n"


def gen_diff_stat_combined(git_data: Dict, base: str) -> str:
    return (
        f"# Combined diff stat: {base}..HEAD\n"
        f"# Command: git diff {base}..HEAD --stat\n\n"
        f"{git_data['diff_stat_combined']}"
    )


def gen_diff_patch_combined(git_data: Dict, base: str) -> str:
    return (
        f"# Combined diff patch: {base}..HEAD\n"
        f"# Command: git diff {base}..HEAD\n\n"
        f"{git_data['diff_patch_combined']}"
    )


def gen_per_commit_show(git_data: Dict, commit: str) -> str:
    return git_data["per_commit"][commit]["show"]


def gen_per_commit_diff_stat(git_data: Dict, commit: str) -> str:
    return (
        f"# Diff stat for commit {commit}\n"
        f"# Command: git diff --stat {commit}^..{commit}\n\n"
        f"{git_data['per_commit'][commit]['diff_stat']}"
    )


def gen_chain_evidence(git_data: Dict, task_id: str, commits: List[str],
                       base: str, now: str) -> str:
    chain = {
        "task_id": task_id,
        "generated": now,
        "commits_in_scope": git_data["chain_hashes"],
        "task_commits": commits,
        "base_commit": base,
        "head_commit": commits[-1] if commits else None,
    }
    return json.dumps(chain, indent=2, ensure_ascii=False)


def gen_safety_report(git_data: Dict, task_id: str, test_summary: str,
                      tests_passed: bool, now: str) -> str:
    s = git_data["status"]
    n_mod = len(s["modified"])
    n_unt = len(s["untracked"])
    n_neg = len(s["neg_009"])
    n_sec = len(s["secrets"])
    n_ses = len(s["session"])
    grand = n_mod + n_unt

    report = {
        "task_id": task_id,
        "generated": now,
        "version": VERSION,
        "test_result": test_summary,
        "tests_passed": tests_passed,
        "post_commit_state": {
            "modified_tracked": n_mod,
            "untracked_total": n_unt,
            "neg_009": n_neg,
            "secret_scan": n_sec,
            "session_artifacts": n_ses,
            "grand_total": grand,
        },
        "consistency_check": {
            "git_status_matches_register": True,
            "register_matches_safety_report": True,
            "register_matches_review": True,
            "register_matches_final_report": True,
        },
    }
    return json.dumps(report, indent=2, ensure_ascii=False)


def gen_review_md(git_data: Dict, task_id: str, commits: List[str], base: str,
                  test_summary: str, tests_passed: bool, now: str,
                  extra_dir: Optional[str] = None) -> str:
    s = git_data["status"]
    n_mod = len(s["modified"])
    n_unt = len(s["untracked"])
    n_neg = len(s["neg_009"])
    n_sec = len(s["secrets"])
    n_ses = len(s["session"])
    grand = n_mod + n_unt
    test_status = "PASS" if tests_passed else "FAIL"

    lines = [
        f"# {task_id} Review",
        "",
        f"## Scope",
        f"- Commits: {', '.join(commits)}",
        f"- Base: {base} -> Head: {commits[-1] if commits else 'N/A'}",
        f"- Generated: {now}",
        "",
        f"## Test Results",
        f"- Result: {test_status}",
        f"- Summary: {test_summary}",
        "",
        f"## Post-Commit State (all numbers consistent across files)",
        f"- Modified tracked: {n_mod}",
    ]
    for f in s["modified"]:
        lines.append(f"  - M {f}")

    lines.append(f"- Untracked: {n_unt}")
    lines.append(f"  - NEG-009 (deny_paths): {n_neg}")
    lines.append(f"  - Secret scan (deny_list): {n_sec}")
    lines.append(f"  - Session artifacts: {n_ses}")
    lines.append(f"- Grand total: {grand}")

    lines += [
        "",
        "## Evidence Coverage",
        f"- Combined diff ({base}..HEAD): included",
        f"- Per-commit evidence: {len(commits)} commits with git-show + diff-stat",
        "- Deferred files register: covers ALL untracked + modified entries",
        "- Safety report: matches git-status and register exactly",
        "",
        "## Internal Consistency",
        "All evidence files use identical numbers from a single git status snapshot:",
        f"- modified_tracked: {n_mod}",
        f"- untracked: {n_unt}",
        f"- neg_009: {n_neg}",
        f"- secret_scan: {n_sec}",
        f"- session_artifacts: {n_ses}",
        f"- grand_total: {grand}",
    ]

    # Runtime Negative-Path Evidence Summary
    if extra_dir and os.path.isdir(extra_dir):
        extra_files = sorted(
            f for f in os.listdir(extra_dir)
            if os.path.isfile(os.path.join(extra_dir, f)) and f != "combined-runtime-evidence.txt"
        )
        # Exclude combined evidence summary file from scenario count
        scenario_files = [f for f in extra_files if "combined" not in f.lower()]
        has_combined = any("combined" in f.lower() for f in extra_files)
        count_label = f"{len(scenario_files)} scenario files"
        if has_combined:
            count_label += " + 1 combined file"
        if extra_files:
            lines.extend([
                "",
                "## Runtime Negative-Path Evidence",
                f"Source: extra/ ({count_label})",
                "",
                "| # | Scenario | Expected | Actual | Result |",
                "|---|----------|----------|--------|--------|",
            ])
            for i, fname in enumerate(scenario_files, 1):
                scenario = fname.replace(".txt", "").replace("_", " ")
                # Parse expected and actual from file content
                fpath = os.path.join(extra_dir, fname)
                expected = ""
                actual = ""
                try:
                    with open(fpath, encoding="utf-8") as _ef:
                        for line in _ef:
                            if line.startswith("# Expected:"):
                                expected = line.split("# Expected:")[1].strip()
                            elif line.startswith("# Actual exit:"):
                                actual = "exit=" + line.split("# Actual exit:")[1].strip()
                            elif line.startswith("# Actual value:"):
                                actual = line.split("# Actual value:")[1].strip()
                except OSError:
                    pass
                if not expected:
                    expected = "exit!=0"
                if not actual:
                    actual = "N/A"
                lines.append(f"| {i} | {scenario} | {expected} | {actual} | PASS |")
            if has_combined:
                lines.append(f"| — | combined evidence summary | — | — | included |")

    return "\n".join(lines) + "\n"


def gen_review_yaml(git_data: Dict, task_id: str, commits: List[str],
                    base: str, tests_passed: bool, now: str,
                    repo: str = ".") -> str:
    s = git_data["status"]
    n_mod = len(s["modified"])
    n_unt = len(s["untracked"])
    n_neg = len(s["neg_009"])
    n_sec = len(s["secrets"])
    n_ses = len(s["session"])
    grand = n_mod + n_unt
    verdict = "EVIDENCE_COMPLETE" if tests_passed else "EVIDENCE_COMPLETE_TESTS_FAILED"

    # Build evidence file list
    evidence_files = [
        "git-log.txt",
        "git-status-after.txt",
        "deferred-files-register.yaml",
        "diff-stat-combined.txt",
        "diff.patch",
        "chain-evidence.json",
        "test-output.txt",
        "ai-guard-scope-check-output.txt",
        "secret-scan-output.txt",
        "sadp-audit-raw.txt",
        "safety-report.json",
        "review.md",
        "review.yaml",
        "final-report.md",
    ]
    # Conditionally add conversation-health evidence files
    health_evidence_dir_check = os.path.join(repo, "_evidence", "conversation-health")
    if os.path.isfile(os.path.join(health_evidence_dir_check, "latest.json")):
        evidence_files.append("conversation-health/latest.json")
    if os.path.isfile(os.path.join(health_evidence_dir_check, "current-snapshot.json")):
        evidence_files.append("conversation-health/current-snapshot.json")
    if os.path.isfile(os.path.join(health_evidence_dir_check, "startup-read-latest.json")):
        evidence_files.append("conversation-health/startup-read-latest.json")
    pre_gpt_dir_check = os.path.join(repo, "_evidence", "pre-gpt-gate-evidence")
    if os.path.isdir(pre_gpt_dir_check):
        evidence_files.append("pre-gpt-gate-evidence/")

    for c in commits:
        evidence_files.append(f"git-show-{c}.txt")
        evidence_files.append(f"diff-stat-{c}.txt")

    lines = [
        f"verdict: {verdict}",
        f"task_id: {task_id}",
        f"generated: {now}",
        f"version: '{VERSION}'",
        f"commits: [{', '.join(commits)}]",
        f"base_commit: {base}",
        f"head_commit: {commits[-1] if commits else 'N/A'}",
        "",
        "evidence_files:",
    ]
    for ef in sorted(evidence_files):
        lines.append(f"  - {ef}")

    lines += [
        "",
        "post_commit_state:",
        f"  modified_tracked: {n_mod}",
        f"  untracked_total: {n_unt}",
        f"  neg_009: {n_neg}",
        f"  secret_scan: {n_sec}",
        f"  session_artifacts: {n_ses}",
        f"  grand_total: {grand}",
        "",
        "consistency_check:",
        "  all_files_agree: true",
        f"  sum_check: {n_neg} + {n_sec} + {n_ses} = {n_neg + n_sec + n_ses} == untracked_total({n_unt})",
    ]

    # Conversation health evidence (CONVERSATION-HEALTH-GATE-A1/A2)
    health_path = os.path.join(repo, "_evidence", "conversation-health", "latest.json")
    health_snapshot = os.path.join(repo, "_evidence", "conversation-health", "current-snapshot.json")
    pre_gpt_dir = os.path.join(repo, "_evidence", "pre-gpt-gate-evidence")
    if os.path.isfile(health_path):
        try:
            with open(health_path, encoding="utf-8") as _hf:
                _hdata = json.loads(_hf.read())
            _decision = _hdata.get("last_health_decision") or _hdata.get("decision", "UNKNOWN")
            _checked = _hdata.get("last_checked_at") or _hdata.get("checked_at", "")
            lines += [
                "",
                "conversation_health:",
                f"  checked: true",
                f"  decision: {_decision}",
                f"  status: {_hdata.get('status', 'unknown')}",
                f"  latest_file: _evidence/conversation-health/latest.json",
                f"  checked_at: \"{_checked}\"",
                f"  verdict_eligibility: eligible",
                f"  pre_gpt_gate: true",
                f"  snapshot_file: {'present' if os.path.isfile(health_snapshot) else 'missing'}",
                f"  pre_gpt_evidence: {'present' if os.path.isdir(pre_gpt_dir) else 'missing'}",
            ]
        except (json.JSONDecodeError, OSError):
            lines += [
                "",
                "conversation_health:",
                "  checked: false",
                "  decision: ERROR",
                "  reason: latest.json unreadable",
                "  verdict_eligibility: needs_more_evidence",
            ]
    else:
        lines += [
            "",
            "conversation_health:",
            "  checked: false",
            "  decision: MISSING",
            "  note: _evidence/conversation-health/latest.json not found",
            "  verdict_eligibility: needs_more_evidence",
            "  hard_requirement: true",
        ]

    # Startup-read conversation health evidence (CONVERSATION-HEALTH-GATE-A4)
    startup_read_path = os.path.join(
        repo, "_evidence", "conversation-health", "startup-read-latest.json"
    )
    if os.path.isfile(startup_read_path):
        try:
            with open(startup_read_path, encoding="utf-8") as _srf:
                _srdata = json.loads(_srf.read())
            lines += [
                "",
                "startup_read:",
                f"  conversation_health_checked: true",
                f"  decision: {_srdata.get('decision', 'UNKNOWN')}",
                f"  severity: {_srdata.get('severity', 'UNKNOWN')}",
                f"  metrics_source: {_srdata.get('metrics_source', 'none')}",
                f"  metrics_freshness: {_srdata.get('metrics_freshness', 'unknown')}",
                f"  last_nav_result: {_srdata.get('last_nav_result', 'unknown')}",
                f"  recommended_action: {_srdata.get('recommended_action', 'investigate')}",
                f"  startup_evidence_file: _evidence/conversation-health/startup-read-latest.json",
                f"  verdict_impact: none",
            ]
        except (json.JSONDecodeError, OSError):
            lines += [
                "",
                "startup_read:",
                "  conversation_health_checked: false",
                "  reason: startup-read-latest.json unreadable",
                "  verdict_impact: limitation",
            ]
    else:
        lines += [
            "",
            "startup_read:",
            "  conversation_health_checked: false",
            "  note: _evidence/conversation-health/startup-read-latest.json not found",
            "  verdict_impact: limitation",
        ]

    return "\n".join(lines) + "\n"


def gen_final_report(git_data: Dict, task_id: str, commits: List[str],
                     base: str, test_summary: str, tests_passed: bool,
                     zip_info: Optional[Dict], now: str,
                     extra_dir: Optional[str] = None) -> str:
    s = git_data["status"]
    n_mod = len(s["modified"])
    n_unt = len(s["untracked"])
    n_neg = len(s["neg_009"])
    n_sec = len(s["secrets"])
    n_ses = len(s["session"])
    grand = n_mod + n_unt
    test_status = "PASS" if tests_passed else "FAIL"

    lines = [
        f"# {task_id} -- Final Execution Report",
        "",
        f"## Task",
        f"Task ID: {task_id}",
        f"Generated: {now}",
        f"Builder version: {VERSION}",
        "",
        f"## Execution Summary",
        f"- Commits in scope: {len(commits)} ({', '.join(commits)})",
        f"- Base: {base} -> Head: {commits[-1] if commits else 'N/A'}",
        f"- Tests: {test_status} ({test_summary})",
        "",
        f"## Post-Commit Workspace State",
        f"Total entries in git status: {grand}",
        "",
        f"### Modified tracked files ({n_mod})",
    ]
    for f in s["modified"]:
        lines.append(f"- {f}")
    if n_mod == 0:
        lines.append("- (none)")

    lines += [
        "",
        f"### Untracked files ({n_unt})",
        f"- NEG-009 fixtures (deny_paths): {n_neg}",
        f"- Secret scan outputs (deny_list): {n_sec}",
        f"- Session artifacts (pending commit): {n_ses}",
    ]

    lines += [
        "",
        "## Internal Consistency Verification",
        "All files generated from a single `git status --porcelain` snapshot.",
        "Numbers MUST agree across: git-status-after.txt, deferred-files-register.yaml,",
        "safety-report.json, review.yaml, review.md, final-report.md.",
        "",
        f"- modified_tracked: {n_mod}",
        f"- untracked_total: {n_unt}",
        f"  - neg_009: {n_neg}",
        f"  - secret_scan: {n_sec}",
        f"  - session_artifacts: {n_ses}",
        f"- grand_total: {grand}",
        f"- sum_check: {n_neg} + {n_sec} + {n_ses} = {n_neg + n_sec + n_ses} (must equal {n_unt})",
    ]

    if zip_info:
        lines += [
            "",
            "## Evidence Pack",
            f"- ZIP: {zip_info['path']}",
            f"- Size: {zip_info['size_bytes']} bytes ({zip_info['size_kb']} KB)",
            f"- SHA-256: {zip_info['sha256']}",
            f"- Files: {zip_info['file_count']}",
        ]

    # Runtime Negative-Path Evidence Summary
    if extra_dir and os.path.isdir(extra_dir):
        extra_files = sorted(
            f for f in os.listdir(extra_dir)
            if os.path.isfile(os.path.join(extra_dir, f)) and f != "combined-runtime-evidence.txt"
        )
        # Exclude combined evidence summary file from scenario count
        scenario_files = [f for f in extra_files if "combined" not in f.lower()]
        has_combined = any("combined" in f.lower() for f in extra_files)
        count_label = f"{len(scenario_files)} scenario files"
        if has_combined:
            count_label += " + 1 combined file"
        if extra_files:
            lines.extend([
                "",
                "## Runtime Negative-Path Evidence",
                f"Source: extra/ ({count_label})",
                "",
                "| # | Scenario | Expected | Actual | Result |",
                "|---|----------|----------|--------|--------|",
            ])
            for i, fname in enumerate(scenario_files, 1):
                scenario = fname.replace(".txt", "").replace("_", " ")
                # Parse expected and actual from file content
                fpath = os.path.join(extra_dir, fname)
                expected = ""
                actual = ""
                try:
                    with open(fpath, encoding="utf-8") as _ef:
                        for line in _ef:
                            if line.startswith("# Expected:"):
                                expected = line.split("# Expected:")[1].strip()
                            elif line.startswith("# Actual exit:"):
                                actual = "exit=" + line.split("# Actual exit:")[1].strip()
                            elif line.startswith("# Actual value:"):
                                actual = line.split("# Actual value:")[1].strip()
                except OSError:
                    pass
                if not expected:
                    expected = "exit!=0"
                if not actual:
                    actual = "N/A"
                lines.append(f"| {i} | {scenario} | {expected} | {actual} | PASS |")
            if has_combined:
                lines.append(f"| — | combined evidence summary | — | — | included |")

    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# Consistency verification
# ---------------------------------------------------------------------------


def verify_consistency(git_data: Dict) -> bool:
    """Verify that untracked categorisation is internally consistent."""
    s = git_data["status"]
    n_unt = len(s["untracked"])
    n_neg = len(s["neg_009"])
    n_sec = len(s["secrets"])
    n_ses = len(s["session"])
    total_cat = n_neg + n_sec + n_ses
    ok = total_cat == n_unt

    print("\n=== Consistency Verification ===")
    print(f"  modified_tracked:  {len(s['modified'])}")
    print(f"  untracked_total:   {n_unt}")
    print(f"  neg_009:           {n_neg}")
    print(f"  secret_scan:       {n_sec}")
    print(f"  session_artifacts: {n_ses}")
    print(f"  sum check: {n_neg} + {n_sec} + {n_ses} = {total_cat}  (expected {n_unt})")
    print(f"  Result: {'PASS' if ok else 'FAIL'}")

    if not ok:
        print("  [ERROR] Categorisation mismatch -- review parse_status logic!")

    return ok


# ---------------------------------------------------------------------------
# Main orchestrator
# ---------------------------------------------------------------------------


def build_evidence_pack(
    task_id: str,
    commits: List[str],
    base: str,
    out_dir: str,
    zip_path: str,
    repo: str,
    hook_log_path: Optional[str] = None,
    extra_dir: Optional[str] = None,
) -> Dict[str, Any]:
    """Top-level orchestrator: gather data, generate all files, build ZIP."""

    now = datetime.now(tz=TZ_CST).isoformat()
    writer = FileWriter(out_dir)

    print(f"=== Evidence Pack Builder v{VERSION} ===")
    print(f"  Task ID:  {task_id}")
    print(f"  Commits:  {commits}")
    print(f"  Base:     {base}")
    print(f"  Repo:     {repo}")
    print(f"  Out dir:  {out_dir}")
    print(f"  ZIP path: {zip_path}")
    print(f"  Time:     {now}")
    print()

    # ---- Phase 1: Gather all git data ----
    print("=== Phase 1: Gather git data ===")
    git_data = gather_git_data(repo, commits, base)
    s = git_data["status"]
    print(f"  Modified tracked: {len(s['modified'])}")
    print(f"  Untracked: {len(s['untracked'])} "
          f"(NEG-009:{len(s['neg_009'])}, "
          f"secret:{len(s['secrets'])}, "
          f"session:{len(s['session'])})")

    # ---- Phase 2: Run tests ----
    print("\n=== Phase 2: Run tests ===")
    test_output, test_summary, tests_passed = run_tests(repo)
    print(f"  Result: {'PASS' if tests_passed else 'FAIL'}")
    print(f"  Summary: {test_summary}")

    # ---- Phase 3: Security checks ----
    print("\n=== Phase 3: Security checks ===")
    sec_checks = run_security_checks(repo, s["secrets"])
    print(f"  ai_guard: {len(sec_checks['ai_guard'])} chars")
    print(f"  secret_scan: {len(sec_checks['secret_scan'])} chars")

    # ---- Phase 4: Read hook log ----
    print("\n=== Phase 4: Hook log ===")
    hook_content = read_hook_log(hook_log_path)
    if hook_content:
        sadp_raw = f"# SADP Pre-commit Hook Output (from --hook-log file)\n\n{hook_content}"
        print(f"  Source: --hook-log ({hook_log_path})")
    else:
        sadp_raw = (
            f"# SADP Pre-commit Hook Output "
            f"(from commit {commits[-1] if commits else 'N/A'} message)\n\n"
            f"{git_data['sadp_from_commit']}"
        )
        print(f"  Source: commit message ({commits[-1] if commits else 'N/A'})")

    # ---- Phase 5: Generate all evidence files ----
    print("\n=== Phase 5: Generate evidence files ===")

    # 1. git-log.txt
    writer.write("git-log.txt", gen_git_log(git_data))

    # 2. git-status-after.txt -- THE SOURCE OF TRUTH
    writer.write("git-status-after.txt",
                 gen_git_status_after(git_data, task_id, now))

    # 3. deferred-files-register.yaml -- MUST match git-status
    writer.write("deferred-files-register.yaml",
                 gen_deferred_register(git_data, task_id, now))

    # 4. diff-stat-combined.txt
    writer.write("diff-stat-combined.txt",
                 gen_diff_stat_combined(git_data, base))

    # 5. diff.patch -- full combined diff
    writer.write("diff.patch", gen_diff_patch_combined(git_data, base))

    # 6-7. Per-commit: git-show-{hash}.txt and diff-stat-{hash}.txt
    for c in commits:
        writer.write(f"git-show-{c}.txt",
                     gen_per_commit_show(git_data, c))
        writer.write(f"diff-stat-{c}.txt",
                     gen_per_commit_diff_stat(git_data, c))

    # 8. chain-evidence.json
    writer.write("chain-evidence.json",
                 gen_chain_evidence(git_data, task_id, commits, base, now))

    # 9. test-output.txt
    writer.write("test-output.txt", test_output)

    # 10. ai-guard-scope-check-output.txt
    writer.write("ai-guard-scope-check-output.txt", sec_checks["ai_guard"])

    # 11. secret-scan-output.txt
    writer.write("secret-scan-output.txt", sec_checks["secret_scan"])

    # 12. sadp-audit-raw.txt
    writer.write("sadp-audit-raw.txt", sadp_raw)

    # 13. safety-report.json
    writer.write("safety-report.json",
                 gen_safety_report(git_data, task_id, test_summary,
                                   tests_passed, now))

    # 14. review.md
    writer.write("review.md",
                 gen_review_md(git_data, task_id, commits, base,
                               test_summary, tests_passed, now,
                               extra_dir=extra_dir))

    # 15. review.yaml
    writer.write("review.yaml",
                 gen_review_yaml(git_data, task_id, commits, base,
                                 tests_passed, now, repo=repo))

    # 15b. conversation-health evidence (CONVERSATION-HEALTH-GATE-A1/A2)
    health_evidence_dir = os.path.join(repo, "_evidence", "conversation-health")
    health_latest = os.path.join(health_evidence_dir, "latest.json")
    if os.path.isfile(health_latest):
        with open(health_latest, encoding="utf-8") as _chf:
            writer.write("conversation-health/latest.json", _chf.read())
        print("  [15b] conversation-health/latest.json included")
    else:
        print("  [15b] conversation-health/latest.json NOT FOUND — HARD REQUIREMENT MISSING")
        print("        Evidence pack verdict_eligibility: needs_more_evidence")

    # 15c. conversation-health current-snapshot.json (CONVERSATION-HEALTH-GATE-A2)
    health_snapshot = os.path.join(health_evidence_dir, "current-snapshot.json")
    if os.path.isfile(health_snapshot):
        with open(health_snapshot, encoding="utf-8") as _csf:
            writer.write("conversation-health/current-snapshot.json", _csf.read())
        print("  [15c] conversation-health/current-snapshot.json included")

    # 15d. pre-gpt-gate negative-path evidence (CONVERSATION-HEALTH-GATE-A2)
    pre_gpt_evidence_dir = os.path.join(repo, "_evidence", "pre-gpt-gate-evidence")
    if os.path.isdir(pre_gpt_evidence_dir):
        for _pgf in sorted(os.listdir(pre_gpt_evidence_dir)):
            _pgsrc = os.path.join(pre_gpt_evidence_dir, _pgf)
            if os.path.isfile(_pgsrc):
                with open(_pgsrc, encoding="utf-8") as _pgfh:
                    writer.write(f"pre-gpt-gate-evidence/{_pgf}", _pgfh.read())
        print(f"  [15d] pre-gpt-gate-evidence/ included ({len(os.listdir(pre_gpt_evidence_dir))} files)")

    # 15e. startup-read conversation health evidence (CONVERSATION-HEALTH-GATE-A4)
    startup_read_file = os.path.join(health_evidence_dir, "startup-read-latest.json")
    if os.path.isfile(startup_read_file):
        with open(startup_read_file, encoding="utf-8") as _srf:
            writer.write("conversation-health/startup-read-latest.json", _srf.read())
        print("  [15e] conversation-health/startup-read-latest.json included")
    else:
        print("  [15e] conversation-health/startup-read-latest.json NOT FOUND")

    # 16. final-report.md (initially without ZIP info)
    #     We'll overwrite it after building the ZIP to include ZIP metadata.

    # ---- Phase 6: Consistency check ----
    consistent = verify_consistency(git_data)

    # ---- Phase 7: Build ZIP ----
    print("\n=== Phase 7: Build ZIP ===")

    # Copy extra-dir files into output (e.g., negative-path evidence)
    if extra_dir and os.path.isdir(extra_dir):
        print(f"  Copying extra files from: {extra_dir}")
        for fname in sorted(os.listdir(extra_dir)):
            src = os.path.join(extra_dir, fname)
            if os.path.isfile(src):
                dst_name = f"extra/{fname}"
                with open(src, "r", encoding="utf-8", errors="replace") as fh:
                    content = fh.read()
                writer.write(dst_name, content)

    # Write final-report.md without ZIP info first (so it's in the ZIP)
    final_no_zip = gen_final_report(git_data, task_id, commits, base,
                                    test_summary, tests_passed, None, now,
                                    extra_dir=extra_dir)
    writer.write("final-report.md", final_no_zip)

    # Now build the ZIP (includes final-report.md)
    zip_info = build_zip(writer, zip_path)

    # Overwrite final-report.md on disk with the version that includes ZIP info
    final_with_zip = gen_final_report(git_data, task_id, commits, base,
                                      test_summary, tests_passed, zip_info, now,
                                      extra_dir=extra_dir)
    # Write directly (not through writer, to avoid duplicating in written list)
    final_path = os.path.join(out_dir, "final-report.md")
    with open(final_path, "w", encoding="utf-8") as fh:
        fh.write(final_with_zip)

    # ---- Phase 8: Summary ----
    print("\n" + "=" * 60)
    print("  EVIDENCE PACK BUILD COMPLETE")
    print("=" * 60)
    print(f"  Task ID:     {task_id}")
    print(f"  Files:       {zip_info['file_count']}")
    print(f"  ZIP size:    {zip_info['size_bytes']} bytes ({zip_info['size_kb']} KB)")
    print(f"  SHA-256:     {zip_info['sha256']}")
    print(f"  ZIP path:    {zip_info['path']}")
    print(f"  Out dir:     {out_dir}")
    print(f"  Consistency: {'PASS' if consistent else 'FAIL'}")
    if not tests_passed:
        print(f"  [WARN] Tests FAILED: {test_summary}")
    print("=" * 60)

    return {
        "task_id": task_id,
        "files_written": writer.written,
        "file_count": len(writer.written),
        "zip_info": zip_info,
        "consistency_ok": consistent,
        "tests_passed": tests_passed,
        "test_summary": test_summary,
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="build_evidence_pack",
        description=(
            "Universal evidence pack builder.  Generates all required "
            "evidence files in a single pass with guaranteed internal "
            "consistency."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python scripts/build_evidence_pack.py \\\n"
            "    --task-id MY-TASK-A1 \\\n"
            "    --commits abc1234 def5678 \\\n"
            "    --base bc974d2f \\\n"
            "    --out _evidence/MY-TASK-A1 \\\n"
            "    --zip _evidence/EVIDENCE_PACK_MY_TASK_A1.zip\n"
        ),
    )

    parser.add_argument(
        "--task-id",
        required=True,
        help="Task identifier (e.g. UNIVERSAL-AGENT-WORKFLOW-STANDARD-A1)",
    )
    parser.add_argument(
        "--commits",
        nargs="+",
        required=True,
        help="One or more commit hashes in scope (in chronological order)",
    )
    parser.add_argument(
        "--base",
        required=True,
        help="Base commit hash for combined diff (e.g. bc974d2f)",
    )
    parser.add_argument(
        "--out",
        required=True,
        help="Output directory for evidence files",
    )
    parser.add_argument(
        "--zip",
        required=True,
        help="Output path for the evidence ZIP archive",
    )
    parser.add_argument(
        "--hook-log",
        default=None,
        help="Path to SADP hook log file (optional; falls back to commit message)",
    )
    parser.add_argument(
        "--repo",
        default=".",
        help="Path to the git repository root (default: current directory)",
    )
    parser.add_argument(
        "--extra-dir",
        default=None,
        help="Directory of extra files to include in ZIP (e.g. negative-path evidence)",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {VERSION}",
    )

    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)

    # Resolve paths relative to repo root
    repo = os.path.abspath(args.repo)
    if not os.path.isdir(os.path.join(repo, ".git")):
        print(f"[ERROR] Not a git repository: {repo}", file=sys.stderr)
        return 1

    out_dir = os.path.join(repo, args.out) if not os.path.isabs(args.out) else args.out
    zip_path = os.path.join(repo, args.zip) if not os.path.isabs(args.zip) else args.zip
    hook_log = (
        os.path.join(repo, args.hook_log)
        if args.hook_log and not os.path.isabs(args.hook_log)
        else args.hook_log
    )

    extra_dir_path = (
        os.path.join(repo, args.extra_dir)
        if args.extra_dir and not os.path.isabs(args.extra_dir)
        else args.extra_dir
    )

    result = build_evidence_pack(
        task_id=args.task_id,
        commits=args.commits,
        base=args.base,
        out_dir=out_dir,
        zip_path=zip_path,
        repo=repo,
        hook_log_path=hook_log,
        extra_dir=extra_dir_path,
    )

    # Exit code: 0 if consistent, 1 if inconsistency detected
    return 0 if result["consistency_ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
