#!/usr/bin/env python3
"""generate_reconciliation_report.py — GPT Capture Reconciliation Report Generator.

Scans all GPT review records in the agent-acceptance project and produces
an end-to-end audit reconciliation report per HANDOFF_WORKFLOW_HARDENING_PLAN.md §5.4.

Reconciliation chain:
  Submission → Capture → Verification → Verdict

Anomaly types (from spec §5.4):
  - orphan_submission:    submission exists but no capture
  - orphan_capture:       capture exists but no submission
  - unverified_capture:   capture exists but not verified
  - verdict_mismatch:     verifier verdict ≠ GPT raw reply
  - stale_submission:     submission timeout
  - pre_standardization:  pre-standard format, cannot fully verify
  - truncated_capture:     captured reply is incomplete

Usage:
    python scripts/generate_reconciliation_report.py \
        --reports-dir "D:/agent-acceptance/_reports" \
        --evidence-dir "D:/agent-acceptance/evidence_packs" \
        --output-json "_reports/gpt-capture-reconciliation-harden-a1/GPT_CAPTURE_RECONCILIATION_REPORT.json" \
        --output-md "_reports/gpt-capture-reconciliation-harden-a1/GPT_CAPTURE_RECONCILIATION_REPORT.md"
"""

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

# ── Constants ──────────────────────────────────────────────────────

VALID_VERDICTS = {
    "accepted", "accepted_with_limitation", "blocked",
    "human_required", "review_unverified", "mixed_blocked", "mixed"
}

VALID_STATUSES = {
    "complete", "orphan_submission", "orphan_capture",
    "unverified_capture", "verdict_mismatch", "pre_standardization",
    "truncated_capture", "blocked_chain_continuation"
}

VALID_ANOMALY_SEVERITIES = {"critical", "high", "medium", "low", "info"}

TZ_CST = timezone(timedelta(hours=8))


# ── Helpers ────────────────────────────────────────────────────────

def sha256_file(path: Path) -> str | None:
    """Compute SHA-256 of a file, return first 32 hex chars or None."""
    if not path or not path.exists():
        return None
    try:
        h = hashlib.sha256(path.read_bytes()).hexdigest()
        return h[:32] + "..."
    except Exception:
        return None


def file_mtime_iso(path: Path) -> str | None:
    """Get file modification time as ISO 8601 string."""
    if not path or not path.exists():
        return None
    try:
        ts = path.stat().st_mtime
        return datetime.fromtimestamp(ts, tz=TZ_CST).isoformat()
    except Exception:
        return None


def safe_read_json(path: Path) -> dict | None:
    """Read and parse a JSON file, return None on failure."""
    if not path or not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def extract_verdict_from_text(text: str) -> str | None:
    """Extract overall_judgment from raw GPT reply text."""
    m = re.search(r"overall_judgment:\s*(\S+)", text, re.IGNORECASE)
    if m:
        v = m.group(1).strip().lower()
        return v if v in VALID_VERDICTS else v
    return None


def has_end_marker(text: str) -> bool:
    """Check if text contains END_OF_GPT_RESPONSE marker."""
    return "END_OF_GPT_RESPONSE" in text


def has_next_task_auth(text: str) -> bool:
    """Check if text contains next_task_authorization section."""
    return "next_task_authorization" in text.lower()


def extract_next_task_id_from_text(text: str) -> str | None:
    """Extract next_task_authorization task_id from raw text."""
    m = re.search(r"next_task_authorization:.*?task_id:\s*(\S+)", text, re.IGNORECASE | re.DOTALL)
    if m:
        return m.group(1).strip()
    return None


# ── Record Scanner ─────────────────────────────────────────────────

class ReconciliationScanner:
    """Scans project directories and builds reconciliation data."""

    def __init__(self, reports_dir: Path, evidence_dir: Path):
        self.reports_dir = reports_dir
        self.evidence_dir = evidence_dir
        self.tasks: dict[str, dict] = {}  # task_id -> task data

    def scan(self):
        """Run full scan pipeline."""
        self._scan_record_files()
        self._scan_result_files()
        self._scan_run_ids()
        self._scan_capture_reconciliations()
        self._scan_evidence_packs()
        self._scan_verify_outputs()

    def _ensure_task(self, task_id: str) -> dict:
        """Get or create task entry."""
        if task_id not in self.tasks:
            self.tasks[task_id] = {
                "task_id": task_id,
                "report_dir": None,
                "evidence_pack_dir": None,
                "rounds": {},
            }
        return self.tasks[task_id]

    def _ensure_round(self, task: dict, round_id: str) -> dict:
        """Get or create round entry within a task."""
        if round_id not in task["rounds"]:
            task["rounds"][round_id] = {
                "round": round_id,
                "record_file": None,
                "result_file": None,
                "result_size_bytes": None,
                "run_id": None,
                "run_id_source": None,
                "verdict": None,
                "has_end_marker": False,
                "has_next_task_auth": False,
                "next_task_authorized_id": None,
                "verify_passed": None,
                "verify_output_file": None,
                "capture_reconciliation_file": None,
                "capture_mismatch": None,
                "submitted_at": None,
                "captured_at": None,
                "verified_at": None,
                "status": None,
                "anomalies": [],
                "closure_ready": None,
            }
        return task["rounds"][round_id]

    def _task_id_from_dirname(self, dirname: str) -> str:
        """Convert directory name to canonical task_id (UPPER-KEBAB)."""
        return dirname.upper().replace("_", "-")

    def _infer_round_id(self, filename: str) -> str:
        """Infer round ID from filename patterns.
        
        Handles:
        - GPT_REVIEW_RESULT_R1.txt → R1
        - GPT_REVIEW_RESULT_R2.txt → R2
        - GPT_REVIEW_RESULT_NEWCHAT_INITIAL.txt → NEWCHAT_INITIAL
        - GPT_REVIEW_RESULT_NEWCHAT_VERIFIED.txt → NEWCHAT_VERIFIED
        - GPT_REVIEW_RESULT_NEWCHAT.txt → NEWCHAT
        - GPT_REVIEW_RESULT_ATTACHCHAT.txt → ATTACHCHAT
        - GPT_REVIEW_RESULT.txt → R1
        - GPT_REVIEW_RECORD.json → R1
        - GPT_REVIEW_RECORD_R2.json → R2
        """
        # Standard round pattern: _R1, _R2, etc.
        m = re.search(r"_(R\d+)", filename, re.IGNORECASE)
        if m:
            return m.group(1).upper()
        # Special named rounds (for HANDOFF-PIPELINE-REFACTOR-A1)
        for special in ("NEWCHAT_INITIAL", "NEWCHAT_VERIFIED", "NEWCHAT", "ATTACHCHAT"):
            if special.lower() in filename.lower():
                return special
        return "R1"

    # ── Scan RECORD JSON files ──
    def _scan_record_files(self):
        """Scan GPT_REVIEW_RECORD*.json files."""
        for record_path in sorted(self.reports_dir.glob("*/GPT_REVIEW_RECORD*.json")):
            data = safe_read_json(record_path)
            if not data:
                continue

            task_id = data.get("task_id", self._task_id_from_dirname(record_path.parent.name))
            task = self._ensure_task(task_id)
            task["report_dir"] = str(record_path.parent.relative_to(self.reports_dir.parent))

            round_id = data.get("round", self._infer_round_id(record_path.name))
            # Normalize round_id
            if isinstance(round_id, str) and round_id.startswith("R1 ") and "R2" in round_id:
                round_id = "R2"  # Follow-up captured as R2

            rnd = self._ensure_round(task, round_id)
            rnd["record_file"] = str(record_path.name)

            # Extract verdict info
            verdict = data.get("verdict", {})
            if isinstance(verdict, dict):
                rnd["verdict"] = verdict.get("overall_judgment")
                rnd["has_end_marker"] = verdict.get("has_end_marker", False)
                rnd["has_next_task_auth"] = verdict.get("has_next_task_auth", False)
            else:
                # Legacy RECORD format (flat)
                rnd["verdict"] = data.get("parsed_overall_judgment")
                rnd["has_end_marker"] = data.get("has_end_marker", False)
                rnd["has_next_task_auth"] = data.get("has_next_task_auth", False)

            # Run ID
            rnd["run_id"] = data.get("run_id")

            # Submission info
            submission = data.get("submission", {})
            if isinstance(submission, dict):
                rnd["submitted_at"] = submission.get("sent_at")
                rnd["captured_at"] = submission.get("sent_at")  # Approximate

            # Capture reconciliation
            cap_recon = data.get("capture_reconciliation", {})
            if isinstance(cap_recon, dict):
                rnd["capture_mismatch"] = cap_recon.get("capture_mismatch")

            # Verifier
            verifier = data.get("verifier", {})
            if isinstance(verifier, dict):
                rnd["verify_passed"] = verifier.get("valid")
                rnd["closure_ready"] = verifier.get("closure_ready")

            # Next task authorization
            next_auth = data.get("next_task_authorization", {})
            if isinstance(next_auth, dict):
                rnd["next_task_authorized_id"] = next_auth.get("task_id")

            # Captured reply
            captured = data.get("captured_reply", {})
            if isinstance(captured, dict):
                result_path = captured.get("result_path")
                if result_path:
                    rnd["result_file"] = Path(result_path).name

            # Timestamps
            rnd["captured_at"] = data.get("created_at", rnd.get("captured_at"))

    # ── Scan RESULT text files ──
    def _scan_result_files(self):
        """Scan GPT_REVIEW_RESULT*.txt and .md files."""
        for result_path in sorted(self.reports_dir.glob("*/GPT_REVIEW_RESULT*")):
            if result_path.suffix not in (".txt", ".md"):
                continue

            dirname = result_path.parent.name
            # Try to find task_id from RECORD or infer from dirname
            task_id = self._find_task_id_for_dir(dirname)
            if not task_id:
                task_id = self._task_id_from_dirname(dirname)

            task = self._ensure_task(task_id)
            if not task["report_dir"]:
                task["report_dir"] = str(result_path.parent.relative_to(self.reports_dir.parent))

            round_id = self._infer_round_id(result_path.stem)
            rnd = self._ensure_round(task, round_id)

            # Only fill if not already populated by RECORD
            if not rnd["result_file"]:
                rnd["result_file"] = result_path.name

            rnd["result_size_bytes"] = result_path.stat().st_size

            # Parse text content
            try:
                text = result_path.read_text(encoding="utf-8")
            except Exception:
                text = ""

            if not rnd["verdict"]:
                rnd["verdict"] = extract_verdict_from_text(text)
            if not rnd["has_end_marker"]:
                rnd["has_end_marker"] = has_end_marker(text)
            if not rnd["has_next_task_auth"]:
                rnd["has_next_task_auth"] = has_next_task_auth(text)
            if not rnd["next_task_authorized_id"]:
                rnd["next_task_authorized_id"] = extract_next_task_id_from_text(text)

            if not rnd["captured_at"]:
                rnd["captured_at"] = file_mtime_iso(result_path)

    def _find_task_id_for_dir(self, dirname: str) -> str | None:
        """Find the canonical task_id for a report directory.
        
        Uses exact match on directory name to avoid substring false positives
        (e.g., 'global-project-evidence-binding-a1' must NOT match
        'GLOBAL-PROJECT-EVIDENCE-BINDING-A1-R4').
        """
        dirname_lower = dirname.lower()
        # 1. Exact match: task's report_dir basename == dirname
        for tid, tdata in self.tasks.items():
            rdir = tdata.get("report_dir")
            if rdir:
                rdir_basename = Path(rdir).name.lower()
                if rdir_basename == dirname_lower:
                    return tid
        # 2. Direct check: any RECORD in this exact dir has a task_id
        for record_path in self.reports_dir.glob(f"{dirname}/GPT_REVIEW_RECORD*.json"):
            data = safe_read_json(record_path)
            if data and "task_id" in data:
                return data["task_id"]
        return None

    # ── Scan RUN_ID files ──
    def _scan_run_ids(self):
        """Scan *_RUN_ID*.txt and GPT_REVIEW_RUN_ID.txt files."""
        # Collect all RUN_ID files from report subdirectories
        run_id_files = []
        for d in sorted(self.reports_dir.iterdir()):
            if d.is_dir():
                run_id_files.extend(d.glob("*RUN_ID*.txt"))
        for run_id_path in sorted(run_id_files):
            dirname = run_id_path.parent.name
            task_id = self._find_task_id_for_dir(dirname)
            if not task_id:
                task_id = self._task_id_from_dirname(dirname)

            task = self._ensure_task(task_id)
            round_id = self._infer_round_id(run_id_path.stem)
            rnd = self._ensure_round(task, round_id)

            if not rnd["run_id"]:
                try:
                    rnd["run_id"] = run_id_path.read_text(encoding="utf-8").strip()
                    rnd["run_id_source"] = run_id_path.name
                except Exception:
                    pass

    # ── Scan Capture Reconciliation JSON files ──
    def _scan_capture_reconciliations(self):
        """Scan GPT_CAPTURE_RECONCILIATION*.json files."""
        for cap_path in sorted(self.reports_dir.glob("*/GPT_CAPTURE_RECONCILIATION*.json")):
            data = safe_read_json(cap_path)
            if not data:
                continue

            dirname = cap_path.parent.name
            task_id = self._find_task_id_for_dir(dirname)
            if not task_id:
                task_id = self._task_id_from_dirname(dirname)

            task = self._ensure_task(task_id)
            round_id = self._infer_round_id(cap_path.stem)
            rnd = self._ensure_round(task, round_id)

            rnd["capture_reconciliation_file"] = cap_path.name
            if "capture_mismatch" in data:
                rnd["capture_mismatch"] = data["capture_mismatch"]
            if not rnd["run_id"] and "target_run_id" in data:
                rnd["run_id"] = data["target_run_id"]

    # ── Scan Evidence Packs ──
    def _scan_evidence_packs(self):
        """Scan evidence_packs directories."""
        if not self.evidence_dir.exists():
            return
        for pack_dir in sorted(self.evidence_dir.iterdir()):
            if not pack_dir.is_dir():
                continue
            # Match to task by directory name similarity
            pack_name = pack_dir.name.lower()
            matched = False
            for tid in self.tasks:
                tid_lower = tid.lower().replace("_", "-")
                if tid_lower == pack_name or tid_lower in pack_name:
                    self.tasks[tid]["evidence_pack_dir"] = str(
                        pack_dir.relative_to(self.evidence_dir.parent)
                    )
                    matched = True
                    break
            # If not matched, store as potential match
            if not matched:
                # Store for later reference
                pass

    # ── Scan Verify Output files ──
    def _scan_verify_outputs(self):
        """Scan VERIFY_GPT_REPLY_OUTPUT*.txt files."""
        for verify_path in sorted(self.reports_dir.glob("*/VERIFY_GPT_REPLY_OUTPUT*.txt")):
            dirname = verify_path.parent.name
            task_id = self._find_task_id_for_dir(dirname)
            if not task_id:
                task_id = self._task_id_from_dirname(dirname)

            task = self._ensure_task(task_id)
            round_id = self._infer_round_id(verify_path.stem)
            rnd = self._ensure_round(task, round_id)

            if rnd["verify_passed"] is None:
                try:
                    text = verify_path.read_text(encoding="utf-8")
                    if "GUARD OK" in text:
                        rnd["verify_passed"] = True
                    elif "GUARD BLOCKED" in text:
                        rnd["verify_passed"] = False
                except Exception:
                    pass
            rnd["verify_output_file"] = verify_path.name
            if not rnd["verified_at"]:
                rnd["verified_at"] = file_mtime_iso(verify_path)


# ── Report Builder ─────────────────────────────────────────────────

class ReconciliationReportBuilder:
    """Builds the reconciliation report from scanned data."""

    def __init__(self, scanner: ReconciliationScanner):
        self.scanner = scanner

    def build(self) -> dict:
        """Build complete reconciliation report."""
        now = datetime.now(tz=TZ_CST)
        report_id = f"RECON-{now.strftime('%Y%m%d')}-001"

        reconciliation = []
        all_anomalies = []

        # Counters
        total_submissions = 0
        total_captures = 0
        total_verified = 0
        total_verdicts = 0
        orphan_submissions = 0
        orphan_captures = 0
        unverified_captures = 0

        # Process each task sorted by first captured_at
        # Exclude the current task (GPT-CAPTURE-RECONCILIATION-HARDEN-A1)
        # as it has no review record yet
        CURRENT_TASK_ID = "GPT-CAPTURE-RECONCILIATION-HARDEN-A1"
        sorted_tasks = sorted(
            [t for t in self.scanner.tasks.values()
             if t["task_id"].upper() != CURRENT_TASK_ID.upper()],
            key=lambda t: self._earliest_timestamp(t)
        )

        for seq, task in enumerate(sorted_tasks, 1):
            for round_id in sorted(task["rounds"].keys()):
                rnd = task["rounds"][round_id]
                entry = self._build_entry(seq, task, round_id, rnd)
                reconciliation.append(entry)

                # Update counters
                status = entry["status"]
                total_submissions += 1  # Each round is a submission attempt

                if rnd.get("result_file"):
                    total_captures += 1
                else:
                    orphan_submissions += 1

                if rnd.get("verify_passed") is not None:
                    total_verified += 1
                elif rnd.get("result_file") and status not in ("pre_standardization",):
                    unverified_captures += 1

                if rnd.get("verdict") and rnd["verdict"] in VALID_VERDICTS:
                    total_verdicts += 1

                # Collect anomalies
                for anomaly in entry.get("anomalies", []):
                    all_anomalies.append({
                        "task_id": task["task_id"],
                        "round": round_id,
                        "type": anomaly.get("type", "unknown"),
                        "severity": anomaly.get("severity", "info"),
                        "description": anomaly.get("description", ""),
                    })

        summary = {
            "total_submissions": total_submissions,
            "total_captures": total_captures,
            "total_verified": total_verified,
            "total_verdicts": total_verdicts,
            "orphan_submissions": orphan_submissions,
            "orphan_captures": orphan_captures,
            "unverified_captures": unverified_captures,
        }

        # Build authorization chain
        auth_chain = self._build_authorization_chain()

        report = {
            "report_id": report_id,
            "task_id": "GPT-CAPTURE-RECONCILIATION-HARDEN-A1",
            "generated_at": now.isoformat(),
            "generator": "scripts/generate_reconciliation_report.py",
            "hardening_plan_ref": "HANDOFF_WORKFLOW_HARDENING_PLAN.md section 5.4",
            "summary": summary,
            "reconciliation": reconciliation,
            "authorization_chain": auth_chain,
            "anomalies": all_anomalies,
        }

        return report

    def _earliest_timestamp(self, task: dict) -> str:
        """Get earliest timestamp from a task's rounds."""
        timestamps = []
        for rnd in task["rounds"].values():
            for key in ("submitted_at", "captured_at", "verified_at"):
                ts = rnd.get(key)
                if ts:
                    timestamps.append(ts)
        return min(timestamps) if timestamps else "9999"

    def _build_entry(self, seq: int, task: dict, round_id: str, rnd: dict) -> dict:
        """Build a single reconciliation entry."""
        anomalies = []

        # Determine status
        status = self._determine_status(task, rnd, anomalies)

        entry = {
            "seq": seq,
            "task_id": task["task_id"],
            "round": round_id,
            "report_dir": task.get("report_dir"),
            "evidence_pack_dir": task.get("evidence_pack_dir"),
            "submitted_at": rnd.get("submitted_at"),
            "captured_at": rnd.get("captured_at"),
            "verified_at": rnd.get("verified_at"),
            "verdict": rnd.get("verdict"),
            "run_id": rnd.get("run_id"),
            "has_end_marker": rnd.get("has_end_marker", False),
            "has_next_task_auth": rnd.get("has_next_task_auth", False),
            "next_task_authorized_id": rnd.get("next_task_authorized_id"),
            "verify_passed": rnd.get("verify_passed"),
            "closure_ready": rnd.get("closure_ready"),
            "capture_mismatch": rnd.get("capture_mismatch"),
            "result_file": rnd.get("result_file"),
            "result_size_bytes": rnd.get("result_size_bytes"),
            "record_file": rnd.get("record_file"),
            "status": status,
            "anomalies": anomalies,
        }

        return entry

    def _determine_status(self, task: dict, rnd: dict, anomalies: list) -> str:
        """Determine reconciliation status for a round."""
        has_result = bool(rnd.get("result_file"))
        has_record = bool(rnd.get("record_file"))
        has_verdict = bool(rnd.get("verdict"))
        verify_passed = rnd.get("verify_passed")
        has_end = rnd.get("has_end_marker", False)
        verdict = rnd.get("verdict")
        result_size = rnd.get("result_size_bytes")
        task_id_upper = task["task_id"].upper()

        # ── Era classification ──
        # Pre-standardization: AA-* tasks (markdown format, no structured protocol)
        is_aa_pre_standard = task_id_upper.startswith("AA-")

        # Pre-RECORD era: HANDOFF-PIPELINE-REFACTOR-A1 (multiple sub-rounds,
        # no RECORD, iterative captures, pre-standardization of RECORD format)
        is_pipeline_refactor = "HANDOFF-PIPELINE-REFACTOR" in task_id_upper

        # Pre-standardization era: no RECORD file AND no RUN_ID
        is_no_record_era = not has_record and not rnd.get("run_id")

        # ── Truncated capture check (highest priority for post-standard tasks) ──
        if has_result and not has_end and not is_aa_pre_standard and not is_pipeline_refactor:
            if has_verdict and verdict in VALID_VERDICTS:
                anomalies.append({
                    "type": "truncated_capture",
                    "severity": "high",
                    "description": (
                        f"Result captured at intermediate state: has verdict '{verdict}' "
                        f"but missing END_OF_GPT_RESPONSE marker (size={result_size}B). "
                        f"Likely requires follow-up message to complete."
                    ),
                })
                return "truncated_capture"

        # ── Pre-standardization: AA-* tasks ──
        if is_aa_pre_standard:
            anomalies.append({
                "type": "pre_standardization",
                "severity": "low",
                "description": (
                    "Pre-standardization format (.md): no RECORD, no RUN_ID, "
                    "no structured END_OF_GPT_RESPONSE. "
                    "Cannot be fully verified by current verify_gpt_reply.py."
                ),
            })
            return "pre_standardization"

        # ── Pre-RECORD era: HANDOFF-PIPELINE-REFACTOR-A1 ──
        if is_pipeline_refactor:
            anomalies.append({
                "type": "pre_standardization",
                "severity": "medium",
                "description": (
                    "Pre-RECORD era: no GPT_REVIEW_RECORD.json. Multiple iterative "
                    "sub-rounds (R1-R4, NEWCHAT_INITIAL, NEWCHAT_VERIFIED, ATTACHCHAT). "
                    "Formal verify_gpt_reply.py was not standardized yet."
                ),
            })
            return "pre_standardization"

        # ── No RECORD and no RUN_ID (generic pre-standard) ──
        if is_no_record_era and not has_record:
            anomalies.append({
                "type": "pre_standardization",
                "severity": "medium",
                "description": (
                    "No RECORD and no RUN_ID: pre-standardization of structured "
                    "verification protocol. Cannot fully verify."
                ),
            })
            return "pre_standardization"

        # ── Orphan submission (no capture) ──
        if not has_result:
            anomalies.append({
                "type": "orphan_submission",
                "severity": "high",
                "description": "Submission record exists but no captured GPT response.",
            })
            return "orphan_submission"

        # ── Unverified capture (has capture but verify not run) ──
        if verify_passed is None and has_result:
            anomalies.append({
                "type": "unverified_capture",
                "severity": "high",
                "description": (
                    "Capture exists but verify_gpt_reply.py was not run "
                    "(no VERIFY_GPT_REPLY_OUTPUT file found)."
                ),
            })
            return "unverified_capture"

        # ── Verdict mismatch (verifier failed but GPT said accepted) ──
        if verify_passed is False and verdict in ("accepted", "accepted_with_limitation"):
            anomalies.append({
                "type": "verdict_mismatch",
                "severity": "medium",
                "description": f"Verifier failed (exit≠0) but GPT verdict was {verdict}.",
            })
            return "verdict_mismatch"

        # ── Blocked verdict (part of chain, not anomaly) ──
        if verdict == "blocked":
            return "blocked_chain_continuation"

        # ── review_unverified (GPT couldn't give definitive verdict) ──
        if verdict == "review_unverified":
            anomalies.append({
                "type": "verdict_mismatch",
                "severity": "medium",
                "description": "GPT returned review_unverified — not a definitive verdict.",
            })
            return "verdict_mismatch"

        # ── Capture mismatch warning ──
        if rnd.get("capture_mismatch") is True:
            anomalies.append({
                "type": "orphan_capture",
                "severity": "medium",
                "description": (
                    "Capture reconciliation detected mismatch between "
                    "selected and last assistant message."
                ),
            })

        # ── Accepted without next_task_authorization ──
        if verdict in ("accepted", "accepted_with_limitation") and not rnd.get("has_next_task_auth"):
            anomalies.append({
                "type": "verdict_mismatch",
                "severity": "medium",
                "description": f"Verdict is {verdict} but missing next_task_authorization.",
            })

        return "complete"

    def _build_authorization_chain(self) -> list:
        """Build the next_task_authorization chain."""
        chains = []

        # Build normalized lookup of all known task_ids
        known_task_ids = set()
        for t in self.scanner.tasks.values():
            known_task_ids.add(t["task_id"].upper())
            known_task_ids.add(t["task_id"].upper().replace("-", "_"))
            known_task_ids.add(t["task_id"].upper().replace("_", "-"))

        for task in sorted(self.scanner.tasks.values(), key=lambda t: self._earliest_timestamp(t)):
            for round_id in sorted(task["rounds"].keys()):
                rnd = task["rounds"][round_id]
                next_id = rnd.get("next_task_authorized_id")
                if next_id and next_id.lower() not in ("none", ""):
                    # Check existence with flexible matching
                    next_id_normalized = next_id.upper()
                    exists = (
                        next_id_normalized in known_task_ids
                        or next_id_normalized.replace("_", "-") in known_task_ids
                        or next_id_normalized.replace("-", "_") in known_task_ids
                    )
                    # Special case: current task (being executed now)
                    if next_id_normalized.replace("-", "_") == "GPT_CAPTURE_RECONCILIATION_HARDEN_A1":
                        exists = False  # This is the current task, not yet reviewed

                    chain_entry = {
                        "source_task_id": task["task_id"],
                        "source_round": round_id,
                        "source_verdict": rnd.get("verdict"),
                        "authorized_task_id": next_id,
                        "authorized_exists": exists,
                    }
                    chains.append(chain_entry)

        return chains


# ── Markdown Renderer ──────────────────────────────────────────────

class MarkdownRenderer:
    """Renders the reconciliation report as Markdown."""

    def render(self, report: dict) -> str:
        """Generate full Markdown report."""
        lines = []
        lines.append("# GPT Capture Reconciliation Report")
        lines.append("")
        lines.append(f"**Report ID**: `{report['report_id']}`  ")
        lines.append(f"**Task ID**: `{report['task_id']}`  ")
        lines.append(f"**Generated At**: `{report['generated_at']}`  ")
        lines.append(f"**Generator**: `{report['generator']}`  ")
        lines.append(f"**Hardening Plan Reference**: `{report['hardening_plan_ref']}`")
        lines.append("")

        # Summary
        lines.append("## Summary")
        lines.append("")
        s = report["summary"]
        lines.append(f"| Metric | Count |")
        lines.append(f"|--------|-------|")
        lines.append(f"| Total Submissions | {s['total_submissions']} |")
        lines.append(f"| Total Captures | {s['total_captures']} |")
        lines.append(f"| Total Verified | {s['total_verified']} |")
        lines.append(f"| Total Valid Verdicts | {s['total_verdicts']} |")
        lines.append(f"| Orphan Submissions | {s['orphan_submissions']} |")
        lines.append(f"| Orphan Captures | {s['orphan_captures']} |")
        lines.append(f"| Unverified Captures | {s['unverified_captures']} |")
        lines.append("")

        # Verdict distribution
        lines.append("## Verdict Distribution")
        lines.append("")
        verdict_counts = {}
        for entry in report["reconciliation"]:
            v = entry.get("verdict") or "(none)"
            verdict_counts[v] = verdict_counts.get(v, 0) + 1
        lines.append("| Verdict | Count |")
        lines.append("|---------|-------|")
        for v, c in sorted(verdict_counts.items(), key=lambda x: -x[1]):
            lines.append(f"| `{v}` | {c} |")
        lines.append("")

        # Reconciliation table
        lines.append("## Reconciliation Detail")
        lines.append("")
        lines.append("| # | Task ID | Round | Verdict | Status | END Marker | Next Auth | Verify | Closure |")
        lines.append("|---|---------|-------|---------|--------|------------|-----------|--------|---------|")
        for entry in report["reconciliation"]:
            end_mark = "✓" if entry.get("has_end_marker") else "✗"
            auth_mark = "✓" if entry.get("has_next_task_auth") else "✗"
            verify_mark = "✓" if entry.get("verify_passed") else ("✗" if entry.get("verify_passed") is False else "—")
            closure_mark = "✓" if entry.get("closure_ready") else ("✗" if entry.get("closure_ready") is False else "—")
            verdict = entry.get("verdict") or "(none)"
            lines.append(
                f"| {entry['seq']} | `{entry['task_id']}` | {entry['round']} | "
                f"`{verdict}` | `{entry['status']}` | {end_mark} | {auth_mark} | "
                f"{verify_mark} | {closure_mark} |"
            )
        lines.append("")

        # Authorization chain
        lines.append("## Authorization Chain")
        lines.append("")
        if report.get("authorization_chain"):
            lines.append("```")
            for link in report["authorization_chain"]:
                exists = "✓" if link["authorized_exists"] else "✗ NOT FOUND"
                lines.append(
                    f"{link['source_task_id']} ({link['source_round']}, {link['source_verdict']})"
                )
                lines.append(f"  ──→ {link['authorized_task_id']} [{exists}]")
                lines.append("")
            lines.append("```")
        else:
            lines.append("No authorization chain data found.")
        lines.append("")

        # Anomalies
        lines.append("## Anomalies")
        lines.append("")
        anomalies = report.get("anomalies", [])
        if anomalies:
            # Group by severity
            by_severity = {}
            for a in anomalies:
                sev = a.get("severity", "info")
                by_severity.setdefault(sev, []).append(a)

            for sev in ["critical", "high", "medium", "low", "info"]:
                items = by_severity.get(sev, [])
                if not items:
                    continue
                lines.append(f"### {sev.upper()} ({len(items)})")
                lines.append("")
                for a in items:
                    lines.append(f"- **{a['task_id']}** ({a['round']}): [{a['type']}] {a['description']}")
                lines.append("")
        else:
            lines.append("No anomalies detected.")
            lines.append("")

        # Reconciliation chain diagram
        lines.append("## Process Flow")
        lines.append("")
        lines.append("```")
        lines.append("Submission → Capture → Verification → Verdict")
        lines.append("")
        lines.append(f"  [{s['total_submissions']} submissions] → [{s['total_captures']} captures] → "
                      f"[{s['total_verified']} verified] → [{s['total_verdicts']} verdicts]")
        lines.append("")
        lines.append(f"  Orphan submissions: {s['orphan_submissions']}")
        lines.append(f"  Orphan captures:    {s['orphan_captures']}")
        lines.append(f"  Unverified:         {s['unverified_captures']}")
        lines.append("```")
        lines.append("")

        # Footer
        lines.append("---")
        lines.append("")
        lines.append(f"*Report generated by `generate_reconciliation_report.py` at `{report['generated_at']}`*")
        lines.append("")
        lines.append("END_OF_RECONCILIATION_REPORT")

        return "\n".join(lines)


# ── Main ───────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Generate GPT Capture Reconciliation Report"
    )
    parser.add_argument(
        "--reports-dir",
        default="D:/agent-acceptance/_reports",
        help="Path to _reports directory",
    )
    parser.add_argument(
        "--evidence-dir",
        default="D:/agent-acceptance/evidence_packs",
        help="Path to evidence_packs directory",
    )
    parser.add_argument(
        "--output-json",
        required=True,
        help="Output path for JSON report",
    )
    parser.add_argument(
        "--output-md",
        required=True,
        help="Output path for Markdown report",
    )

    args = parser.parse_args()

    reports_dir = Path(args.reports_dir)
    evidence_dir = Path(args.evidence_dir)

    if not reports_dir.exists():
        print(f"ERROR: Reports directory not found: {reports_dir}")
        sys.exit(1)

    print(f"Scanning reports directory: {reports_dir}")
    scanner = ReconciliationScanner(reports_dir, evidence_dir)
    scanner.scan()

    print(f"Found {len(scanner.tasks)} tasks")
    total_rounds = sum(len(t["rounds"]) for t in scanner.tasks.values())
    print(f"Found {total_rounds} review rounds")

    print("Building reconciliation report...")
    builder = ReconciliationReportBuilder(scanner)
    report = builder.build()

    # Write JSON
    output_json = Path(args.output_json)
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(
        json.dumps(report, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"JSON report written to: {output_json}")

    # Write Markdown
    output_md = Path(args.output_md)
    renderer = MarkdownRenderer()
    md_content = renderer.render(report)
    output_md.write_text(md_content, encoding="utf-8")
    print(f"Markdown report written to: {output_md}")

    # Print summary
    s = report["summary"]
    print(f"\n── Summary ──")
    print(f"Total submissions:    {s['total_submissions']}")
    print(f"Total captures:       {s['total_captures']}")
    print(f"Total verified:       {s['total_verified']}")
    print(f"Total valid verdicts: {s['total_verdicts']}")
    print(f"Orphan submissions:   {s['orphan_submissions']}")
    print(f"Orphan captures:      {s['orphan_captures']}")
    print(f"Unverified captures:  {s['unverified_captures']}")
    print(f"Anomalies:            {len(report.get('anomalies', []))}")
    print(f"Auth chain links:     {len(report.get('authorization_chain', []))}")


if __name__ == "__main__":
    main()
