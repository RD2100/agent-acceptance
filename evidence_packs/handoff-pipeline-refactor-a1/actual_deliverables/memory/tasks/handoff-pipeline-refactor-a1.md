# HANDOFF-PIPELINE-REFACTOR-A1

> task_id: HANDOFF-PIPELINE-REFACTOR-A1
> status: in_progress
> source: user-authorized Phase 1 after Gate 0 inventory

## Purpose

Refactor GPT and coding-agent handoff so source-of-truth hierarchy is explicit, stale risks are surfaced, legacy handoff files are retained as audit references, and draft handoff materials are not treated as approved before verified GPT review.

## Current decisions

- Paper workflow is active in bounded, local, privacy-gated mode.
- Full paper text must not enter GPT conversation or long-term memory.
- Memory compiler is recall layer only, not source of truth.
- Canonical paper module status uses `.ai/module_ledger/` plus `_reports/PAPER_PROJECT_INDEX.json`.
- Canonical governance task state uses `.ai/tasks/`.
- Root-level `GPT_*.txt` files are legacy/reference unless verified and source-map bound.

## Gate 0 evidence

- `_reports/handoff-pipeline-refactor-a1/SHELL_HEALTH_BEFORE.txt`
- `_reports/handoff-pipeline-refactor-a1/GATE0_REUSE_CHECK.md`
- `_reports/handoff-pipeline-refactor-a1/GATE0_REUSE_CHECK.json`

## Safety boundary

No paper full text, original paragraphs, advisor comments, private notes, raw transcripts, cookies, sessions, tokens, or secrets may be written to memory, BOOT_CONTEXT, evidence packs, or handoff artifacts.
