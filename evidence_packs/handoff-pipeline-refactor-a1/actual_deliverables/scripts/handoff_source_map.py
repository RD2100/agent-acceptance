#!/usr/bin/env python3
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

SOURCE_PRIORITY = [
    {"layer": "P0", "description": "Verified GPT verdicts, evidence packs, TEST_OUTPUT, Project Index, issue ledgers, manifests"},
    {"layer": "P1", "description": "GPT-approved BOOT_CONTEXT, HANDOFF, PASTE_BLOCK"},
    {"layer": "P2", "description": "claude-memory-compiler and memory/index recall layer"},
    {"layer": "P3", "description": "legacy PROJECT_HISTORY, old HANDOFF, old PASTE_BLOCK audit references"},
]


def _sha256(path: Path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _timestamp(path: Path):
    return datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat()


def build_source_map(repo_root, claims, task_id="HANDOFF-PIPELINE-REFACTOR-A1"):
    root = Path(repo_root)
    mapped = []
    for claim in claims:
        source_path = claim["source_path"]
        fp = root / source_path
        bound = fp.exists()
        mapped.append({
            "claim_id": claim["claim_id"],
            "claim": claim["claim"],
            "source_layer": claim["source_layer"],
            "source_path": source_path,
            "sha256": _sha256(fp) if bound and fp.is_file() else None,
            "timestamp": _timestamp(fp) if bound else None,
            "bound": bound,
        })
    return {
        "task_id": task_id,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_priority": SOURCE_PRIORITY,
        "claims": mapped,
    }


def default_claims():
    return [
        {"claim_id": "source_truth_hierarchy", "claim": "P0/P1/P2/P3 source-of-truth hierarchy is defined.", "source_layer": "P1", "source_path": "HANDOFF_SOURCE_OF_TRUTH.md"},
        {"claim_id": "legacy_inventory", "claim": "Legacy handoff files are inventoried, not modified.", "source_layer": "P1", "source_path": "LEGACY_HANDOFF_INVENTORY.md"},
        {"claim_id": "paper_project_index", "claim": "Paper module status is sourced from PAPER_PROJECT_INDEX.", "source_layer": "P0", "source_path": "_reports/PAPER_PROJECT_INDEX.json"},
        {"claim_id": "gate0_reuse", "claim": "Gate 0 reuse-before-build inventory was completed.", "source_layer": "P0", "source_path": "_reports/handoff-pipeline-refactor-a1/GATE0_REUSE_CHECK.md"},
    ]


def main():
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent
    result = build_source_map(root, default_claims())
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if all(c["bound"] for c in result["claims"]) else 1


if __name__ == "__main__":
    sys.exit(main())
