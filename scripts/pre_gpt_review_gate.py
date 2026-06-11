#!/usr/bin/env python3
"""
pre_gpt_review_gate.py — Gate evidence pack before CDP submission.
Runs linter + targeted checks. Blocks submission on SD-01 or missing evidence.

Integration with startup_read_gate.py (per hardening plan §5.7.3):
    If --startup-proof-path is provided, the startup read gate check runs
    as an additional pre-submission gate. The pack will be BLOCKED if the
    startup read gate fails.

Usage:
    python scripts/pre_gpt_review_gate.py <pack_dir> \
        [--startup-proof-path <proof.json>] \
        [--required-reads <NEXT_AGENT_REQUIRED_READS.json>] \
        [--strict]
"""
import json, sys, argparse
from pathlib import Path
from evidence_pack_linter import lint

REPO = Path(__file__).resolve().parent.parent

# Well-known search paths for NEXT_AGENT_REQUIRED_READS.json
_REQUIRED_READS_SEARCH_PATHS = [
    REPO / "NEXT_AGENT_REQUIRED_READS.json",
    REPO / "_reports" / "next-agent-workflow-bootstrap-a1" / "NEXT_AGENT_REQUIRED_READS.json",
]


def resolve_required_reads_path(explicit: str = None) -> str | None:
    """Resolve NEXT_AGENT_REQUIRED_READS.json path.

    Search order:
    1. Explicit path if provided and exists.
    2. REPO/NEXT_AGENT_REQUIRED_READS.json
    3. _reports/next-agent-workflow-bootstrap-a1/NEXT_AGENT_REQUIRED_READS.json
    4. Glob _reports/*/NEXT_AGENT_REQUIRED_READS.json (latest modified)

    Returns resolved path string or None if not found.
    """
    if explicit:
        p = Path(explicit)
        if p.exists():
            return str(p)
        return None

    for candidate in _REQUIRED_READS_SEARCH_PATHS:
        if candidate.exists():
            return str(candidate)

    # Fallback: glob for any _reports/*/NEXT_AGENT_REQUIRED_READS.json
    matches = sorted(
        REPO.glob("_reports/*/NEXT_AGENT_REQUIRED_READS.json"),
        key=lambda f: f.stat().st_mtime,
        reverse=True,
    )
    if matches:
        return str(matches[0])

    return None


def _extract_task_id_from_manifest(manifest_path: Path) -> str:
    """Extract task_id from PACK_MANIFEST.md table.

    Looks for a table row containing 'task_id' in the Field column.
    """
    if not manifest_path.exists():
        return ""
    content = manifest_path.read_text(encoding="utf-8", errors="replace")
    for line in content.splitlines():
        if "task_id" in line.lower() and "|" in line:
            parts = [p.strip().strip("`") for p in line.split("|")]
            # Find the part after "task_id"
            for i, part in enumerate(parts):
                if part.lower() == "task_id" and i + 1 < len(parts):
                    val = parts[i + 1].strip()
                    if val and not val.startswith("-"):
                        return val
    return ""


def gate(
    pack_dir: str,
    startup_proof_path: str = None,
    required_reads_path: str = None,
    strict: bool = False,
) -> dict:
    """Run pre-GPT-review gate. Returns verdict. Blocks on errors.

    Args:
        pack_dir: Path to the evidence pack directory.
        startup_proof_path: Optional path to startup proof JSON.
            If provided, startup read gate check is run.
        required_reads_path: Optional path to NEXT_AGENT_REQUIRED_READS.json.
            Auto-detected if not provided.
        strict: If True, startup read gate runs in strict mode.
    """
    result = lint(pack_dir)

    # Additional checks
    p = Path(pack_dir)
    extra_checks = {}

    # Actual deliverables content check
    ad = p / "actual_deliverables"
    if ad.is_dir():
        files = list(ad.rglob("*"))
        extra_checks["deliverable_count"] = len(files)
        if len(files) == 0:
            result["errors"].append("SD-01: summary-only pack — no actual deliverables")

    # Manifest hash check
    manifest = p / "PACK_MANIFEST.md"
    if manifest.exists():
        content = manifest.read_text(encoding="utf-8", errors="replace")
        extra_checks["has_sha256_entries"] = "sha256" in content.lower() or "|" in content

    # Startup read gate integration (§5.7.3)
    startup_result = None
    if startup_proof_path:
        # Import startup_read_gate dynamically
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        try:
            from startup_read_gate import gate as startup_gate
        except ImportError:
            result["errors"].append(
                "startup_read_gate.py not found — cannot run startup read check"
            )
            startup_result = None
        else:
            # Resolve required reads path with auto-detection
            reads_path = resolve_required_reads_path(required_reads_path)
            if reads_path is None:
                result["errors"].append(
                    "NEXT_AGENT_REQUIRED_READS.json not found — searched repo root "
                    "and _reports/ subdirectories"
                )
            else:
                extra_checks["required_reads_resolved"] = reads_path

                # Extract task_id from pack manifest
                task_id = _extract_task_id_from_manifest(manifest)

                startup_result = startup_gate(
                    task_id=task_id,
                    proof_path=startup_proof_path,
                    required_reads_path=reads_path,
                    repo_root=str(REPO),
                    strict=strict,
                )

                # Merge startup gate results
                extra_checks["startup_read_gate"] = {
                    "gate_passed": startup_result["gate_passed"],
                    "errors_count": len(startup_result["errors"]),
                    "warnings_count": len(startup_result["warnings"]),
                }
                if "coverage_ratio" in startup_result.get("extra_checks", {}):
                    extra_checks["startup_coverage_ratio"] = startup_result["extra_checks"]["coverage_ratio"]

                if not startup_result["gate_passed"]:
                    for err in startup_result["errors"]:
                        result["errors"].append(f"startup_read_gate: {err}")

                # Forward startup warnings
                for w in startup_result.get("warnings", []):
                    result.setdefault("warnings", []).append(f"startup_read_gate: {w}")

    # Blocking decision
    blocked = len(result["errors"]) > 0
    return {
        "gate_passed": not blocked,
        "errors": result["errors"],
        "warnings": result.get("warnings", []),
        "extra_checks": extra_checks,
        "recommendation": "READY for GPT submission" if not blocked else "BLOCKED: fix errors before CDP submit",
    }

def main():
    parser = argparse.ArgumentParser(
        description="Pre-GPT Review Gate — lint evidence pack + optional startup read check"
    )
    parser.add_argument("pack_dir", help="Path to evidence pack directory")
    parser.add_argument(
        "--startup-proof-path",
        default=None,
        help="Path to startup proof JSON (enables startup read gate check)",
    )
    parser.add_argument(
        "--required-reads",
        default=None,
        help="Path to NEXT_AGENT_REQUIRED_READS.json (default: auto-detect)",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        default=False,
        help="Run startup read gate in strict mode",
    )

    args = parser.parse_args()
    r = gate(
        pack_dir=args.pack_dir,
        startup_proof_path=args.startup_proof_path,
        required_reads_path=args.required_reads,
        strict=args.strict,
    )
    print(json.dumps(r, indent=2, ensure_ascii=False))
    sys.exit(0 if r["gate_passed"] else 1)

if __name__ == "__main__":
    main()
