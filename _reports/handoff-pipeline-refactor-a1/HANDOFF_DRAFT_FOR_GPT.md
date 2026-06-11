# HANDOFF Draft for GPT Review

> task_id: HANDOFF-PIPELINE-REFACTOR-A1
> generated_at: 2026-06-08T12:46:21.220248+00:00
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
[]
```

## Human-required modules

```json
[]
```

## Next task queue

```json
[
  "Submit evidence pack to GPT review after gates pass"
]
```

## Safety boundaries

- Do not include paper full text, original paragraphs, advisor comments, private notes, raw transcript, cookies, sessions, tokens, or secrets.
- Do not delete, move, rename, or rewrite legacy handoff/history files.
- Do not generate approved handoff files before verified GPT review.

END_OF_HANDOFF
