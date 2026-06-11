#!/usr/bin/env python3
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from validate_context_memory import check_privacy
from validate_handoff import validate_handoff

FORBIDDEN_VIEW_KEYS = {"raw_paper_text", "full_section_text", "paragraph_text", "advisor_comments", "private_notes"}


def _safe_project_view(project_view):
    forbidden = sorted(k for k in project_view.keys() if k in FORBIDDEN_VIEW_KEYS)
    return forbidden


def _json_block(value):
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True)


def compile_handoff_draft(repo_root, output_dir, project_view=None, task_id="HANDOFF-PIPELINE-REFACTOR-A1"):
    root = Path(repo_root)
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    project_view = project_view or {}
    forbidden = _safe_project_view(project_view)
    if forbidden:
        return {
            "task_id": task_id,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "approval_status": "draft_only",
            "draft_path": str(out / "HANDOFF_DRAFT_FOR_GPT.md"),
            "paste_block_path": str(out / "PASTE_BLOCK_DRAFT_FOR_NEW_GPT.txt"),
            "source_map_path": str(out / "HANDOFF_EVIDENCE_MAP.json"),
            "privacy_checked": True,
            "safety_pass": False,
            "errors": [f"forbidden project_view keys: {forbidden}"],
            "hash": None,
        }

    now = datetime.now(timezone.utc).isoformat()
    closed = project_view.get("closed_modules", [])
    human_required = project_view.get("human_required_modules", [])
    next_tasks = project_view.get("next_tasks", ["Submit handoff evidence pack to GPT review"])

    draft = f"""# HANDOFF Draft for GPT Review

> task_id: {task_id}
> generated_at: {now}
> approval_status: draft_only

This file is a coding-agent draft. It is not approved handoff material until GPT review is captured and verified.

## Project scope

DevFrame agent-acceptance handoff pipeline. This draft focuses on source-of-truth hierarchy, stale checks, safety scanning, legacy handoff inventory, and Minimax M3 observation logging.

## Current toolchain

- GPT review transaction runner: `scripts/gpt_review_transaction.py`
- GPT reply verifier: `scripts/verify_gpt_reply.py`
- GPT reply capture helper: `scripts/capture_gpt_reply.py`
- Review queue: `scripts/review_queue.py`
- Evidence pack linter/gate: `scripts/evidence_pack_linter.py`, `scripts/pre_gpt_review_gate.py`
- Boot context/handoff helpers: `scripts/build_boot_context.py`, `scripts/validate_handoff.py`
- Memory compiler/privacy guard: `scripts/memory_compiler.py`, `scripts/sync_compiled_memory.py`, `scripts/validate_context_memory.py`

## Source-of-truth hierarchy

- P0: captured GPT verdicts, evidence packs, TEST_OUTPUT, Project Index, issue ledgers, manifests
- P1: GPT-approved BOOT_CONTEXT / HANDOFF / PASTE_BLOCK
- P2: claude-memory-compiler knowledge and memory/index recall layer
- P3: legacy PROJECT_HISTORY, old HANDOFF, old PASTE_BLOCK audit references

Memory compiler is a recall layer, not source of truth.

## Paper workflow status

Paper workflow is active in bounded, local, privacy-gated mode. Full paper text must not enter GPT conversation or long-term memory.

## Module state policy

Paper module status is sourced from `.ai/module_ledger/` plus `_reports/PAPER_PROJECT_INDEX.json`.
Governance/task status is sourced from `.ai/tasks/`.

## Closed modules and limitations

```json
{_json_block(closed)}
```

## Human-required modules

```json
{_json_block(human_required)}
```

## Next task queue

```json
{_json_block(next_tasks)}
```

## Safety boundaries

- Do not include paper full text, original paragraphs, advisor comments, private notes, raw transcript, cookies, sessions, tokens, or secrets.
- Do not delete, move, rename, or rewrite legacy handoff/history files.
- Do not generate approved handoff files before verified GPT review.

END_OF_HANDOFF
"""

    privacy = check_privacy(draft, "HANDOFF_DRAFT_FOR_GPT.md")
    if not privacy["pass"]:
        return {
            "task_id": task_id,
            "generated_at": now,
            "approval_status": "draft_only",
            "draft_path": str(out / "HANDOFF_DRAFT_FOR_GPT.md"),
            "paste_block_path": str(out / "PASTE_BLOCK_DRAFT_FOR_NEW_GPT.txt"),
            "source_map_path": str(out / "HANDOFF_EVIDENCE_MAP.json"),
            "privacy_checked": True,
            "safety_pass": False,
            "errors": privacy["issues"],
            "hash": None,
        }

    draft_path = out / "HANDOFF_DRAFT_FOR_GPT.md"
    paste_path = out / "PASTE_BLOCK_DRAFT_FOR_NEW_GPT.txt"
    draft_path.write_text(draft, encoding="utf-8")
    paste_path.write_text(
        "GPT handoff draft follows. Treat as draft_only until verified GPT review.\n\n" + draft,
        encoding="utf-8",
    )
    validation = validate_handoff(str(draft_path))
    digest = hashlib.sha256(draft.encode("utf-8")).hexdigest()
    return {
        "task_id": task_id,
        "generated_at": now,
        "approval_status": "draft_only",
        "draft_path": str(draft_path),
        "paste_block_path": str(paste_path),
        "source_map_path": str(out / "HANDOFF_EVIDENCE_MAP.json"),
        "privacy_checked": True,
        "safety_pass": True,
        "handoff_validation": validation,
        "hash": digest,
    }


def default_project_view(root: Path):
    closed_modules = []
    human_required_modules = []
    index_path = root / "_reports/PAPER_PROJECT_INDEX.json"
    if index_path.exists():
        try:
            index = json.loads(index_path.read_text(encoding="utf-8"))
            for module in index.get("modules", []):
                status = module.get("review_status") or module.get("status")
                entry = {"id": module.get("id"), "status": status, "rounds": module.get("rounds")}
                if status in {"accepted", "accepted_with_limitation", "closed"}:
                    closed_modules.append(entry)
                if status == "human_required":
                    human_required_modules.append(entry)
        except json.JSONDecodeError:
            pass
    return {
        "paper_status": "active_bounded_privacy_gated",
        "current_task": "HANDOFF-PIPELINE-REFACTOR-A1",
        "closed_modules": closed_modules,
        "human_required_modules": human_required_modules,
        "next_tasks": ["Submit evidence pack to GPT review after gates pass"],
    }


def main():
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT
    out = root / "_reports/handoff-pipeline-refactor-a1"
    result = compile_handoff_draft(root, out, default_project_view(root))
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("safety_pass") else 1


if __name__ == "__main__":
    sys.exit(main())
